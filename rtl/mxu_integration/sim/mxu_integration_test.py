import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
import numpy as np

@cocotb.test()
async def test_mxu_integration(dut):

    # Clock of 10ns period (100MHz)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset the DUT
    dut.rst_n.value = 0
    for i in range(4):
        dut.act_in[i].value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # weight matrix
    W = np.array([
        [1, 2, 0, -1],
        [0, 1, 1,  2],
        [2, 0, 1,  1],
        [1, 1, 0,  1],], dtype=np.int8)

    weight_bus = 0
    flat = W.flatten()
    for i in range(16):
        weight_bus |= (int(flat[i]) & 0xFF) << (8 * i)

    dut.weight_bus.value = weight_bus
    dut.load_w.value = 1
    await RisingEdge(dut.clk)
    dut.load_w.value = 0

    a = np.array([3, -1, -2, 4], dtype=np.int8)

    # no manual stagger
    for j in range(4):
        dut.act_in[j].value = int(a[j])
    await RisingEdge(dut.clk)

    for z in range(7):
        await RisingEdge(dut.clk)

    expected = a.astype(np.int32) @ W.astype(np.int32)

    for j in range(4):
        got = dut.psum_out[j].value.to_signed()
        assert got == expected[j], f"col{j}: expected {expected[j]}, got {got}"
    print(f"PASS: psum_out matches golden model {expected.tolist()}", flush=True)