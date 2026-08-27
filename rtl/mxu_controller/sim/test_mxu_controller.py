import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

@cocotb.test()
async def test_mxu_controller(dut):

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # reset
    dut.rst_n.value = 0
    dut.matrix_start.value = 0
    dut.matrix_cmd.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)

    assert dut.matrix_busy.value == 0, "should be idle after reset"

    #M_LD_W
    dut.matrix_cmd.value = 0b00
    dut.matrix_start.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.matrix_start.value = 0

    assert dut.load_w.value == 1, f"LOAD_W: load_w should be 1, got {dut.load_w.value}"
    assert dut.load_a.value == 0
    assert dut.acc_en.value == 0
    assert dut.matrix_busy.value == 1

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert dut.matrix_done.value == 1, "should be in DONE"
    assert dut.load_w.value == 0

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert dut.matrix_busy.value == 0, "should be back in IDLE"
    dut._log.info("M_LD_W ok")

    #M_LD_A
    dut.matrix_cmd.value = 0b01
    dut.matrix_start.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.matrix_start.value = 0

    assert dut.load_a.value == 1, f"LOAD_A: load_a should be 1, got {dut.load_a.value}"
    assert dut.load_w.value == 0

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert dut.matrix_done.value == 1

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert dut.matrix_busy.value == 0
    dut._log.info("M_LD_A ok")

    # M_MUL
    dut.matrix_cmd.value = 0b10
    dut.matrix_start.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.matrix_start.value = 0

    # RUN lasts 9 cycles
    acc_en_count = 0
    for i in range(9):
        acc_en_count += int(dut.acc_en.value)
        assert dut.matrix_busy.value == 1, f"cycle {i}: should be busy"
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)

    assert acc_en_count == 1, f"acc_en should rise once, got - {acc_en_count}x"
    assert dut.matrix_done.value == 1, "should be in DONE after RUN"

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert dut.matrix_busy.value == 0
    dut._log.info("M_MUL ok")

    # M_ST
    dut.matrix_cmd.value = 0b11
    dut.matrix_start.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.matrix_start.value = 0

    assert dut.store_en.value == 1, f"STORE: store_en should be 1, got {dut.store_en.value}"
    assert dut.acc_clear.value == 1, "acc_clear and store_en both high"

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert dut.matrix_done.value == 1

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert dut.matrix_busy.value == 0
    dut._log.info("M_ST ok")