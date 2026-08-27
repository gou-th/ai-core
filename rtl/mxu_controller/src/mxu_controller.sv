module mxu_controller (
    input logic clk, rst_n,
    input logic matrix_start,
    input logic [1:0] matrix_cmd, // 00=M_LD_W 01=M_LD_A 10=M_MUL 11=M_ST
    output logic matrix_busy,
    output logic matrix_done,
    output logic load_w,
    output logic load_a,
    output logic store_en,
    output logic acc_en,
    output logic acc_clear
);

typedef enum logic [2:0] {
    IDLE = 3'b000,
    LOAD_W = 3'b001,
    LOAD_A = 3'b010,
    RUN = 3'b011,
    STORE = 3'b100,
    DONE = 3'b101
} state_t;

state_t current_state, next_state;
logic [3:0] cycle_count;

// state reg
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) 
        current_state <= IDLE;
    else        
        current_state <= next_state;
end

// cycle counter
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)                
        cycle_count <= 0;
    else if (current_state != RUN)     
        cycle_count <= 0;
    else                       
        cycle_count <= cycle_count + 1;
end

// next state logic
always_comb begin
    next_state = current_state;
    case (current_state)
        IDLE:   if (matrix_start) begin
                    case (matrix_cmd)
                        2'b00: next_state = LOAD_W;
                        2'b01: next_state = LOAD_A;
                        2'b10: next_state = RUN;
                        2'b11: next_state = STORE;
                    endcase
                end
        LOAD_W: next_state = DONE;
        LOAD_A: next_state = DONE;
        RUN: if (cycle_count == 4'd8) next_state = DONE;
        STORE: next_state = DONE;
        DONE: next_state = IDLE;
        default: next_state = IDLE;
    endcase
end

// output logic
always_comb begin
    matrix_busy = (current_state != IDLE);
    matrix_done = (current_state == DONE);
    load_w = (current_state == LOAD_W);
    load_a = (current_state == LOAD_A);
    acc_en = (current_state == RUN) && (cycle_count == 4'd8);
    store_en = (current_state == STORE);    
    acc_clear = (current_state == STORE);
end
endmodule