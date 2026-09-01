module requant #(
    parameter int M=955,
    parameter int S=24)(
    input logic signed [31:0] acc_in [3:0],  //4 accumulator values 
    output logic signed [7:0] act_out [3:0]  //4 requantized values
);

logic signed [63:0] product [3:0];
logic signed [63:0] shifted_wide [3:0];
logic signed [31:0] shifted [3:0];

always_comb begin
    for (int i=0;i<4;i++) begin
        product[i] = (acc_in[i]<0) ? 64'sd0 : (acc_in[i]*M);
        shifted_wide[i] = product[i] >>> S;
        shifted[i] = shifted_wide[i][31:0];

        if (shifted[i]>127) act_out[i] = 8'sd127;
        else act_out[i] = shifted[i][7:0];
    end
end
endmodule