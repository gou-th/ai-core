import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge


@cocotb.test()
async def test_program(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    for _ in range(30):
        await RisingEdge(dut.clk)

    assert dut.u_regfile.regs[1].value == 0,  f"R1 = {dut.u_regfile.regs[1].value}"
    assert dut.u_regfile.regs[2].value == 15, f"R2 = {dut.u_regfile.regs[2].value}"
    assert dut.u_regfile.regs[3].value == 1,  f"R3 = {dut.u_regfile.regs[3].value}"