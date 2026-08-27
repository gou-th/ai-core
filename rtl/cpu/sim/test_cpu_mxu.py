import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
import numpy as np

@cocotb.test()
async def test_cpu(dut):

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)

    # weight tile and activation vector
    W = np.array([
        [1, 2, 0, -1],
        [0, 1, 1,  2],
        [2, 0, 1,  1],
        [1, 1, 0,  1]], dtype=np.int8)
    a = np.array([3, -1, -2, 4], dtype=np.int8)

    weight_bus = 0
    flat = W.flatten()
    for i in range(16):
        weight_bus |= (int(flat[i]) & 0xFF) << (8 * i)
    dut.weight_data.value = weight_bus

    for i in range(4):
        dut.act_data[i].value = int(a[i])

    expected = (a.astype(np.int32) @ W.astype(np.int32))

    # run until store_en high
    for cycle in range(60):
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        if int(dut.store_en.value):
            got = [dut.result_data[j].value.signed_integer for j in range(4)]
            for j in range(4):
                assert got[j] == expected[j], f"col{j}: expected {expected[j]}, got {got[j]}"
            dut._log.info(f"PASS at cycle {cycle}: result_data = {got}")
            break
    else:
        assert False, "store_en never went high within 60 cycles"