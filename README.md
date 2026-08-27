# Heterogeneous AI Core
 
A small INT8 systolic-array accelerator on the Basys 3, driven by a custom CPU and instruction set. The goal is to run neural network inference end-to-end on real hardware. A scalar CPU sequences a 4×4 weight-stationary systolic array through a small custom ISA.
 
![Language](https://img.shields.io/badge/Language-SystemVerilog-blue) ![Sim](https://img.shields.io/badge/Sim-Verilator%20%2B%20cocotb-9cf) ![Target](https://img.shields.io/badge/Target-Basys%203%20(Artix--7)-lightgrey) 
 
## Spec
 
| | |
|---|---|
| Numeric system | INT8 in, INT32 accumulate |
| Array | 4×4, weight-stationary |
| CPU | 3-stage scalar (fetch / decode / execute) |
| ISA | 10 custom opcodes, 32-bit encoding |
| Target | Basys 3 (Artix-7, XC7A35T) |
| Verification | cocotb golden model in NumPy |
 
## ISA
 
`[31:26] opcode | [25:21] rd | [20:16] rs1 | [15:0] imm`
 
| Op | Mnemonic | Operands | Action |
|---|---|---|---|
| 0x00 | `LI` | Rd, Imm | Rd ← Imm |
| 0x01 | `ADDI` | Rd, Rs1, Imm | Rd ← Rs1 + Imm |
| 0x02 | `LOOP` | Rs1, Imm | Rs1 ← Rs1 − 1; branch if Rs1 ≠ 0 |
| 0x03 | `M_LD_W` | Rs1 | load weight tile into array |
| 0x04 | `M_MUL` | Rd, Rs1 | run systolic matmul |
| 0x05 | `ACT` | Rs1, Imm | ReLU activation |
| 0x06 | `STATUS` | Rd | Rd ← matrix unit status |
| 0x07 | `HALT` | — | stop |
| 0x08 | `M_LD_A` | Rs1 | load activation tile |
| 0x09 | `M_ST` | Rs1, Imm | store accumulator result |
 
## [Assembler](assembler/)
 
Turns `.asm` into the `.mem` hex the hardware loads.
 
```
python3 assembler/assembler.py assembler/test.asm assembler/test.mem
```
 
## [Golden Model](golden_model/)
 
Bit-accurate NumPy reference for the full MNIST forward pass - INT8 quantization, integer matmul, INT32 accumulation, ReLU, argmax. Runs at 98.6% accuracy. Will serve as the verification oracle once the systolic array produces MNIST-scale outputs to check against; PE and CPU tests so far are verified against pre-computed expected values.
 
```
pip install numpy tensorflow
python3 golden_model/golden_model.py
```
 
## [RTL](rtl/)
 
Each block lives in its own folder, split into `src/` (design) and `sim/` (cocotb testbench + Makefile).
 
### PE - [`rtl/pe/`](rtl/pe/)
 
Single weight-stationary processing element. INT8×INT8 → INT32 accumulate, 1-cycle registered output. Verified against pre-computed MAC values across signed weight/activation combinations.
 
```
cd rtl/pe/sim && make
```

### CPU - [`rtl/cpu/`](rtl/cpu/)
 
3-stage scalar CPU running the ISA above. Verified with a pre-assembled integration test cross-checked against a GTKWave trace and cocotb.
 
```
cd rtl/cpu/sim && make
````

### Systolic Array - [`rtl/systolic_array/`](rtl/systolic_array/)

4×4 mesh of the verified PE, weight-stationary. Weights broadcast to all 16 PEs in a single `load_w` cycle rather than shifting row-by-row. This is a deliberate deviation from the classic TPU-style array.

```
cd rtl/systolic_array/sim && make
```

### Skew Buffer - [`rtl/skew_buffer/`](rtl/skew_buffer/)

Staggers the 4 incoming activations by 0/1/2/3 cycles i.e. row i delayed i cycles so they enter the array diagonally, as the systolic dataflow requires. Verified standalone against expected per-row delay.

```
cd rtl/skew_buffer/sim && make
```

### Deskew Buffer - [`rtl/deskew_buffer/`](rtl/deskew_buffer)

Reverses the array's output stagger. `psum_out[j]` exits the array at a different cycle per column; this buffer delays each column (3/2/1/0 cycles) so all 4 land aligned on the same cycle. Verified standalone.

```
cd rtl/deskew_buffer/sim && make
```

### MXU Integration - [`rtl/mxu_integration/`](rtl/mxu_integration/)

Wires skew_buffer -> systolic_array -> deskew_buffer into one datapath. Raw activations in, aligned INT32 psums out. 

```
cd rtl/mxu_integration/sim && make
```

### Accumulator Bank - [`rtl/accum_bank/`](rtl/accum_bank/)

4x INT32 registers accumulating partial sums across multiple tiles of a layer. `acc_en` adds current `psum_in` into the running total; `acc_clear` resets it for a new layer.

```
cd rtl/accum_bank/sim && make
```

### MXU Controller - [`rtl/mxu_controller/`](rtl/mxu_controller/)

6 state FSM (IDLE -> LOAD_W -> LOAD_A -> RUN -> STORE -> DONE) managing weight and activation preloads, systolic array execution and accumulator bank integration. Acts as the main handshaking mechanism with CPU.

```
cd rtl/mxu_controller/sim && make
```

### CPU <-> MXU Integration - [`rtl/cpu/sim/test_cpu_mxu.py`](rtl/cpu/sim/test_cpu_mxu.py)

End to end CPU and MXU handshake verification. CPU executes a new assembler script [`cpu_test.asm`](rtl/cpu/sim/cpu_test.asm) and verified using reference run.

```
cd rtl/cpu/sim && make
```

