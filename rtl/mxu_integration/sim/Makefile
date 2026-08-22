SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILATOR_TRACE = 1
VERILOG_SOURCES = $(PWD)/../../pe/src/pe.sv $(PWD)/../../systolic_array/src/systolic_array.sv \
                   $(PWD)/../../skew_buffer/src/skew_buffer.sv \
                   $(PWD)/../../deskew_buffer/src/deskew_buffer.sv \
				   $(PWD)/../src/mxu_integration.sv

TOPLEVEL = mxu_integration
MODULE = mxu_integration_test
include $(shell cocotb-config --makefiles)/Makefile.sim