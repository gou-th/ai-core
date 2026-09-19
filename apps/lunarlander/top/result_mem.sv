module result_mem (
     input logic clk, write_en,
     input logic [8:0] write_addr,
     input logic [127:0] write_data,
     input logic [8:0] read_addr,
     output logic [127:0] data_out
 );
 
 (* ram_style = "block" *) logic [127:0] mem [0:256];
 initial $readmemh("results.mem", mem);
 
 always_ff @(posedge clk) begin
     if (write_en) begin
         mem[write_addr] <= write_data;
     end
     data_out <= mem[read_addr];
 end
 
 endmodule