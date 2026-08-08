import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

@cocotb.test()
async def test_dut(dut):

    # Clock of 10ns period (100MHz)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start()) 

    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    async def load_weight(weight):
        dut.weight.value = weight
        dut.load_w.value = 1
        await RisingEdge(dut.clk)
        dut.load_w.value = 0

    async def do_mac(weight, act, psum_in):
        dut.act_in.value = act
        dut.psum_in.value = psum_in
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        expected = psum_in + weight * act
        psum_out = dut.psum_out.value.to_signed()
        assert psum_out == expected, f"Expected {expected}, got {psum_out}"
    
    W= 3
    await load_weight(W)
    await do_mac(W,2,8)    # 8 + 3*2 = 14
    await do_mac(W,5,6)    # 6 + 3*5 = 21  
    await do_mac(W,-4,5)   # 5 + 3*(-4) = -7
    W = -2
    await load_weight(W)
    await do_mac(W,3,7)    # 7 + (-2)*3 = 1
    await do_mac(W,-5,10)  # 10 + (-2)*(-5) = 20