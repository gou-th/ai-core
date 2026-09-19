import sys
import numpy as np

def ceil4(n):
    return -(-n // 4)

def tile_to_hex(tile):
    flat = tile.flatten()
    bytes_msb = reversed(flat)
    return ''.join(f'{int(b) & 0xFF:02X}' for b in bytes_msb)

def write_layer(f, weights, n_input_tiles, n_output_groups):
    for output_group in range(n_output_groups):
        for input_tile in range(n_input_tiles):
            rows = slice(input_tile * 4, input_tile * 4 + 4)
            cols = slice(output_group * 4, output_group * 4 + 4)
            f.write(tile_to_hex(weights[rows, cols]) + '\n')

def pad_weights(w, in_dim, out_dim):
    padded = np.zeros((ceil4(in_dim) * 4, ceil4(out_dim) * 4), dtype=np.int8)
    padded[:in_dim, :out_dim] = w
    return padded

def generate_weights_mem(layer_pairs, weight_arrays, out_path):
    assert len(weight_arrays) == len(layer_pairs)
    with open(out_path, 'w') as f:
        for i, (in_dim, out_dim) in enumerate(layer_pairs):
            w = weight_arrays[i]
            assert w.shape == (in_dim, out_dim), \
                f"layer {i}: expected ({in_dim},{out_dim}), got {w.shape}"
            w_padded = pad_weights(w, in_dim, out_dim)
            write_layer(f, w_padded, ceil4(in_dim), ceil4(out_dim))
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert_weights.py 9,128;129,128;129,4 w1.npy w2.npy w3.npy -o weights.mem")
        sys.exit(1)

    layer_pairs = []
    for pair in sys.argv[1].split(';'):
        in_dim, out_dim = pair.split(',')
        layer_pairs.append((int(in_dim), int(out_dim)))
    n_layers = len(layer_pairs)

    npy_paths = sys.argv[2:2 + n_layers]
    if len(npy_paths) != n_layers:
        print(f"Need {n_layers} .npy files for {n_layers} layer(s)")
        sys.exit(1)

    out_path = "weights.mem"
    if "-o" in sys.argv:
        out_path = sys.argv[sys.argv.index("-o") + 1]

    weight_arrays = [np.load(p) for p in npy_paths]
    generate_weights_mem(layer_pairs, weight_arrays, out_path)