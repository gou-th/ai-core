SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILATOR_TRACE = 1
VERILOG_SOURCES = $(PWD)/../../pe/src/pe.sv \
                   $(PWD)/../../systolic_array/src/systolic_array.sv \
                   $(PWD)/../../skew_buffer/src/skew_buffer.sv \
                   $(PWD)/../../deskew_buffer/src/deskew_buffer.sv \
                   $(PWD)/../../mxu_integration/src/mxu_integration.sv \
                   $(PWD)/../../accum_bank/src/accum_bank.sv \
                   $(PWD)/../../mxu_controller/src/mxu_controller.sv \
                   $(PWD)/../../requant/src/requant.sv \
                   $(PWD)/../src/weight_mem.sv \
                   $(PWD)/../src/act_mem.sv \
                   $(PWD)/../src/result_mem.sv \
                   $(PWD)/../src/fetch.sv \
                   $(PWD)/../src/decode.sv \
                   $(PWD)/../src/execute.sv \
                   $(PWD)/../src/regfile.sv \
                   $(PWD)/../src/cpu.sv
TOPLEVEL = cpu
MODULE = test_mnist
VERILATOR_TRACE = 1
include $(shell cocotb-config --makefiles)/Makefile.sim