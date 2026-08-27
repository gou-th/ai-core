module cpu (
    input logic clk,
    input logic rst_n,

    //weight memory interface
    output logic [15:0] weight_addr,
    input logic [127:0] weight_data,

    //activation memory interface
    output logic [15:0] act_addr,
    input logic signed [7:0] act_data [3:0],

    //result interface
    output logic store_en,
    output logic [15:0] result_addr,
    output logic signed [31:0] result_data [3:0]
);

//control signals
logic pc_load, stall, write_en, is_branch, is_halt, is_m_op, is_act;
logic matrix_start, matrix_busy, matrix_done;
logic load_w, load_a, acc_en, acc_clear;
logic [15:0] pc_out, pc_next, imm;
logic [31:0] instr, rd_data, rs1_data, rs1_data_out;
logic [4:0] rd_addr, rs1_addr, wrt_addr_mux;
logic [5:0] opcode;
logic [1:0] m_op_type, matrix_cmd;

//datapath
logic signed [7:0] act_reg [3:0];
logic signed [31:0] psum_out [3:0];

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
    .opcode(opcode),
    .rs1_data(rs1_data_out),
    .imm(imm),
    .is_m_op(is_m_op),
    .is_halt(is_halt),
    .matrix_done(matrix_done),
    .matrix_busy(matrix_busy),
    .m_op_type(m_op_type),
    .alu_result(rd_data),
    .pc_next(pc_next),
    .pc_load(pc_load),
    .stall(stall),
    .matrix_start(matrix_start),
    .matrix_cmd(matrix_cmd)
);

mxu_controller u_mxu_controller (
    .clk(clk),
    .rst_n(rst_n),
    .matrix_start(matrix_start),
    .matrix_cmd(matrix_cmd),
    .matrix_busy(matrix_busy),
    .matrix_done(matrix_done),
    .load_w(load_w),
    .load_a(load_a),
    .store_en(store_en),
    .acc_en(acc_en),
    .acc_clear(acc_clear)
);


assign weight_addr = rs1_data_out[15:0];   // M_LD_W Rs1
assign act_addr = rs1_data_out[15:0];   // M_LD_A Rs1
assign result_addr = imm;  // M_ST  Rs1, Imm

// activation holding register
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        for (int i = 0; i < 4; i++) act_reg[i] <= 8'sd0;
    else if (load_a)
        for (int i = 0; i < 4; i++) act_reg[i] <= act_data[i];
end

mxu_integration u_mxu (
    .clk(clk), .rst_n(rst_n),
    .load_w(load_w),
    .act_in(act_reg),
    .weight_bus(weight_data),
    .psum_out(psum_out)
);

accum_bank u_accum (
    .clk(clk), .rst_n(rst_n),
    .psum_in(psum_out),
    .acc_en(acc_en), .acc_clear(acc_clear),
    .acc_out(result_data)
);

initial begin
    $dumpfile("cpu_new.vcd");
    $dumpvars(0, cpu);
end

endmodule