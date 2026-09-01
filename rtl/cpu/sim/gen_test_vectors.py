import numpy as np

W = np.array([
    [1, 2, 0, -1],
    [0, 1, 1,  2],
    [2, 0, 1,  1],
    [1, 1, 0,  1]], dtype=np.int8)
a = np.array([3, -1, -2, 4], dtype=np.int8)

with open('weights.mem', 'w') as f:
    flat = W.flatten()
    hex_str = ''.join(f'{int(b) & 0xFF:02X}' for b in reversed(flat))
    f.write(hex_str + '\n')

with open('images.mem', 'w') as f:
    hex_str = ''.join(f'{int(b) & 0xFF:02X}' for b in reversed(a))
    f.write(hex_str + '\n')

print("weights.mem:", open('weights.mem').read().strip())
print("images.mem:", open('images.mem').read().strip())
