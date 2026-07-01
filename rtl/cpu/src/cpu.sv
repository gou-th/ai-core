module cpu (
    input logic clk,
    input logic rst_n
);

logic pc_load, stall, write_en, is_branch, is_halt, is_m_op, is_act;
logic [15:0] pc_out, pc_next, imm;
logic [31:0] instr, rd_data, rs1_data, rs1_data_out;
logic [4:0] rd_addr, rs1_addr;
logic [5:0] opcode;
logic [1:0] m_op_type;
logic [4:0] wrt_addr_mux;
assign wrt_addr_mux = is_branch ? rs1_addr : rd_addr;

regfile u_regfile (
    .clk(clk),
    .rst_n(rst_n),
    .wrt_en(write_en),
    .wrt_addr(wrt_addr_mux),
    .wrt_data(rd_data),
    .read_addr(rs1_addr),
    .read_data(rs1_data)
);

fetch u_fetch (
    .clk(clk),
    .rst_n(rst_n),
    .pc_load(pc_load),
    .pc_next(pc_next),
    .stall(stall),
    .pc_out(pc_out),
    .instr_out(instr)
);

decode u_decode(
    .instr_in(instr),
    .rs1_data(rs1_data),
    .rd(rd_addr),
    .rs1_addr(rs1_addr),
    .imm(imm),
    .opcode(opcode),
    .reg_write(write_en),
    .is_branch(is_branch),
    .is_halt(is_halt),
    .is_m_op(is_m_op),
    .is_act(is_act),
    .m_op_type(m_op_type),
    .rs1_data_out(rs1_data_out)
);

execute u_execute (
    .clk(clk),
    .rst_n(rst_n),
    .opcode(opcode),
    .rs1_data(rs1_data_out),
    .imm(imm),
    .pc_out(pc_out),
    .is_branch(is_branch),
    .alu_result(rd_data),
    .pc_next(pc_next),
    .pc_load(pc_load),
    .stall(stall)
);

initial begin
    $dumpfile("cpu.vcd");
    $dumpvars(0, cpu);
end

endmodule