import numpy as np

w1 = np.load('w1.npy')   #layer 1 (784, 128) 
w2 = np.load('w2.npy')   #layer 2 (128, 10)  


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


#padded to 12 with zero columns since array works in group of 4
w2_padded = np.zeros((128, 12), dtype=np.int8)
w2_padded[:, :10] = w2

with open('../rtl/cpu/sim/weights.mem', 'w') as f:
    # Layer 1 addresses 0 to 6271
    write_layer(f, w1, n_input_tiles=196, n_output_groups=32)
    # Layer 2 -> addresses 6272 till 6367
    write_layer(f, w2_padded, n_input_tiles=32, n_output_groups=3)