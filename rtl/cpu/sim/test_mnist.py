import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
import numpy as np
import os

requant_mul = 955
requant_shift = 24
image_count = 20

img_base = 0        # input images - 0..195
layer1_base = 196   # layer1 output - 196..227

layer1_stores = 32  # 128/4
layer2_stores = 3   # 12/4
total_stores = layer1_stores + layer2_stores


def quantize_image(img_f32):
    "Pixels 0.0-1.0 to INT8 0-127 flat 784 values."
    return np.clip(np.round(img_f32.flatten() * 127), 0, 127).astype(np.int32)


def requantize(accumulators):
    "ReLU, fixed-point rescale and saturate; same as requant.sv."
    relu = np.where(accumulators < 0, 0, accumulators)
    scaled = (relu.astype(np.int64) * requant_mul) >> requant_shift
    return np.clip(scaled, 0, 127).astype(np.int32)


def reference_model(img_f32, w1, w2):
    "output computed in Python."
    image = quantize_image(img_f32)
    layer1_acc = image @ w1              # (128,) INT32 before ReLU
    layer1_out = requantize(layer1_acc)  # (128,) INT8 after ACT
    layer2_output = layer1_out @ w2      # (10,) INT32
    return layer1_acc, layer1_out, layer2_output


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


def write_img_to_mem(dut, img_f32):
    "write images directly to act_mem, inside cpu, inside ai_core_top"
    image = quantize_image(img_f32)
    for tile in range(196):
        pixels = image[tile * 4: tile * 4 + 4]
        dut.u_cpu.u_act_mem.mem[img_base + tile].value = pack_bytes(pixels)


def read_layer1_output(dut):
    "read back 128 INT8 values that ACT wrote into act_mem."
    values = []
    for tile in range(32):
        word = int(dut.u_cpu.u_act_mem.mem[layer1_base + tile].value)
        values.extend(unpack_bytes(word))
    return np.array(values)


async def reset_cpu(dut):
    "reset for 3 cycles, clears PC and registers"
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)


async def run_program(dut):
    "run till all 35 M_ST instructions are done"
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


def check(name, got, expected, image_index):
    "compare 2 arrays and report the differences"
    wrong = np.where(got != expected)[0]
    if len(wrong):
        i = wrong[0]
        raise AssertionError(
            f"image {image_index} - {name}: {len(wrong)}/{len(expected)} wrong. "
            f"At index {i}: expected {expected[i]}, got {got[i]}"
        )


@cocotb.test()
async def test_mnist(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    golden = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '..', '..', '..', 'golden_model')
    w1 = np.load(os.path.join(golden, 'w1.npy')).astype(np.int32)
    w2 = np.load(os.path.join(golden, 'w2.npy')).astype(np.int32)
    images = np.load(os.path.join(golden, 'test_images.npy'))
    labels = np.load(os.path.join(golden, 'test_labels.npy'))

    n = min(image_count, len(images))
    correct_predictions = 0
    for idx in range(n):
        expected_acc, expected_act, expected_output = reference_model(
            images[idx], w1, w2)
        ref_pred = int(np.argmax(expected_output))

        write_img_to_mem(dut, images[idx])
        await reset_cpu(dut)
        stores, cycles = await run_program(dut)

        # argmax's registered output for the final store lags by one cycle
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)

        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        # INT32 accumulators from layer 1
        got_acc = np.array(stores[:layer1_stores]).flatten()
        check("layer-1 accumulators", got_acc, expected_acc, idx)

        # ACT output in act_mem
        got_act = read_layer1_output(dut)
        check("ACT requant", got_act, expected_act, idx)

        # layer-2, remove the 2 zero-padding columns.
        got_output = np.array(stores[layer1_stores:]).flatten()[:10]
        check("layer-2 output", got_output, expected_output, idx)

        # prediction, read straight from the argmax hardware
        hw_digit = int(dut.u_argmax.digit.value)
        assert hw_digit == ref_pred, (
            f"image {idx}: argmax hardware said {hw_digit}, "
            f"reference argmax says {ref_pred}"
        )

        label = int(labels[idx])
        if hw_digit == label:
            correct_predictions += 1

        print(f"image {idx}: predicted {hw_digit}, "
              f"label {label} ({cycles} cycles)", flush=True)

    print(f"argmax bit-exact vs reference: {n}/{n}", flush=True)
    print(f"accuracy vs labels: {correct_predictions}/{n} "
          f"({100 * correct_predictions / n:.0f}%)", flush=True)