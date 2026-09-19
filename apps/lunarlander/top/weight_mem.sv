module weight_mem (
    input logic clk,
    input logic [12:0] addr,
    output logic [127:0] data_out
);

(* ram_style = "block" *) logic [127:0] mem [0:8191];
initial $readmemh("weights.mem", mem);

always_ff @(posedge clk) data_out <= mem[addr];

endmodule