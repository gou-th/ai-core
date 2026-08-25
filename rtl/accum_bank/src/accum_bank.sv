module accum_bank (
    input logic clk, rst_n,
    input logic signed [31:0] psum_in [3:0],
    input logic acc_en, acc_clear,
    output logic signed [31:0] acc_out [3:0]
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (int i = 0; i < 4; i++) begin
            acc_out[i] <= 32'sd0;
        end
    end else if (acc_clear) begin
        for (int j = 0; j < 4; j++) begin
            acc_out[j] <= 32'sd0;
        end
    end else if (acc_en) begin
        for (int k = 0; k < 4; k++) begin
            acc_out[k] <= acc_out[k] + psum_in[k];
        end
    end
end

endmodule