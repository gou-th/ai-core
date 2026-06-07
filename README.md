# Heterogeneous AI Core

A small INT8 systolic-array accelerator on the Basys 3, driven by a custom CPU and instruction set. The goal is to run neural network inference end-to-end on real hardware. A scalar CPU sequences a 4×4 weight-stationary systolic array through a small custom ISA.


> **Status:** Software foundation done - ISA, assemble and golden model complete. RTL begins next.

## [Assembler](assembler/)

A frozen instruction set and a Python assembler that turns a `.asm` program into the `.mem` hex the hardware runs. Each instruction encodes to a 32-bit word:

```
[31:26] opcode | [25:21] rd | [20:16] rs1 | [15:0] imm
```

```
python3 assembler/assembler.py assembler/test.asm assembler/test.mem
```

## [Golden Model](golden_model/)

A bit-accurate NumPy reference for the full MNIST forward pass - INT8 quantization, integer matmul, INT32 accumulation, ReLU, argmax. It runs at 98.6% accuracy and serves as the verification oracle: every RTL block built from here gets checked against it.

```
pip install numpy tensorflow
python3 golden_model/golden_model.py
```
![Golden model running MNIST at 98.6%](golden_model/golden_model_run.png)
