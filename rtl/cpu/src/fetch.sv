module fetch (
    input logic clk,
    input logic rst_n,
    input logic pc_load,        // 0 - PC+1, 1 - take pc_next (LOOP)
    input logic [15:0] pc_next,  
    input logic stall,          // hold PC for M_MUL instr
    output logic [15:0] pc_out, 
    output logic [31:0] instr_out
);

logic [31:0] instr_mem [0:255]; // Instruction memory
initial $readmemh("program.mem", instr_mem); // Load instructions from hex file

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pc_out <= 0; 
    end else if (!stall) begin
        if (pc_load) 
            pc_out <= pc_next;   // LOOP
        else
            pc_out <= pc_out + 1;  
        end
end

assign instr_out = instr_mem[pc_out[7:0]];

endmodule

