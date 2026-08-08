module execute (
    input logic clk,
    input logic rst_n,
    input logic [5:0] opcode,
    input logic [31:0] rs1_data,
    input logic [15:0] imm,
    input logic [15:0] pc_out,
    input logic is_branch,
    output logic [31:0] alu_result,
    output logic [15:0] pc_next,
    output logic pc_load,
    output logic stall
);

always_comb begin
    alu_result = 0;
    pc_next = 0;
    pc_load = 0;
    stall = 0;

    case (opcode) 
        6'h00: // LI
            alu_result = {{16'b0},imm}; // zero-extend immediate
        6'h01: // ADDI
            alu_result = rs1_data + {{16'b0},imm};
        6'h02: begin // LOOP
            alu_result = rs1_data - 1;
            pc_next = imm;
            pc_load = (rs1_data - 1) != 0;
        end
        6'h06: //STATUS
            alu_result = 1;
        default: ;
    endcase
end

endmodule