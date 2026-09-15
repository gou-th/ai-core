module argmax (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    input  logic valid,
    input  logic signed [31:0] out [3:0],
    output logic [3:0] digit
);

    logic signed [31:0] best_val;
    logic [3:0] best_idx;
    logic [3:0] base;

    //registered two pairwise comparisons (0 vs 1 and 2 vs 3)
    logic signed [31:0] pair01_val, pair23_val;
    logic [3:0] pair01_idx, pair23_idx;
    logic valid_s1;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pair01_val <= 32'sh80000000;
            pair23_val <= 32'sh80000000;
            pair01_idx <= 4'd0;
            pair23_idx <= 4'd0;
            valid_s1 <= 1'b0;
        end else begin
            if (out[0] >= out[1]) begin
                pair01_val <= out[0];
                pair01_idx <= base;
            end else begin
                pair01_val <= out[1];
                pair01_idx <= base + 4'd1;
            end

            if ((base + 4'd2) < 4'd10 && out[2] >= out[3]) begin
                pair23_val <= out[2];
                pair23_idx <= base + 4'd2;
            end else if ((base + 4'd3) < 4'd10) begin
                pair23_val <= out[3];
                pair23_idx <= base + 4'd3;
            end else begin
                pair23_val <= 32'sh80000000;
                pair23_idx <= 4'd0;
            end
            valid_s1 <= valid;
        end
    end

    //combine the two pair max then compare against current max
    logic signed [31:0] grp_val_r;
    logic [3:0] grp_idx_r;
    logic valid_s2;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grp_val_r <= 32'sh80000000;
            grp_idx_r <= 4'd0;
            valid_s2 <= 1'b0;
        end else begin
            if (pair01_val >= pair23_val) begin
                grp_val_r <= pair01_val;
                grp_idx_r <= pair01_idx;
            end else begin
                grp_val_r <= pair23_val;
                grp_idx_r <= pair23_idx;
            end
            valid_s2 <= valid_s1;
        end
    end

    //compare against current max
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n || start) begin
            best_val <= 32'sh80000000;
            best_idx <= 4'd0;
            base <= 4'd0;
        end else begin
            if (valid) base <= base + 4'd4;
            if (valid_s2 && grp_val_r > best_val) begin
                best_val <= grp_val_r;
                best_idx <= grp_idx_r;
            end
        end
    end
    assign digit = best_idx;

endmodule