module mxu_integration (
    input logic clk, rst_n, load_w,
    input  logic signed [7:0] act_in [3:0],
    input logic [127:0] weight_bus,
    output logic signed [31:0] psum_out [3:0]
);

logic signed [7:0] skewed_act_in [3:0];     
logic signed [31:0] psum_out_skewed [3:0];   

skew_buffer skew_buffer_inst (
    .clk(clk),
    .rst_n(rst_n),
    .act_in(act_in),
    .act_out(skewed_act_in)
);

systolic_array systolic_array_inst (
    .clk(clk),
    .rst_n(rst_n),
    .act_in(skewed_act_in),
    .weight_bus(weight_bus),
    .load_w(load_w),
    .psum_out(psum_out_skewed)
);

deskew_buffer deskew_buffer_inst (
    .clk(clk),
    .rst_n(rst_n),
    .psum_in(psum_out_skewed),
    .psum_out(psum_out)
);


initial begin
    $dumpfile("mxu_integration.vcd");
    $dumpvars(0, mxu_integration);
end

endmodule