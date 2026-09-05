module ai_core_top (
    input  logic clk,
    input  logic rst_n,
    output logic [6:0] seg,
    output logic [3:0] an
);

    logic store_en;
    logic signed [31:0] result_data [3:0];

    cpu u_cpu (
        .clk(clk),
        .rst_n(rst_n),
        .store_en(store_en),
        .result_data(result_data)
    );

    //count - 0 to 31 are layer 1, 32 to 34 are layer-2
    logic [5:0] store_count;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) 
            store_count <= 6'd0;
        else if (store_en)   
            store_count <= store_count + 6'd1;
    end

    logic layer2_valid;
    assign layer2_valid = store_en && (store_count >= 6'd32);
    logic [3:0] digit;

    argmax u_argmax (
        .clk(clk),
        .rst_n(rst_n),
        .start(store_en && (store_count == 6'd31)),
        .valid(layer2_valid),
        .out(result_data),
        .digit(digit)
    );

    seven_seg u_seven_seg (
        .clk(clk),
        .rst_n(rst_n),
        .digit(digit),
        .seg(seg),
        .an(an)
    );

endmodule