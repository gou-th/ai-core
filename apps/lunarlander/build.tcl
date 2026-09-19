#*****************************************************************************************
# Vivado Tcl script - recreate the ai-core LunarLander demo project
#
# Usage (from apps/lunarlander/):
#   vivado -mode batch -source build.tcl
# or, inside Vivado's Tcl console:
#   source build.tcl
#*****************************************************************************************

set origin_dir "."
if { [info exists ::origin_dir_loc] } {
  set origin_dir $::origin_dir_loc
}

set _xil_proj_name_ "ai_core_lunarlander"
if { [info exists ::user_project_name] } {
  set _xil_proj_name_ $::user_project_name
}

# Create project
create_project ${_xil_proj_name_} ./${_xil_proj_name_} -part xc7a35tcpg236-1

set proj_dir [get_property directory [current_project]]

set obj [current_project]
set_property -name "default_lib" -value "xil_defaultlib" -objects $obj
set_property -name "part" -value "xc7a35tcpg236-1" -objects $obj
set_property -name "simulator_language" -value "Mixed" -objects $obj

# ── sources_1 fileset ──
if {[string equal [get_filesets -quiet sources_1] ""]} {
  create_fileset -srcset sources_1
}
set obj [get_filesets sources_1]

set files [list \
 [file normalize "${origin_dir}/../../rtl/pe/pe.sv"] \
 [file normalize "${origin_dir}/../../rtl/systolic_array/systolic_array.sv"] \
 [file normalize "${origin_dir}/../../rtl/skew_buffer/skew_buffer.sv"] \
 [file normalize "${origin_dir}/../../rtl/deskew_buffer/deskew_buffer.sv"] \
 [file normalize "${origin_dir}/../../rtl/mxu_integration/mxu_integration.sv"] \
 [file normalize "${origin_dir}/../../rtl/accum_bank/accum_bank.sv"] \
 [file normalize "${origin_dir}/../../rtl/mxu_controller/mxu_controller.sv"] \
 [file normalize "${origin_dir}/../../rtl/requant/requant.sv"] \
 [file normalize "${origin_dir}/../../rtl/cpu/fetch.sv"] \
 [file normalize "${origin_dir}/../../rtl/cpu/decode.sv"] \
 [file normalize "${origin_dir}/../../rtl/cpu/execute.sv"] \
 [file normalize "${origin_dir}/../../rtl/cpu/regfile.sv"] \
 [file normalize "${origin_dir}/../../rtl/cpu/cpu.sv"] \
 [file normalize "${origin_dir}/../../rtl/uart/uart_rx.sv"] \
 [file normalize "${origin_dir}/../../rtl/uart/uart_tx.sv"] \
 [file normalize "${origin_dir}/argmax/argmax.sv"] \
 [file normalize "${origin_dir}/seven_seg/seven_seg.sv"] \
 [file normalize "${origin_dir}/top/weight_mem.sv"] \
 [file normalize "${origin_dir}/top/act_mem.sv"] \
 [file normalize "${origin_dir}/top/result_mem.sv"] \
 [file normalize "${origin_dir}/top/ai_core_top.sv"] \
 [file normalize "${origin_dir}/top/weights.mem"] \
 [file normalize "${origin_dir}/top/program.mem"] \
]
add_files -norecurse -fileset $obj $files

set file [file normalize "${origin_dir}/top/weights.mem"]
set_property -name "file_type" -value "Memory File" -objects [get_files -of_objects [get_filesets sources_1] [list "*$file"]]

set file [file normalize "${origin_dir}/top/program.mem"]
set_property -name "file_type" -value "Memory File" -objects [get_files -of_objects [get_filesets sources_1] [list "*$file"]]

set obj [get_filesets sources_1]
set_property -name "top" -value "ai_core_top" -objects $obj

# ── constrs_1 fileset ──
if {[string equal [get_filesets -quiet constrs_1] ""]} {
  create_fileset -constrset constrs_1
}
set obj [get_filesets constrs_1]
set file [file normalize "${origin_dir}/constrs_1/ai_core_constraints.xdc"]
add_files -norecurse -fileset $obj [list $file]
set_property -name "file_type" -value "XDC" -objects [get_files -of_objects [get_filesets constrs_1] [list "*$file"]]
set_property -name "target_part" -value "xc7a35tcpg236-1" -objects $obj

# ── synth_1 / impl_1 runs ──
if {[string equal [get_runs -quiet synth_1] ""]} {
    create_run -name synth_1 -part xc7a35tcpg236-1 -flow {Vivado Synthesis 2025} -strategy "Vivado Synthesis Defaults" -constrset constrs_1
}
current_run -synthesis [get_runs synth_1]

if {[string equal [get_runs -quiet impl_1] ""]} {
    create_run -name impl_1 -part xc7a35tcpg236-1 -flow {Vivado Implementation 2025} -strategy "Vivado Implementation Defaults" -constrset constrs_1 -parent_run synth_1
}
current_run -implementation [get_runs impl_1]

puts "INFO: Project created: ${_xil_proj_name_}"
puts "INFO: Run synth_1 -> impl_1 -> write_bitstream to build."