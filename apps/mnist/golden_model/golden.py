import numpy as np
import json

#load weights 
w1 = np.load('w1.npy').astype(np.int32)  #(784, 128)
b1 = np.load('b1.npy').astype(np.int32)  #(128,)
w2 = np.load('w2.npy').astype(np.int32)  #(128, 10)
b2 = np.load('b2.npy').astype(np.int32)  #(10,)

#load scales
with open('scales.json') as f:
    scales = json.load(f)
scale_w1 = scales['scale_w1']
scale_w2 = scales['scale_w2']
scale_img = 1.0/127  #quantized to +-127

'''Mimics one 4x4 systolic array tile.
act_4: (4,) INT8/INT32 activations
weight_4x4: (4,4) INT8 weights
returns: (4,) INT32 partial sums '''
def tile_matmul(act_4: np.ndarray, weight_4x4: np.ndarray) -> np.ndarray:
    act = act_4.astype(np.int32)
    w = weight_4x4.astype(np.int32)
    psum = np.zeros(4, dtype=np.int32)
    for out_idx in range(4):
        psum[out_idx] = np.dot(act, w[:, out_idx])
    return psum

'''Integer forward pass
image_f32: (28,28) or (784,), float 0.0-1.0
returns: predicted digit 0-9'''
def forward(image_f32):
    image_flat = image_f32.flatten()
    image_int8 = np.clip(np.round(image_flat * 127), 0, 127).astype(np.int32)

    # Layer 1: (784,) x (784,128) to (128,) INT32, requant & ReLU to INT8
    layer1_acc = np.dot(image_int8, w1) + b1  # INT32 with bias
    layer1_req = (layer1_acc * scale_img * scale_w1)
    layer1_int8 = np.clip(np.round(layer1_req), 0, 127).astype(np.int32)
    # Layer 2: (128,) x (128,10) to (10,) INT32 (final layer)
    layer2_logits = np.dot(layer1_int8, w2) + b2
    return int(np.argmax(layer2_logits))
if __name__ == "__main__":
    test_images = np.load('test_images.npy')
    test_labels = np.load('test_labels.npy')
    correct = 0
    n = len(test_images)
    for i in range(n):
        pred = forward(test_images[i])
        actual = int(test_labels[i])
        print(f"Image {i}: pred={pred}, actual={actual}")
        if pred == actual:
            correct += 1
    print(f"\nAccuracy: {correct}/{n} ({100*correct/n:.1f}%)")