# AI Core

![FPGA](https://img.shields.io/badge/FPGA-Basys_3_XC7A35T-orange)
![HDL](https://img.shields.io/badge/HDL-SystemVerilog-blue)
![tooling](https://img.shields.io/badge/sim-cocotb_Verilator-brightgreen)

A custom AI accelerator built from scratch on a Basys 3 (Artix-7 XC7A35T) FPGA. A small custom CPU drives a 4x4 weight-stationary systolic array and the whole thing is programmed through a 10-instruction ISA with its own assembler.

It's running my own trained model: a PPO policy for LunarLander-v3 trained on my machine, quantized to INT8 and playing the game live on the board. Every action comes from the FPGA real time and checked against a NumPy reference model before it was deployed on hardware.

---

## Demo

https://github.com/user-attachments/assets/ae688596-a088-453b-9f3e-4d6d89a33b37

---

## What it is

A full custom inference stack:

1. ISA + assembler - A 32-bit instruction set for driving the matrix unit plus a two-pass Python assembler that gives `.mem` files
2. Scalar CPU - A 3-stage fetch/decode/execute sequencer with 8 registers. It isn't a general-purpose core, it's really just a controller for the matrix unit
3. 4x4 systolic array - Weight-stationary INT8 PEs mapped onto DSP slices with INT32 accumulation and then fixed-point requant + ReLU
4. Toolchain - Python codegen that turns layer shapes into assembly and quantized weights into BRAM init files
5. The policy - a -trained LunarLander, quantized to INT8 and running entirely on the board

---

## Architecture

### Instantiation hierarchy

`ai_core_top` is the top-level wrapper. Everything in `rtl/` (green) is the shared core. The amber blocks are the per-app pieces - memories, the byte-packer glue, argmax and the output stage.

![ai_core_top instantiation](docs/diagrams/ai_core_top_instantiation.svg)

### CPU internals

3-stage pipeline with the register file and the matrix-unit controller. The CPU freezes its PC while the array runs: `stall = (is_m_op && !matrix_done) || is_halt`.

![CPU internals](docs/diagrams/ai_core_cpu_internals.svg)

### Assembler toolchain

The `assembler/` folder is at the repo root. Layer shapes and quantized weights go in as inputs, `program.mem` and `weights.mem` come out and initialize the BRAMs.

![Assembler toolchain](docs/diagrams/assembler_toolchain.svg)

### End-to-end flow

The host streams observations to the board, the board sends the chosen action back over `uart_tx` and the host steps the environment and repeats. That loop is the whole demo.

![LunarLander flow](docs/diagrams/lunarlander_full_flow.svg)

---

## Results

| | LunarLander |
|---|---|
| Network | 8 -> 128 -> 128 -> 4 dense (PPO policy) |
| Quantization | INT8, per-channel weights |
| Task metric | mean reward 261.2 over 20 ep (threshold 200 = solved) |
| On-board | live, UART obs in / action out |

### Resource use (post-synthesis, `ai_core_top`, Artix-7)

| Resource | Used | Available |
|---|---|---|
| Slice LUTs | 733 (3.52%) | 20,800 |
| Slice registers (FF) | 1171 (2.81%) | 41,600 |
| Block RAM (36k tiles) | 8.5 (17%) | 50 |
| DSP48E1 | 24 (26.67%) | 90 |
| Clock | 100 MHz | |
| Setup slack (WNS) | +0.253 ns | |

---

## ISA

32-bit fixed-width encoding:

```
[31:26] opcode (6b) | [25:21] Rd (5b) | [20:16] Rs1 (5b) | [15:0] immediate (16b)
```

| Op | Mnemonic | Operands | Action |
|---|---|---|---|
| 0x00 | `LI` | Rd, Imm | Rd <- Imm |
| 0x01 | `ADDI` | Rd, Rs1, Imm | Rd <- Rs1 + Imm |
| 0x02 | `LOOP` | Rs1, Imm | Rs1 <- Rs1 - 1, branch to Imm if Rs1 != 0 |
| 0x03 | `M_LD_W` | Rs1 | load weight tile into array |
| 0x04 | `M_MUL` | Rd, Rs1 | run systolic matmul |
| 0x05 | `ACT` | Rs1 | ReLU activation |
| 0x06 | `STATUS` | Rd | Rd <- matrix-unit status |
| 0x07 | `HALT` | — | stop |
| 0x08 | `M_LD_A` | Rs1 | load activation tile |
| 0x09 | `M_ST` | Rs1 | store accumulator result |

Registers are `R0` through `R7`. Labels for `LOOP` targets get resolved in a two-pass scan.

---

## Repo layout

```
ai-core/
├── rtl/                     # shared core
│   ├── cpu/                 # fetch, decode, execute, regfile
│   ├── pe/                  # INT8 processing element (DSP slice)
│   ├── systolic_array/      # 4x4 weight-stationary array
│   ├── skew_buffer/         # input skew
│   ├── deskew_buffer/       # output de-skew
│   ├── mxu_controller/      # matrix-unit FSM
│   ├── mxu_integration/     # array + controller wiring
│   ├── accum_bank/          # INT32 accumulators
│   ├── requant/             # fixed-point ReLU + rescale
│   └── uart/                # uart_rx, uart_tx
├── assembler/               # toolchain
│   ├── assembler.py         # two-pass assembler -> .mem
│   ├── build_program.py     # interactive: layer pairs -> asm -> .mem
│   ├── convert_weights.py   # quantized .npy weights -> weights.mem
│   └── layer_gen.py         # layer-shape -> assembly codegen
├── apps/
│   └── lunarlander/
│       ├── top/              # ai_core_top.sv (3-layer, byte-packer), program.asm
│       ├── argmax/           # 4-way Q16 dequant comparator
│       ├── seven_seg/
│       ├── golden_model/     # train_quantize.py (PPO), golden.py, w*.npy, scales.json
│       ├── lunarlander_host/ # host_script.py (drives the board + render window)
│       ├── sim/
│       ├── constrs_1/
│       └── build.tcl
├── LICENSE
└── README.md
```

---

## Quickstart

Setup is split across two folders: `~/ai_core` on WSL for cocotb / Verilator / Python and `C:\ai_core_vivado` on Windows for Vivado. Files get copied between them.

### 1. Generate the memory files (WSL)

Program first then weights. Layer pairs carry a folded bias row, so 8+1 and 128+1.

```bash
python assembler/assembler.py apps/lunarlander/top/program.asm apps/lunarlander/top/program.mem

python assembler/convert_weights.py 9,128;129,128;129,4 \
    apps/lunarlander/golden_model/w1.npy apps/lunarlander/golden_model/w2.npy apps/lunarlander/golden_model/w3.npy \
    -o apps/lunarlander/top/weights.mem
```

If you don't want to hand-write the `.asm`, `python assembler/build_program.py` takes the layer `(in,out)` pairs and does the codegen + assembly in one go. The `.npy` weights come out of `golden_model/train_quantize.py`.

### 2. Simulate (WSL)

```bash
cd apps/lunarlander/sim && make
```

### 3. Build the bitstream (Windows -> Vivado)

```powershell
cd path/to/apps/lunarlander    # use the path on your device
source build.tcl
```

Run this from the Vivado Tcl shell.

### 4. Run it on hardware (Windows)

Serial only works on the Windows side. Port and baud are hardcoded in `host_script.py` (`COM4`, 115200) so change those if yours differ.

```powershell
python apps/lunarlander/lunarlander_host/host_script.py
```