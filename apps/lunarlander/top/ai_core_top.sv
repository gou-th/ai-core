module ai_core_top (
    input logic clk,
    input logic rst_n_btn,
    input logic rx,
    output logic tx,
    output logic [6:0] seg,
    output logic [3:0] an
);

    logic rst_n;
    assign rst_n = ~rst_n_btn;

    logic store_en;
    logic signed [31:0] result_data [3:0];

    logic [7:0] uart_data;
    logic uart_data_valid;

    uart_rx #(.clk_per_bit(16'd868)) u_uart_rx (
        .clk(clk),
        .rst_n(rst_n),
        .rx(rx),
        .data(uart_data),
        .data_valid(uart_data_valid)
    );

    logic running;
    logic core_rst_n;

    typedef enum logic [2:0] {BIAS_IDLE, BIAS_W2, BIAS_W35, BIAS_W68, BIAS_DONE} bias_state_t;
    bias_state_t bias_state;
    logic bias_init_done;
    logic bias_wrt_en;
    logic [7:0] bias_wrt_addr;
    logic [31:0] bias_wrt_data;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bias_state <= BIAS_IDLE;
            bias_init_done <= 1'b0;
            bias_wrt_en <= 1'b0;
        end else begin
            bias_wrt_en <= 1'b0;
            case (bias_state)
                BIAS_IDLE: begin
                    bias_wrt_en <= 1'b1;
                    bias_wrt_addr <= 8'd2;
                    bias_wrt_data <= 32'h0000007F;
                    bias_state <= BIAS_W2;
                end
                BIAS_W2: begin
                    bias_wrt_en <= 1'b1;
                    bias_wrt_addr <= 8'd35;
                    bias_wrt_data <= 32'h0000007F;
                    bias_state <= BIAS_W35;
                end
                BIAS_W35: begin
                    bias_wrt_en <= 1'b1;
                    bias_wrt_addr <= 8'd68;
                    bias_wrt_data <= 32'h0000007F;
                    bias_state <= BIAS_W68;
                end
                BIAS_W68: begin
                    bias_init_done <= 1'b1;
                    bias_state <= BIAS_DONE;
                end
                default: ;
            endcase
        end
    end

    assign core_rst_n = rst_n && (running || !bias_init_done);

    //byte to word 
    logic [7:0] b0, b1, b2;
    logic [3:0] byte_cnt;
    logic ext_wrt_en;
    logic [7:0] ext_wrt_addr;
    logic [31:0] ext_wrt_data;
    logic obs_done;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            byte_cnt <= 4'd0;
            ext_wrt_en <= 1'b0;
            obs_done <= 1'b0;
        end else begin
            ext_wrt_en <= 1'b0;
            obs_done <= 1'b0;
            if (running) begin
                byte_cnt <= 4'd0;
            end else if (uart_data_valid) begin
                case (byte_cnt[1:0])
                    2'd0: b0 <= uart_data;
                    2'd1: b1 <= uart_data;
                    2'd2: b2 <= uart_data;
                    2'd3: begin
                        ext_wrt_en <= 1'b1;
                        ext_wrt_addr <= {6'd0, byte_cnt[3:2]};
                        ext_wrt_data <= {uart_data, b2, b1, b0};
                    end
                endcase
                if (byte_cnt == 4'd7) begin  
                    byte_cnt <= 4'd0;
                    obs_done <= 1'b1;
                end else begin
                    byte_cnt <= byte_cnt + 1'b1;
                end
            end
        end
    end

    //store_count boundaries: layer1 (128 outputs / 4 = 32 chunks) + layer2 (128 outputs / 4 = 32 chunks) + layer3 (4 outputs / 4 = 1 chunk) = 65 total.
  
    logic [1:0] drain_cnt;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            running <= 1'b0;
            drain_cnt <= 2'd0;
        end else if (obs_done) begin
            running <= 1'b1;
            drain_cnt <= 2'd0;
        end else if (running && store_count == 7'd65) begin
            if (drain_cnt == 2'd2)
                running <= 1'b0;
            else
                drain_cnt <= drain_cnt + 2'b1;
        end
    end

    logic [7:0] cpu_ext_wrt_addr;
    logic [31:0] cpu_ext_wrt_data;
    logic cpu_ext_wrt_en;

    assign cpu_ext_wrt_en = bias_init_done ? ext_wrt_en : bias_wrt_en;
    assign cpu_ext_wrt_addr = bias_init_done ? ext_wrt_addr : bias_wrt_addr;
    assign cpu_ext_wrt_data = bias_init_done ? ext_wrt_data : bias_wrt_data;

    cpu #(.REQUANT_M(885580), .REQUANT_S(24)) u_cpu (
        .clk(clk),
        .rst_n(core_rst_n),
        .store_en(store_en),
        .result_data(result_data),
        .ext_wrt_en(cpu_ext_wrt_en),
        .ext_wrt_addr(cpu_ext_wrt_addr),
        .ext_wrt_data(cpu_ext_wrt_data)
    );

    //count 0-31 layer1, 32-63 layer2, 64 layer3 
    logic [6:0] store_count;
    always_ff @(posedge clk or negedge core_rst_n) begin
        if (!core_rst_n)
            store_count <= 7'd0;
        else if (store_en)
            store_count <= store_count + 7'd1;
    end

    logic [1:0] action;
    logic argmax_done;

    argmax u_argmax (
        .clk(clk),
        .rst_n(core_rst_n),
        .start(store_en && (store_count == 7'd63)),
        .valid(store_en && (store_count == 7'd64)),
        .acc(result_data),
        .action(action),
        .done(argmax_done)
    );

    logic [1:0] display_action;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            display_action <= 2'd0;
        else if (argmax_done)
            display_action <= action;
    end

        // fire uart_tx once per inference, right when the action is ready
    logic tx_start;
    logic tx_busy;
    logic argmax_done_prev;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            argmax_done_prev <= 1'b0;
            tx_start <= 1'b0;
        end else begin
            argmax_done_prev <= argmax_done;
            tx_start <= argmax_done && !argmax_done_prev;
        end
    end

    uart_tx #(.clk_per_bit(16'd868)) u_uart_tx (
        .clk(clk),
        .rst_n(rst_n),
        .data({6'd0, action}),
        .tx_start(tx_start),
        .tx(tx),
        .tx_busy(tx_busy)
    );

    seven_seg u_seven_seg (
        .clk(clk),
        .rst_n(rst_n),
        .digit({2'd0, display_action}),
        .seg(seg),
        .an(an)
    );

endmodule