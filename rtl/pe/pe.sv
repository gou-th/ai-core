module pe #(
    parameter DATA_WIDTH = 8
)(
    input logic clk, rst_n,
    input logic load_w,
    input logic signed [DATA_WIDTH-1:0] act_in, weight,
    input logic signed [4*DATA_WIDTH-1:0] psum_in,
    output logic signed [DATA_WIDTH-1:0] act_out,
    output logic signed [4*DATA_WIDTH-1:0] psum_out
);

reg signed [DATA_WIDTH-1:0] weight_reg;

(* use_dsp = "yes" *)
logic signed [2*DATA_WIDTH-1:0] product;

assign product = act_in * weight_reg;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        act_out <= 0;
        psum_out <= 0;
        weight_reg <= 0;
    end else begin
        if (load_w)
            weight_reg <= weight;
        act_out <= act_in;
        psum_out <= psum_in + {{(4*DATA_WIDTH-2*DATA_WIDTH){product[2*DATA_WIDTH-1]}}, product};
    end
end

endmodule