<!-- badges: TBD — add once CI / license shields are ready -->
<!-- e.g. ![build](...) ![license](...) ![board](https://img.shields.io/badge/FPGA-Basys%203%20XC7A35T-orange) -->

# AI Core

A heterogeneous AI accelerator built from scratch on a **Basys 3 (Xilinx Artix-7 XC7A35T)** FPGA: a custom scalar CPU driving a **4×4 weight-stationary systolic array**, programmed through a custom **10-opcode ISA** and its two-pass assembler. INT8 inference done end-to-end on Basys 3 hardware proven bit-exact against a NumPy golden model.

It runs two workloads on the *same unmodified core*:
- **MNIST** digit classification (proof-of-concept)
- **LunarLander-v3** — a PPO policy network trained by me, quantized to INT8, playing the game live from the board


---

## Demo

[![AI Core demo](docs/img/demo-thumb.png)](https://youtu.be/VIDEO_ID_TBD)

*(click to play — hosted on YouTube)*

---

## What it is

A full custom inference stack:

1. **ISA + assembler** - a 32-bit instruction set for driving a matrix unit, with a Python two-pass assembler that emits `.mem` files.
2. **Scalar CPU** - 3-stage fetch/decode/execute sequencer with an 8-register file. Not a general-purpose core — a controller for the matrix unit.
3. **4×4 systolic array** - weight-stationary INT8 PEs (mapped to DSP48E1 slices), INT32 accumulation, fixed-point requantize + ReLU.
4. **Toolchain** - shared Python codegen that turns layer shapes into assembly and quantized weights into BRAM init files.
5. **Two apps** - MNIST and LunarLander, each a thin per-app wrapper around the shared core.

Verified bit-exact in simulation (cocotb + Verilator) **and** on physical hardware. Timing closed at **100 MHz** on the Basys 3.

---

## Architecture

### Instantiation hierarchy

`ai_core_top` is the per-app wrapper. Everything in `rtl/` (teal) is shared and identical across apps; everything per-app (amber) — memories, byte-packer glue, argmax, output stage — lives under `apps/<app>/`.

![ai_core_top instantiation](docs/diagrams/ai_core_top_instantiation.svg)

### CPU internals

3-stage pipeline with a shared regfile and the matrix-unit controller. The CPU stalls (PC freeze) while the array runs: `stall = (is_m_op && !matrix_done) || is_halt`.

![CPU internals](docs/diagrams/ai_core_cpu_internals.svg)

### Assembler toolchain

Shared, root-level `assembler/`. Per-app layer shapes and quantized weights go in; `program.mem` and `weights.mem` come out and initialize the BRAMs.

![Assembler toolchain](docs/diagrams/assembler_toolchain.svg)

### End-to-end flow — MNIST

One-shot: host sends a test image over UART, board runs inference, predicted digit shows on the 7-segment display.

![MNIST flow](docs/diagrams/mnist_full_flow.svg)

### End-to-end flow — LunarLander

Closed loop: host GUI streams observations to the board, board returns the chosen action over `uart_tx`, host steps the environment and repeats.

![LunarLander flow](docs/diagrams/lunarlander_full_flow.svg)

---

## Results

| | **MNIST** | **LunarLander** |
|---|---|---|
| Network | 784 → 128 → 10 dense | 8 → 128 → 128 → 4 dense (PPO policy) |
| Quantization | INT8, per-tensor | INT8, **per-channel** weights |
| Task metric | bit-exact vs golden (20/20 test images) | **mean reward 261.2** / 20 ep (>200 = solved) |
| On-board | live, UART image input | live, UART obs in / action out |

### Resource utilization (post-synthesis, `ai_core_top`, XC7A35T)

| Resource | MNIST | LunarLander | Available |
|---|---|---|---|
| Slice LUTs | 1574 (7.57%) | 733 (3.52%) | 20,800 |
| Slice Registers (FF) | 1193 (2.87%) | 1171 (2.81%) | 41,600 |
| Block RAM (36k tiles) | 32.5 (65%) | 8.5 (17%) | 50 |
| DSP48E1 | 16 (17.78%) | 24 (26.67%) | 90 |
| Clock | 100 MHz | 100 MHz | — |
| WNS (setup) | +0.035 ns | +0.253 ns | — |

<!-- NUMBERS TO CONFIRM: -->
<!-- - LunarLander DSP: synth report says 24; you noted 22 (post-implementation?). -->
<!-- - LunarLander WNS: screenshot says 0.253 ns; you noted 0.256. -->
<!-- - MNIST WNS +0.035 ns is from an earlier capture — reconfirm against a fresh timing summary. -->
<!-- - LUT counts are post-synthesis; post-implementation is typically lower. -->

MNIST uses exactly the 16 DSPs of the 4×4 array; LunarLander's extra 8 come from the per-channel Q16 dequant multiplies in its argmax stage. MNIST's 784×128 first layer dominates its block-RAM usage.

---

## ISA reference

32-bit fixed-width encoding:

```
[31:26] opcode (6b) | [25:21] Rd (5b) | [20:16] Rs1 (5b) | [15:0] immediate (16b)
```

| Op | Mnemonic | Operands | Action |
|---|---|---|---|
| 0x00 | `LI` | Rd, Imm | Rd <- Imm |
| 0x01 | `ADDI` | Rd, Rs1, Imm | Rd <- Rs1 + Imm |
| 0x02 | `LOOP` | Rs1, Imm | Rs1 <- Rs1 - 1 ; branch to Imm if Rs1 != 0 |
| 0x03 | `M_LD_W` | Rs1 | load weight tile into array |
| 0x04 | `M_MUL` | Rd, Rs1 | run systolic matmul |
| 0x05 | `ACT` | Rs1 | ReLU activation |
| 0x06 | `STATUS` | Rd | Rd <- matrix-unit status |
| 0x07 | `HALT` | — | stop |
| 0x08 | `M_LD_A` | Rs1 | load activation tile |
| 0x09 | `M_ST` | Rs1 | store accumulator result |

Registers: `R0`–`R7`. The assembler resolves labels for `LOOP` targets in a two-pass scan.

---

## Repo structure

```
ai-core/
├── rtl/                     # shared core — identical across all apps
│   ├── cpu/                 # fetch, decode, execute, regfile
│   ├── pe/                  # INT8 processing element (DSP48E1)
│   ├── systolic_array/      # 4×4 weight-stationary array
│   ├── skew_buffer/         # input skew
│   ├── deskew_buffer/       # output de-skew
│   ├── mxu_controller/      # matrix-unit FSM
│   ├── mxu_integration/     # array + controller wiring
│   ├── accum_bank/          # INT32 accumulators
│   ├── requant/             # fixed-point ReLU + rescale
│   └── uart/                # uart_rx, uart_tx
├── assembler/               # shared toolchain
│   ├── assembler.py         # two-pass assembler -> .mem
│   ├── build_program.py     # interactive: layer pairs -> asm -> .mem
│   ├── convert_weights.py   # quantized .npy weights -> weights.mem
│   └── layer_gen.py         # layer-shape -> assembly codegen
├── apps/
│   ├── mnist/
│   │   ├── top/             # ai_core_top.sv, W/A/R mem, mnist.asm, program.mem
│   │   ├── argmax/          # 10-way streamed argmax
│   │   ├── seven_seg/
│   │   ├── golden_model/    # train_quantize.py, golden.py, w*.npy, b*.npy
│   │   ├── mnist_img_host/  # send_image.py (host sender)
│   │   ├── sim/             # cocotb testbench
│   │   ├── constrs_1/       # XDC constraints
│   │   └── build.tcl
│   └── lunarlander/
│       ├── top/             # ai_core_top.sv (3-layer, byte-packer), program.asm
│       ├── argmax/          # 4-way Q16 dequant comparator
│       ├── seven_seg/
│       ├── golden_model/    # train_quantize.py (PPO), golden.py, gui, fpga_demo, w*.npy
│       ├── sim/
│       ├── constrs_1/
│       └── build.tcl
├── LICENSE
└── README.md
```

*(build artifacts — `sim_build/`, `*.vcd`, `__pycache__/` — omitted)*

> Pre-generated `program.mem`, `weights.mem`, and `.npy` weights are committed in their app folders so you can flash and demo **without** running the toolchain. A full rebuild simply overwrites them.

---

## Quickstart

> Two-folder setup: `~/ai_core` (WSL — cocotb / Verilator / Python) and `C:\ai_core_vivado` (Windows — Vivado). Files are copied between them.

### 1. Generate memory files (WSL)

Program first (assemble), then weights (convert the trained `.npy`).

**MNIST**
```bash
# program.mem — assemble the hand-written program
python assembler/assembler.py apps/mnist/top/mnist.asm apps/mnist/top/program.mem

# weights.mem — trained INT8 weights (.npy in golden_model/) -> BRAM init
# NOTE: confirm the exact layer-pair string incl. bias augmentation for MNIST
python assembler/convert_weights.py 784,128;128,10 \
    apps/mnist/golden_model/w1.npy apps/mnist/golden_model/w2.npy \
    -o apps/mnist/top/weights.mem
```

**LunarLander** (layer pairs carry the folded bias row: 8+1, 128+1)
```bash
python assembler/assembler.py apps/lunarlander/top/program.asm apps/lunarlander/top/program.mem

python assembler/convert_weights.py 9,128;129,128;129,4 \
    apps/lunarlander/golden_model/w1.npy apps/lunarlander/golden_model/w2.npy apps/lunarlander/golden_model/w3.npy \
    -o apps/lunarlander/top/weights.mem
```

> Alternative to writing `.asm` by hand: `python assembler/build_program.py` generates the assembly from layer `(in,out)` pairs and assembles it in one step.
> The `.npy` weights come from the per-app training script (`golden_model/train_quantize.py`).

### 2. Simulate (WSL)

```bash
cd apps/mnist/sim && make          # MNIST — Verilator + cocotb
cd apps/lunarlander/sim && make    # LunarLander
```

### 3. Build the bitstream (Windows / Vivado)

```powershell
vivado -mode batch -source apps/mnist/build.tcl
vivado -mode batch -source apps/lunarlander/build.tcl
```

> Runs from PowerShell or cmd as long as `vivado` is on PATH. If not, use the **Vivado Tcl Shell** or call the full path to `vivado.bat`.

### 4. Run on hardware (Windows only)

Serial (COM ports) is Windows-side. Port and baud are **hardcoded in the host scripts** (`COM4`, 115200) — edit them there before running.

```powershell
# MNIST — send a test image over serial
python apps/mnist/mnist_img_host/send_image.py

# LunarLander — live hardware loop (sends observations, reads actions back over UART)
python apps/lunarlander/golden_model/fpga_demo.py
```

> `lunarlander_gui.py` is the **software reference** — it runs the NumPy golden model (`golden.forward`) with no board attached. Use it to sanity-check the policy, not to drive hardware.

---

## Per-module RTL breakdown

- **`pe.sv`** — single INT8×INT8->INT32 MAC with a stationary weight register; sign-extended accumulation. Inferred onto a DSP48E1.
- **`systolic_array.sv`** — 4×4 grid of PEs, diagonal activation skew (3N-2 = 10-cycle fill/drain).
- **`skew_buffer.sv` / `deskew_buffer.sv`** — align inputs into / outputs out of the array.
- **`mxu_controller.sv`** — FSM sequencing weight load, matmul, and accumulation; raises `matrix_done`.
- **`mxu_integration.sv`** — wires the array, controller, and buffers together.
- **`accum_bank.sv`** — INT32 accumulators, one per output column.
- **`requant.sv`** — fixed-point rescale + ReLU, clips INT32 -> INT8.
- **`cpu/`** — `fetch` / `decode` / `execute` / `regfile`; issues matrix commands and stalls on `M_MUL`.
- **`uart/`** — `uart_rx` (host -> board input), `uart_tx` (board -> host, LunarLander action return).
- **`apps/*/argmax/`** — per-app: MNIST streams 10 outputs with a running max; LunarLander is a single-shot 4-way comparator with per-channel Q16 dequant.

---

## License

See [LICENSE](LICENSE).