import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
import numpy as np
import json
import os

obs_count = 20

img_base = 0        # observation input - 0..2 (9 padded values, 3 tiles)
layer1_base = 3      # layer1 output - 3..34
layer2_base = 36     # layer2 output - 36..67

layer1_stores = 32  # 128/4
layer2_stores = 32  # 128/4
layer3_stores = 1   # 4/4
total_stores = layer1_stores + layer2_stores + layer3_stores

BIAS_WORD1 = 2   # bias slot feeding layer1's input
BIAS_WORD2 = 35  # bias slot feeding layer2's input
BIAS_WORD3 = 68  # bias slot feeding layer3's input
CONST_INPUT = 127


def quantize_obs(obs_f32, scale_obs):
    "8 raw observation floats to INT8, single shared scale."
    return np.clip(np.round(obs_f32 / scale_obs), -128, 127).astype(np.int32)


def requantize(accumulators, M, S):
    "ReLU, fixed-point rescale and saturate; same as requant.sv."
    relu = np.where(accumulators < 0, 0, accumulators)
    scaled = (relu.astype(np.int64) * M) >> S
    return np.clip(scaled, 0, 127).astype(np.int32)


def reference_model(obs_f32, w1, w2, w3, scale_obs, M, S):
    "output computed in Python, bias folded into weights as extra row."
    obs_int8 = quantize_obs(obs_f32, scale_obs)
    obs_aug = np.append(obs_int8, CONST_INPUT)          # (9,)

    layer1_acc = obs_aug @ w1                            # (128,) INT32 before ReLU
    layer1_out = requantize(layer1_acc, M, S)             # (128,) INT8 after ACT
    layer1_aug = np.append(layer1_out, CONST_INPUT)       # (129,)

    layer2_acc = layer1_aug @ w2                          # (128,) INT32 before ReLU
    layer2_out = requantize(layer2_acc, M, S)              # (128,) INT8 after ACT
    layer2_aug = np.append(layer2_out, CONST_INPUT)        # (129,)

    layer3_output = layer2_aug @ w3                        # (4,) INT32 action logits
    return layer1_acc, layer1_out, layer2_acc, layer2_out, layer3_output


def pack_bytes(four_values):
    "pack 4 signed bytes into one 32-bit word with value 0 in the low byte"
    word = 0
    for i, v in enumerate(four_values):
        word |= (int(v) & 0xFF) << (i * 8)
    return word


def unpack_bytes(word):
    "split 32-bit word into 4 signed bytes with low byte first"
    values = []
    for i in range(4):
        byte = (word >> (i * 8)) & 0xFF
        values.append(byte - 256 if byte > 127 else byte)
    return values


def write_obs_to_mem(dut, obs_f32, scale_obs):
    "write observation + bias slots directly to act_mem, bypassing UART and the bias-FSM"
    obs_int8 = quantize_obs(obs_f32, scale_obs)
    tile0 = obs_int8[0:4]
    tile1 = obs_int8[4:8]
    tile2 = [CONST_INPUT, 0, 0, 0]   # obs[8] slot is the bias constant

    dut.u_cpu.u_act_mem.mem[img_base + 0].value = pack_bytes(tile0)
    dut.u_cpu.u_act_mem.mem[img_base + 1].value = pack_bytes(tile1)
    dut.u_cpu.u_act_mem.mem[img_base + 2].value = pack_bytes(tile2)

    # layer2/layer3 bias slots hardware writes these via the bias-injection FSM before UART loading even starts
    dut.u_cpu.u_act_mem.mem[BIAS_WORD2].value = pack_bytes([CONST_INPUT, 0, 0, 0])
    dut.u_cpu.u_act_mem.mem[BIAS_WORD3].value = pack_bytes([CONST_INPUT, 0, 0, 0])


