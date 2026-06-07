import numpy as np
import tensorflow as tf

def quantize(weight_f32): 
    scale = (np.abs(weight_f32).max())/127
    weight_int8 = np.clip(np.round(weight_f32/scale), -128, 127).astype(np.int8)
    return weight_int8, scale

def load_weights():
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    x_train,x_test = x_train/255.0, x_test/255.0
    model = tf.keras.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(10),
    ])
    model.compile(optimizer='adam',
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=['accuracy'])
    model.fit(x_train, y_train, epochs=5)
    w1 = model.layers[1].get_weights()[0]
    w2 = model.layers[2].get_weights()[0]
    w1_int8, scale1 = quantize(w1)
    w2_int8, scale2 = quantize(w2)
    return w1_int8, scale1, w2_int8, scale2

def forward(image, w1_int8, scale1, w2_int8, scale2):
    image = image.flatten()
    image_int8,scale_img = quantize(image)
    layer1 = np.dot(image_int8.astype(np.int32), w1_int8.astype(np.int32))
    layer1 = np.clip(layer1*scale_img*scale1, 0, None)
    layer1_int8, scale_layer1 = quantize(layer1)
    layer2 = np.dot(layer1_int8.astype(np.int32), w2_int8.astype(np.int32))
    layer2 = layer2*scale_layer1*scale2
    return np.argmax(layer2)

if __name__ == "__main__":
    w1_int8,scale1,w2_int8,scale2 = load_weights()
    (_, _),(x_test, y_test) = tf.keras.datasets.mnist.load_data()
    x_test = x_test/255.0
    correct = 0
    for i in range(10):
        pred = forward(x_test[i],w1_int8,scale1,w2_int8,scale2)
        actual = y_test[i]
        print(f"Image {i}: predicted={pred}, actual={actual}")
        if pred == actual:
            correct += 1
print(f"\nAccuracy: {correct}/10")
    