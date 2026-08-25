import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

@cocotb.test()
async def test_accum_bank(dut):

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    # reset
    dut.rst_n.value = 0
    dut.acc_en.value = 0
    dut.acc_clear.value = 0
    for i in range(4):
        dut.psum_in[i].value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    for j in range(4):
        assert dut.acc_out[j].value.signed_integer == 0
    # three tiles, hand-computed running sum
    tiles = [
        [3, -1, -2, 4],
        [5,  2, -1, 0],
        [-2, 4,  3, 1],
    ]
    expected = [0, 0, 0, 0]
    for tile in tiles:
        for i in range(4):
            dut.psum_in[i].value = tile[i]
        dut.acc_en.value = 1
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        dut.acc_en.value = 0

        for i in range(4):
            expected[i] += tile[i]

        for i in range(4):
            got = dut.acc_out[i].value.signed_integer
            assert got == expected[i], f"tile mismatch col{i}: expected {expected[i]}, got {got}"

    dut._log.info(f"PASS: accumulated correctly, final = {expected}")

    # clear
    dut.acc_clear.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.acc_clear.value = 0

    for i in range(4):
        got = dut.acc_out[i].value.signed_integer
        assert got == 0, f"clear failed col{i}: got {got}"

    dut._log.info("PASS: acc_clear resets to 0")