;Layer 1 - 784 to 128, ACT writes to act_mem[196 till 227]
LI R1, 32  ;32 output groups
LI R3, 0   ;weight starting addr
LI R5, 196 ;act_mem[196 till 227]
LI R6, 0   ;result_mem[0 till 31]

OUTER1: 
LI R2, 196  ;196 input tiles
LI R4, 0    ;re-read image 

INNER1:
M_LD_W R3
M_LD_A R4
M_MUL R0, R0
ADDI R3, R3, 1
ADDI R4, R4, 1
LOOP R2, INNER1

ACT R5
M_ST R6
ADDI R5, R5, 1
ADDI R6, R6, 1
LOOP R1, OUTER1

;Layer 2 - 128 to 10, results to result_mem[32 till 34]
LI R1, 3
LI R6, 32

OUTER2:
LI R2, 32
LI R4, 196

INNER2:
M_LD_W R3
M_LD_A R4
M_MUL R0, R0
ADDI R3, R3, 1
ADDI R4, R4, 1
LOOP R2, INNER2

M_ST R6
ADDI R6, R6, 1
LOOP R1, OUTER2

HALT