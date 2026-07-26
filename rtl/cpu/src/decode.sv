module decode (
    input logic [31:0] instr_in,
    input logic [31:0] rs1_data,
    output logic [4:0] rd,
    output logic [4:0] rs1_addr,
    output logic [15:0] imm,
    output logic [5:0] opcode,
    output logic reg_write,
    output logic is_branch,
    output logic is_halt,
    output logic is_m_op,
    output logic is_act,
    output logic [1:0] m_op_type,    // 00=M_LD_W 01=M_LD_A 10=M_MUL 11=M_ST
    output logic [31:0] rs1_data_out
);


assign opcode = instr_in[31:26];
assign rd = instr_in[25:21];
assign rs1_addr = instr_in[20:16];
assign imm = instr_in[15:0];
assign rs1_data_out = rs1_data;

always_comb begin
    reg_write = 0;
    is_branch = 0;
    is_halt = 0;
    is_m_op = 0;
    is_act = 0;
    m_op_type = 2'b00;
    case (opcode)
        6'h00: // LI
            reg_write = 1; 
        6'h01: // ADDI
            reg_write = 1;
        6'h02: begin // LOOP 
            reg_write = 1;
            is_branch = 1;
        end
        6'h03: begin // M_LD_W
            is_m_op = 1;
            m_op_type = 2'b00;
        end
        6'h04: begin // M_MUL
            is_m_op = 1;
            m_op_type = 2'b10;
        end
        6'h05: begin // ACT
            is_act = 1;
        end
        6'h06: // STATUS
            reg_write = 1;
        6'h07: // HALT
            is_halt = 1;
        6'h08: begin // M_LD_A
            is_m_op = 1;
            m_op_type = 2'b01;
        end
        6'h09: begin // M_ST
            is_m_op = 1;
            m_op_type = 2'b11;
        end
        default: ;
    endcase
end
endmodule
