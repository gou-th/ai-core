import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
import numpy as np

@cocotb.test()
async def test_deskew_buffer(dut):

    # Clock of 10ns period (100MHz)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start()) 

    # Reset the DUT
    dut.rst_n.value = 0
    for i in range(4):
        dut.psum_in[i].value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


    psums = [10,20,30,40]
    dut.psum_in[0].value= psums[0]
    await RisingEdge(dut.clk)
    
    dut.psum_in[1].value= psums[1]
    await RisingEdge(dut.clk)

    dut.psum_in[2].value= psums[2]
    await RisingEdge(dut.clk)

    dut.psum_in[3].value= psums[3]
    await RisingEdge(dut.clk)

    for j in range(4):
        got = dut.psum_out[j].value.signed_integer
        assert got == psums[j], f"col{j}: expected {psums[j]}, got {got}"

    dut._log.info("PASS: deskew_buffer staggers correctly")

    
    