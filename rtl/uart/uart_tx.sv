module uart_tx #(
    parameter logic [15:0] clk_per_bit = 16'd868 //100 MHz 115200 baud
)(
    input  logic clk, rst_n,
    input  logic [7:0] data,
    input  logic tx_start,
    output logic tx,
    output logic tx_busy
);

    typedef enum logic [1:0] {IDLE, START, DATA, STOP} state_t;
    state_t state;
    logic [15:0] clk_cnt;
    logic [2:0] bit_idx;
    logic [7:0] shifter;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            clk_cnt <= 16'd0;
            bit_idx <= 3'd0;
            shifter <= 8'd0;
            tx <= 1'b1;
            tx_busy <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    tx <= 1'b1;
                    clk_cnt <= 16'd0;
                    bit_idx <= 3'd0;
                    if (tx_start) begin
                        shifter <= data;
                        tx_busy <= 1'b1;
                        state <= START;
                    end else begin
                        tx_busy <= 1'b0;
                    end
                end
                START: begin
                    tx <= 1'b0;
                    if (clk_cnt == clk_per_bit - 1) begin
                        clk_cnt <= 16'd0;
                        state <= DATA;
                    end else clk_cnt <= clk_cnt + 1'b1;
                end
                DATA: begin
                    tx <= shifter[bit_idx];
                    if (clk_cnt == clk_per_bit - 1) begin
                        clk_cnt <= 16'd0;
                        if (bit_idx == 3'd7)
                            state <= STOP;
                        else
                            bit_idx <= bit_idx + 1'b1;
                    end else clk_cnt <= clk_cnt + 1'b1;
                end
                STOP: begin
                    tx <= 1'b1;
                    if (clk_cnt == clk_per_bit - 1) begin
                        clk_cnt <= 16'd0;
                        tx_busy <= 1'b0;
                        state <= IDLE;
                    end else clk_cnt <= clk_cnt + 1'b1;
                end
            endcase
        end
    end
endmodule