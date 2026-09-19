SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILATOR_TRACE = 1

VERILOG_SOURCES = $(PWD)/../../../rtl/pe/pe.sv \
                   $(PWD)/../../../rtl/systolic_array/systolic_array.sv \
                   $(PWD)/../../../rtl/skew_buffer/skew_buffer.sv \
                   $(PWD)/../../../rtl/deskew_buffer/deskew_buffer.sv \
                   $(PWD)/../../../rtl/mxu_integration/mxu_integration.sv \
                   $(PWD)/../../../rtl/accum_bank/accum_bank.sv \
                   $(PWD)/../../../rtl/mxu_controller/mxu_controller.sv \
                   $(PWD)/../../../rtl/requant/requant.sv \
                   $(PWD)/../top/weight_mem.sv \
                   $(PWD)/../top/act_mem.sv \
                   $(PWD)/../top/result_mem.sv \
                   $(PWD)/../../../rtl/cpu/fetch.sv \
                   $(PWD)/../../../rtl/cpu/decode.sv \
                   $(PWD)/../../../rtl/cpu/execute.sv \
                   $(PWD)/../../../rtl/cpu/regfile.sv \
                   $(PWD)/../../../rtl/cpu/cpu.sv \
                   $(PWD)/../argmax/argmax.sv \
                   $(PWD)/../seven_seg/seven_seg.sv \
                   $(PWD)/../top/ai_core_top.sv \
                   $(PWD)/../../../rtl/uart/uart_rx.sv \
                   $(PWD)/../../../rtl/uart/uart_tx.sv

TOPLEVEL = ai_core_top
MODULE = test_lunarlander

include $(shell cocotb-config --makefiles)/Makefile.sim