def read_layer_output(dut, base, tiles):
    "read back INT8 values that ACT wrote into act_mem."
    values = []
    for tile in range(tiles):
        word = int(dut.u_cpu.u_act_mem.mem[base + tile].value)
        values.extend(unpack_bytes(word))
    return np.array(values)


async def reset_cpu(dut):
    "reset for 3 cycles, clears PC and registers"
    dut.rst_n_btn.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n_btn.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n_btn.value = 0
    await FallingEdge(dut.clk)


async def run_program(dut):
    "run till all 65 M_ST instructions are done"
    stores = []

    for cycle in range(3_000_000):
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        if int(dut.u_cpu.store_en.value):
            four = [dut.u_cpu.result_data[j].value.signed_integer for j in range(4)]
            stores.append(four)
            if len(stores) == total_stores:
                return stores, cycle

    raise AssertionError(f"timed out with {len(stores)}/{total_stores} stores")


def check(name, got, expected, obs_index):
    "compare 2 arrays and report the differences"
    wrong = np.where(got != expected)[0]
    if len(wrong):
        i = wrong[0]
        raise AssertionError(
            f"obs {obs_index} - {name}: {len(wrong)}/{len(expected)} wrong. "
            f"At index {i}: expected {expected[i]}, got {got[i]}"
        )


@cocotb.test()
async def test_lunarlander(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    golden = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '..', 'golden_model')
    w1 = np.load(os.path.join(golden, 'w1.npy')).astype(np.int32)
    w2 = np.load(os.path.join(golden, 'w2.npy')).astype(np.int32)
    w3 = np.load(os.path.join(golden, 'w3.npy')).astype(np.int32)
    observations = np.load(os.path.join(golden, 'test_observations.npy'))
    actions = np.load(os.path.join(golden, 'test_actions.npy'))
    with open(os.path.join(golden, 'scales.json')) as f:
        scales = json.load(f)
    scale_obs = scales['scale_obs']
    M = scales['M']
    S = scales['S']

    n = min(obs_count, len(observations))
    correct_predictions = 0
    for idx in range(n):
        (expected_l1_acc, expected_l1_out,
         expected_l2_acc, expected_l2_out,
         expected_output) = reference_model(observations[idx], w1, w2, w3,
                                             scale_obs, M, S)
        ref_pred = int(np.argmax(expected_output))

        write_obs_to_mem(dut, observations[idx], scale_obs)
        await reset_cpu(dut)
        dut.running.value = 1 

        stores, cycles = await run_program(dut)

        for _ in range(10):
            await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)

        got_l1_acc = np.array(stores[:layer1_stores]).flatten()
        check("layer-1 accumulators", got_l1_acc, expected_l1_acc, idx)

        got_l1_out = read_layer_output(dut, layer1_base, layer1_stores)
        check("layer-1 ACT requant", got_l1_out, expected_l1_out, idx)

        got_l2_acc = np.array(stores[layer1_stores:layer1_stores + layer2_stores]).flatten()
        check("layer-2 accumulators", got_l2_acc, expected_l2_acc, idx)

        got_l2_out = read_layer_output(dut, layer2_base, layer2_stores)
        check("layer-2 ACT requant", got_l2_out, expected_l2_out, idx)

        got_output = np.array(stores[layer1_stores + layer2_stores:]).flatten()[:4]
        check("layer-3 output", got_output, expected_output, idx)

        hw_action = int(dut.display_action.value)
        assert hw_action == ref_pred, (
            f"obs {idx}: argmax hardware said {hw_action}, "
            f"reference argmax says {ref_pred}"
        )

        label = int(actions[idx])
        if hw_action == label:
            correct_predictions += 1

        print(f"obs {idx}: predicted {hw_action}, "
              f"float policy {label} ({cycles} cycles)", flush=True)

    print(f"argmax bit-exact vs reference: {n}/{n}", flush=True)
    print(f"agreement vs float policy: {correct_predictions}/{n} "
          f"({100 * correct_predictions / n:.0f}%)", flush=True)