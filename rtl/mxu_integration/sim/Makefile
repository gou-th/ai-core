SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILATOR_TRACE = 1
VERILOG_SOURCES = $(PWD)/../../pe/pe.sv $(PWD)/../../systolic_array/systolic_array.sv \
                   $(PWD)/../../skew_buffer/skew_buffer.sv \
                   $(PWD)/../../deskew_buffer/deskew_buffer.sv \
				   $(PWD)/../mxu_integration.sv

TOPLEVEL = mxu_integration
MODULE = mxu_integration_test
include $(shell cocotb-config --makefiles)/Makefile.sim