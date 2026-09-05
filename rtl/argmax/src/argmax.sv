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

    logic signed [31:0] grp_val;
    logic [3:0] grp_idx;

    //group's local max
    always_comb begin
        grp_val = 32'sh80000000;
        grp_idx = 4'd0;
        for (int i = 0; i < 4; i++) begin
            if ((base + i[3:0]) < 4'd10 && out[i] > grp_val) begin
                grp_val = out[i];
                grp_idx = base + i[3:0];
            end
        end
    end

    //registering stage 1's output
    logic signed [31:0] grp_val_r;
    logic [3:0] grp_idx_r;
    logic valid_r;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grp_val_r <= 32'sh80000000;
            grp_idx_r <= 4'd0;
            valid_r <= 1'b0;
        end else begin
            grp_val_r <= grp_val;
            grp_idx_r <= grp_idx;
            valid_r <= valid;
        end
    end

    //compare registered group max against current best max
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n || start) begin
            best_val <= 32'sh80000000;
            best_idx <= 4'd0;
            base <= 4'd0;
        end else begin
            if (valid) base <= base + 4'd4;
            if (valid_r && grp_val_r > best_val) begin
                best_val <= grp_val_r;
                best_idx <= grp_idx_r;
            end
        end
    end
    assign digit = best_idx;

endmodule