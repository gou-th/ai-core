import serial
import numpy as np
import time
import matplotlib.pyplot as plt
import os

SERIAL_PORT = 'COM4'          # check Device Manager for the Basys 3's COM port
BAUD_RATE = 115200

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), '..', 'golden_model')


def quantize(img_f32):
    "Same as the RTL/testbench: pixels 0.0-1.0 -> INT8 0-127."
    return np.clip(np.round(img_f32.flatten() * 127), 0, 127).astype(np.uint8)


def send_image(ser, img_f32):
    payload = quantize(img_f32)
    assert len(payload) == 784, f"expected 784 bytes, got {len(payload)}"
    ser.write(payload.tobytes())
    ser.flush()


def show_image(img_f32, label=None, predicted=None):
    plt.imshow(img_f32.reshape(28, 28), cmap='gray')
    title = f"label={label}" if label is not None else "sent image"
    if predicted is not None:
        title += f"  |  board says: {predicted}"
    plt.title(title)
    plt.axis('off')
    plt.show(block=False)
    plt.pause(0.1)


def main():
    images = np.load(os.path.join(GOLDEN_DIR, 'test_images.npy'))
    labels = np.load(os.path.join(GOLDEN_DIR, 'test_labels.npy'))

    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)   # let the FTDI chip settle after opening the port

    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
    print(f"{len(images)} test images loaded.\n")

    idx = 0
    while True:
        cmd = input(f"[image {idx}, label={labels[idx]}] "
                    "Enter=send, n=next, q=quit, or type an index: ").strip()

        if cmd.lower() == 'q':
            break
        elif cmd.lower() == 'n':
            idx = (idx + 1) % len(images)
            continue
        elif cmd.isdigit():
            idx = int(cmd) % len(images)
            continue

        show_image(images[idx], label=labels[idx])
        send_image(ser, images[idx])
        print(f"Sent image {idx} (label {labels[idx]}). "
              "Check the 7-segment display on the board.\n")

        idx = (idx + 1) % len(images)

    ser.close()
    print("Disconnected.")


if __name__ == "__main__":
    main()