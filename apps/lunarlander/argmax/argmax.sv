module argmax (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    input  logic valid,
    input  logic signed [31:0] acc [3:0],
    output logic [1:0]  action,
    output logic done
);

    logic signed [31:0] pair01_val, pair23_val;
    logic [1:0] pair01_idx, pair23_idx;
    logic valid_s1;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pair01_val <= 32'sh80000000;
            pair23_val <= 32'sh80000000;
            pair01_idx <= 2'd0;
            pair23_idx <= 2'd0;
            valid_s1 <= 1'b0;
        end else begin
            if (acc[0] >= acc[1]) begin
                pair01_val <= acc[0];
                pair01_idx <= 2'd0;
            end else begin
                pair01_val <= acc[1];
                pair01_idx <= 2'd1;
            end
            if (acc[2] >= acc[3]) begin
                pair23_val <= acc[2];
                pair23_idx <= 2'd2;
            end else begin
                pair23_val <= acc[3];
                pair23_idx <= 2'd3;
            end
            valid_s1 <= valid;
        end
    end

    logic valid_s2;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n || start) begin
            action <= 2'd0;
            valid_s2 <= 1'b0;
        end else begin
            if (valid_s1) begin
                action <= (pair01_val >= pair23_val) ? pair01_idx : pair23_idx;
            end
            valid_s2 <= valid_s1;
        end
    end

    assign done = valid_s2;

endmodule