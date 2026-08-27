module pe #(
    parameter DATA_WIDTH = 8
)
(
    input logic clk,
    input logic rst_n,
    input logic signed [DATA_WIDTH-1:0] act_in,
    input logic signed [DATA_WIDTH-1:0] weight,
    input logic signed [4*DATA_WIDTH-1:0] psum_in,
    input logic load_w,
    output logic signed [DATA_WIDTH-1:0] act_out,
    output logic signed [4*DATA_WIDTH-1:0] psum_out
);

reg signed [DATA_WIDTH-1:0] weight_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        act_out <= 0;
        psum_out <= 0;
        weight_reg <= 0;
    end else begin
        if (load_w) 
            weight_reg <= weight; // Load weight into register
        // Perform MAC operation
        act_out <= act_in; // Pass activation to next PE
        psum_out <= psum_in + (act_in*weight_reg); // Update partial sum
    end
end

endmodule