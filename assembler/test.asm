LI R1, 0x0010        ; load weight base address
LI R2, 0x0020        ; load activation base address
M_LD_W R1            ; load weight tile from mem[R1]
M_LD_A R2            ; load activation tile from mem[R2]
M_MUL R0, R1         ; run matmul, result dest R0
ACT R0, 4            ; ReLU over 4 elements
M_ST R0, 0x0030      ; store results to mem[0x0030]
HALT