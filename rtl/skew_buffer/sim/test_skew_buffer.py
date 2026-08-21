import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
import numpy as np

@cocotb.test()
async def test_skew_buffer(dut):

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


    vals = [10,20,30,40]
    for i in range(4):
        dut.act_in[i].value= vals[i]
    await RisingEdge(dut.clk)

    assert dut.act_out[0].value.signed_integer == vals[0], \
        f"row0: expected {vals[0]}, got {dut.act_out[0].value.signed_integer}"

    # row 1: needs 1 cycle
    await RisingEdge(dut.clk)
    assert dut.act_out[1].value.signed_integer == vals[1], \
        f"row1: expected {vals[1]}, got {dut.act_out[1].value.signed_integer}"

    # row 2: needs 2 cycles total
    await RisingEdge(dut.clk)
    assert dut.act_out[2].value.signed_integer == vals[2], \
        f"row2: expected {vals[2]}, got {dut.act_out[2].value.signed_integer}"

    # row 3: needs 3 cycles total
    await RisingEdge(dut.clk)
    assert dut.act_out[3].value.signed_integer == vals[3], \
        f"row3: expected {vals[3]}, got {dut.act_out[3].value.signed_integer}"

    dut._log.info("PASS: skew_buffer staggers correctly")

    
    