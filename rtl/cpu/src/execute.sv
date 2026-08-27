module execute (
    input logic [5:0] opcode,
    input logic [31:0] rs1_data,
    input logic [15:0] imm,
    input logic is_m_op,
    input logic is_halt,
    input logic matrix_done,
    input logic matrix_busy,
    input logic [1:0] m_op_type,
    output logic [31:0] alu_result,
    output logic [15:0] pc_next,
    output logic pc_load,
    output logic stall,
    output logic matrix_start,
    output logic [1:0] matrix_cmd
);

always_comb begin
    alu_result = 0;
    pc_next = 0;
    pc_load = 0;
    stall = 0;
    matrix_start = 0;
    matrix_cmd = 2'b00;

    case (opcode) 
        6'h00: // LI
            alu_result = {{16'b0},imm}; // zero-extend immediate
        6'h01: // ADDI
            alu_result = rs1_data + {{16{imm[15]}},imm}; // sign-extend immediate
        6'h02: begin // LOOP
            alu_result = (rs1_data == 32'd0) ? 32'd0 : rs1_data - 1; 
            pc_next = imm;
            pc_load = (rs1_data != 32'd0) && (rs1_data - 32'd1 != 32'd0); 
        end
        6'h06: //STATUS
            alu_result = {30'B0, matrix_busy, matrix_done};
        default: ;
    endcase

    matrix_start = is_m_op;
    matrix_cmd = m_op_type;
    stall = (is_m_op && !matrix_done) || is_halt;
end

endmodule