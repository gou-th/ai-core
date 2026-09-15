module uart_rx #(
    parameter logic [15:0] clk_per_bit = 16'd868      //100 MHz 115200 baud
)(
    input logic clk, rst_n,
    input logic rx,
    output logic [7:0] data,
    output logic data_valid
);

    logic rx_1, rx_2;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_1 <= 1'b1;
            rx_2 <= 1'b1;
        end else begin
            rx_1 <= rx;
            rx_2 <= rx_1;
        end
    end

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
            data <= 8'd0;
            data_valid <= 1'b0;
        end else begin
            data_valid <= 1'b0;
            case (state)
                IDLE: begin
                    clk_cnt <= 16'd0;
                    bit_idx <= 3'd0;
                    if (!rx_2) state <= START;
                end
                START: begin
                    if (clk_cnt == (clk_per_bit/2) - 1) begin
                        clk_cnt <= 16'd0;
                        state <= rx_2 ? IDLE : DATA;
                    end else clk_cnt <= clk_cnt + 1'b1;
                end
                DATA: begin
                    if (clk_cnt == clk_per_bit - 1) begin
                        clk_cnt <= 16'd0;
                        shifter[bit_idx] <= rx_2;
                        if (bit_idx == 3'd7) 
                            state <= STOP;
                        else 
                            bit_idx <= bit_idx + 1'b1;
                    end else clk_cnt <= clk_cnt + 1'b1;
                end
                STOP: begin
                    if (clk_cnt == clk_per_bit - 1) begin
                        clk_cnt <= 16'd0;
                        data <= shifter;
                        data_valid <= 1'b1;
                        state <= IDLE;
                    end else clk_cnt <= clk_cnt + 1'b1;
                end
            endcase
        end
    end
endmodule