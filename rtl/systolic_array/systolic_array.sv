module systolic_array (
    input logic clk,
    input logic rst_n,
    input logic signed [7:0] act_in [3:0],
    input logic [127:0] weight_bus,
    input logic load_w,
    output logic signed [31:0] psum_out [3:0]
);

logic signed [7:0] act_wire [3:0][4:0];
logic signed [31:0] psum_wire [4:0][3:0];

generate for (genvar i = 0; i < 4; i++) begin
    assign act_wire[i][0] = act_in[i];
end endgenerate

generate for (genvar i = 0; i < 4; i++) begin
    assign psum_wire[0][i] = 32'sd0;
end endgenerate

generate for (genvar i = 0; i < 4; i++) begin
    for (genvar j = 0; j < 4; j++) begin
         pe pe_inst(
            .clk(clk),
            .rst_n(rst_n),
            .act_in(act_wire[i][j]),
            .weight(weight_bus[(i*32 + j*8) +: 8]),
            .load_w(load_w),
            .psum_in(psum_wire[i][j]),
            .act_out(act_wire[i][j+1]),
            .psum_out(psum_wire[i+1][j])
        );
    end
end endgenerate

generate for (genvar j = 0; j < 4; j++) begin
    assign psum_out[j] = psum_wire[4][j];
end endgenerate


initial begin
    $dumpfile("systolic_array.vcd");
    $dumpvars(0, systolic_array);
end


endmodule
