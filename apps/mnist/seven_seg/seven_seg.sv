module seven_seg (
    input  logic clk,
    input  logic rst_n,
    input  logic [3:0] digit,
    output logic [6:0] seg,    
    output logic [3:0] an   //active low select
);

    always_comb begin
        case (digit)
            4'd0: seg = 7'b1000000;
            4'd1: seg = 7'b1111001;
            4'd2: seg = 7'b0100100;
            4'd3: seg = 7'b0110000;
            4'd4: seg = 7'b0011001;
            4'd5: seg = 7'b0010010;
            4'd6: seg = 7'b0000010;
            4'd7: seg = 7'b1111000;
            4'd8: seg = 7'b0000000;
            4'd9: seg = 7'b0010000;
            default: seg = 7'b1111111;
        endcase
    end
    assign an = 4'b1110;   //rightmost digit
endmodule