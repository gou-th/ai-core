import numpy as np
import tensorflow as tf
import json

#load MNIST
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
x_train, x_test = x_train / 255.0, x_test / 255.0

#build and train
model = tf.keras.Sequential([
    tf.keras.layers.Flatten(input_shape=(28, 28)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(10),
])
model.compile(
    optimizer='adam',
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=['accuracy']
)
model.fit(x_train, y_train, epochs=5, verbose=1)
test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
print(f"\nFloat model test accuracy: {test_acc:.4f}")

#get the weights
w1_f32 = model.layers[1].get_weights()[0]  #(784,128)
b1_f32 = model.layers[1].get_weights()[1]  #(128,)
w2_f32 = model.layers[2].get_weights()[0]  #(128,10)
b2_f32 = model.layers[2].get_weights()[1]  #(10,)

#quantize INT8
def quantize(x_f32):
    scale = np.abs(x_f32).max() / 127
    x_int8 = np.clip(np.round(x_f32 / scale), -128, 127).astype(np.int8)
    return x_int8, scale
w1_int8, scale_w1 = quantize(w1_f32)
b1_int8, scale_b1 = quantize(b1_f32)
w2_int8, scale_w2 = quantize(w2_f32)
b2_int8, scale_b2 = quantize(b2_f32)

np.save('w1.npy', w1_int8)
np.save('b1.npy', b1_int8)
np.save('w2.npy', w2_int8)
np.save('b2.npy', b2_int8)

scales = {
    'scale_w1': float(scale_w1),
    'scale_b1': float(scale_b1),
    'scale_w2': float(scale_w2),
    'scale_b2': float(scale_b2)
}
with open('scales.json', 'w') as f:
    json.dump(scales, f, indent=2)

#test images and labels
np.save('test_images.npy', x_test[:20])
np.save('test_labels.npy', y_test[:20])
print(f"\nscale_w1 = {scale_w1:.6f}")
print(f"scale_w2 = {scale_w2:.6f}")