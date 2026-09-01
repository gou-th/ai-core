import cocotb
from cocotb.triggers import Timer
M = 955
S = 24
def golden_requant(acc):
    if acc < 0:
        return 0
    val = (acc * M) >> S
    return min(val, 127)
@cocotb.test()
async def test_requant(dut):
    test_vals = [0, 1000, -500, 2**20, -2**20, 127*2**24, 300000]
    for i, val in enumerate(test_vals):
        dut.acc_in[i % 4].value = val
        await Timer(1, units="ns")
        expected = golden_requant(val)
        actual = int(dut.act_out[i % 4].value.signed_integer)
        assert actual == expected, f"acc={val}: expected={expected}, got={actual}"