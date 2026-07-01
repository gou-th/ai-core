module regfile (
    input logic clk,
    input logic rst_n,
    input logic wrt_en,
    input logic [4:0] wrt_addr,
    input logic [31:0] wrt_data,
    input logic [4:0] read_addr,
    output logic [31:0] read_data
);

logic [31:0] regs [31:0];
integer i;

always @(posedge clk) begin
    if (!rst_n) begin 
        for (i = 0; i< 32; i = i+1)
            regs[i] <= 0;
    end
    else if (wrt_en) regs[wrt_addr] <= wrt_data;
end

assign read_data = regs[read_addr];
    
endmodule
