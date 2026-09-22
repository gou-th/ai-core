import gymnasium as gym
import numpy as np
import serial
import time
import json
import argparse
import os

COM_PORT = "COM4"
BAUD_RATE = 115200

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), '..', 'golden_model')

with open(os.path.join(GOLDEN_DIR, 'scales.json')) as f:
    scales = json.load(f)
scale_obs = scales["scale_obs"]


def quantize_obs(obs_f32):
    """Must match golden.py's quantization"""
    return np.clip(np.round(obs_f32 / scale_obs), -128, 127).astype(np.int8)


def obs_to_bytes(obs_int8):
    """Pack 8 signed INT8 values into 8 raw bytes for UART."""
    return bytes([int(v) & 0xFF for v in obs_int8])


def get_action_from_fpga(ser, obs_f32):
    packet = obs_to_bytes(quantize_obs(obs_f32))
    ser.write(packet)
    response = ser.read(1)
    if len(response) == 0:
        raise TimeoutError("No response from FPGA")
    return response[0] & 0x03 


def main():
    parser = argparse.ArgumentParser(description="Watch the FPGA play LunarLander live.")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--port", default=COM_PORT)
    args = parser.parse_args()

    ser = serial.Serial(args.port, BAUD_RATE, timeout=1.0)
    time.sleep(2) 

    env = gym.make("LunarLander-v3", render_mode="human")

    try:
        for ep in range(args.episodes):
            obs, _ = env.reset()
            done = False
            total = 0
            while not done:
                action = get_action_from_fpga(ser, obs)
                obs, r, term, trunc, _ = env.step(action)
                total += r
                done = term or trunc
            print(f"Episode {ep}: reward={total:.1f}")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        env.close()
        ser.close()


if __name__ == "__main__":
    main()