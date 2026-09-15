module ai_core_top (
    input  logic clk,
    input  logic rst_n_btn,
    input  logic rx,
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
    assign core_rst_n = rst_n && running;

    //byte to word
    logic [7:0] b0, b1, b2;
    logic [9:0] byte_cnt;
    logic ext_wrt_en;
    logic [7:0] ext_wrt_addr;
    logic [31:0] ext_wrt_data;
    logic img_done;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            byte_cnt <= 10'd0;
            ext_wrt_en <= 1'b0;
            img_done <= 1'b0;
        end else begin
            ext_wrt_en <= 1'b0;
            img_done <= 1'b0;
            if (running) begin
                byte_cnt <= 10'd0;
            end else if (uart_data_valid) begin
                case (byte_cnt[1:0])
                    2'd0: b0 <= uart_data;
                    2'd1: b1 <= uart_data;
                    2'd2: b2 <= uart_data;
                    2'd3: begin
                        ext_wrt_en <= 1'b1;
                        ext_wrt_addr <= byte_cnt[9:2];
                        ext_wrt_data <= {uart_data, b2, b1, b0};
                    end
                endcase
                if (byte_cnt == 10'd783) begin
                    byte_cnt <= 10'd0;
                    img_done <= 1'b1;
                end else begin
                    byte_cnt <= byte_cnt + 1'b1;
                end
            end
        end
    end

    logic [1:0] drain_cnt;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            running <= 1'b0;
            drain_cnt <= 2'd0;
        end else if (img_done) begin
            running <= 1'b1;
            drain_cnt <= 2'd0;
        end else if (running && store_count == 6'd35) begin
            if (drain_cnt == 2'd2) 
                running <= 1'b0;
            else 
                drain_cnt <= drain_cnt + 2'b1;
        end
    end

    cpu u_cpu (
        .clk(clk),
        .rst_n(core_rst_n),
        .store_en(store_en),
        .result_data(result_data),
        .ext_wrt_en(ext_wrt_en),
        .ext_wrt_addr(ext_wrt_addr),
        .ext_wrt_data(ext_wrt_data)
    );

    //count 0 to 31 layer 1, 32 to 34 layer-2
    logic [5:0] store_count;
    always_ff @(posedge clk or negedge core_rst_n) begin
        if (!core_rst_n)
            store_count <= 6'd0;
        else if (store_en)
            store_count <= store_count + 6'd1;
    end

    logic layer2_valid;
    assign layer2_valid = store_en && (store_count >= 6'd32);
    logic [3:0] digit;

    argmax u_argmax (
        .clk(clk),
        .rst_n(core_rst_n),
        .start(store_en && (store_count == 6'd31)),
        .valid(layer2_valid),
        .out(result_data),
        .digit(digit)
    );


    logic [3:0] display_digit;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            display_digit <= 4'd0;
        else if (running && store_count == 6'd35)
            display_digit <= digit;
    end

    seven_seg u_seven_seg (
        .clk(clk),
        .rst_n(rst_n),
        .digit(display_digit),
        .seg(seg),
        .an(an)
    );

endmodule