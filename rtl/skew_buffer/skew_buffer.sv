module skew_buffer (
    input logic clk, rst_n,
    input logic signed [7:0] act_in [3:0],
    output logic signed [7:0] act_out [3:0]
);

logic signed [7:0] shift_reg [3:0][2:0]; 

assign act_out[0] = act_in[0];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (int i = 0; i < 4; i++) begin
            for (int k = 0; k < 3; k++) begin
                shift_reg[i][k] <= 8'sd0;
            end
        end
    end else begin
        shift_reg[1][0] <= act_in[1];

        shift_reg[2][0] <= act_in[2];
        shift_reg[2][1] <= shift_reg[2][0];

        shift_reg[3][0] <= act_in[3];
        shift_reg[3][1] <= shift_reg[3][0];
        shift_reg[3][2] <= shift_reg[3][1]; 

    end
end

assign act_out[1] = shift_reg[1][0];
assign act_out[2] = shift_reg[2][1];
assign act_out[3] = shift_reg[3][2];

initial begin
    $dumpfile("skew_buffer.vcd");
    $dumpvars(0, skew_buffer);
    for (int i = 0; i < 4; i++) begin
        $dumpvars(0, act_in[i]);
        $dumpvars(0, act_out[i]);
    end
end
endmodule