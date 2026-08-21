module deskew_buffer (
    input logic clk, rst_n,
    input logic [31:0] psum_in [3:0],
    output logic [31:0] psum_out [3:0]
);

logic signed [31:0] shift_reg [3:0][2:0]; 

assign psum_out[3] = psum_in[3];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (int i = 0; i < 4; i++) begin
            for (int k = 0; k < 3; k++) begin
                shift_reg[i][k] <= 32'sd0;
            end
        end
    end else begin
        shift_reg[0][0] <= psum_in[0];
        shift_reg[0][1] <= shift_reg[0][0];
        shift_reg[0][2] <= shift_reg[0][1];

        shift_reg[1][0] <= psum_in[1];
        shift_reg[1][1] <= shift_reg[1][0];

        shift_reg[2][0] <= psum_in[2];

    end
end

assign psum_out[0] = shift_reg[0][2];  
assign psum_out[1] = shift_reg[1][1];
assign psum_out[2] = shift_reg[2][0];   

initial begin
    $dumpfile("deskew_buffer.vcd");
    $dumpvars(0, deskew_buffer);
    for (int i = 0; i < 4; i++) begin
        $dumpvars(0, psum_in[i]);
        $dumpvars(0, psum_out[i]);
    end
end
endmodule