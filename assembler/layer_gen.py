def ceil4(n):
    return -(-n // 4)


def generate_dense_layer(input_dim, output_dim, weight_start_addr,
                          act_read_base, act_write_base, result_base,
                          layer_idx, apply_act=True):
    input_tiles = ceil4(input_dim)
    output_groups = ceil4(output_dim)
    OUTER = f"L{layer_idx}_OUTER"
    INNER = f"L{layer_idx}_INNER"

    asm = f"""
LI R1, {output_groups}
LI R3, {weight_start_addr}
LI R5, {act_write_base}
LI R6, {result_base}

{OUTER}:
LI R2, {input_tiles}
LI R4, {act_read_base}

{INNER}:
M_LD_W R3
M_LD_A R4
M_MUL R0, R0
ADDI R3, R3, 1
ADDI R4, R4, 1
LOOP R2, {INNER}
"""
    if apply_act:
        asm += "ACT R5\nADDI R5, R5, 1\n"
    asm += f"""
M_ST R6
ADDI R6, R6, 1
LOOP R1, {OUTER}
"""
    return asm


def generate_network(layer_pairs, weight_base=0, act_base=0, result_base=0):
    prog = ""
    weight_addr = weight_base
    act_read = act_base
    res_addr = result_base

    for i, (in_dim, out_dim) in enumerate(layer_pairs):
        is_last = (i == len(layer_pairs) - 1)
        act_write = act_read + ceil4(in_dim)

        prog += generate_dense_layer(
            input_dim=in_dim,
            output_dim=out_dim,
            weight_start_addr=weight_addr,
            act_read_base=act_read,
            act_write_base=act_write,
            result_base=res_addr,
            layer_idx=i,
            apply_act=not is_last,
        )

        weight_addr += ceil4(in_dim) * ceil4(out_dim)
        act_read = act_write
        res_addr += ceil4(out_dim)

    prog += "HALT\n"
    return prog