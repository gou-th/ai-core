# build_program.py
import sys
from layer_gen import generate_network
from assembler import converter, assemble

def build(layer_dims, out_mem_path, weight_base=0, act_base=0, result_base=0, save_asm=True):
    asm_text = generate_network(layer_dims, weight_base, act_base, result_base)

    if save_asm:
        asm_path = out_mem_path.rsplit('.', 1)[0] + ".asm"
        with open(asm_path, 'w') as f:
            f.write(asm_text)
        print(f"Wrote {asm_path}")

    labels = {}
    instructions = []
    addr = 0
    for line_num, line in enumerate(asm_text.splitlines(), 1):
        token = converter(line)
        if not token:
            continue
        if token[0].endswith(':'):
            labels[token[0][:-1]] = addr
            if len(token) > 1:
                instructions.append((line_num, token[1:]))
                addr += 1
        else:
            instructions.append((line_num, token))
            addr += 1

    with open(out_mem_path, 'w') as fout:
        fout.write("@0000\n")
        for line_num, token in instructions:
            code = assemble(token, line_num, labels)
            if code:
                fout.write(code + '\n')
            else:
                print(f"FAILED at line {line_num}. Aborting, .mem not written correctly")
                sys.exit(1)

    print(f"Wrote {out_mem_path}, {len(instructions)} instructions")

if __name__ == "__main__":
    dims_str = input("Layer dims, comma separated (e.g. 784,128,10): ")
    layer_dims = [int(x.strip()) for x in dims_str.split(',')]
    out_path = input("Output .mem path [like program.mem]: ").strip() or "program.mem"
    build(layer_dims, out_path)nah 