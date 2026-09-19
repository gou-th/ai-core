import gymnasium as gym
import numpy as np
import serial
import time
import json

# ── config ──
COM_PORT = "COM4"      
BAUD_RATE = 115200    

# load the same scale used during quantization
with open("scales.json") as f:
    scales = json.load(f)
scale_obs = scales["scale_obs"]

def quantize_obs(obs_f32):
    """Same quantization as golden.py — must match exactly or hardware
    and host disagree on what the bytes mean."""
    return np.clip(np.round(obs_f32 / scale_obs), -128, 127).astype(np.int8)

def obs_to_bytes(obs_int8):
    """Pack 8 signed INT8 values into 8 raw bytes for UART transmission.
    Two's complement encoding matches what the FPGA's byte-packer expects."""
    return bytes([int(v) & 0xFF for v in obs_int8])

def get_action_from_fpga(ser, obs_f32):
    obs_int8 = quantize_obs(obs_f32)
    packet = obs_to_bytes(obs_int8)
    ser.write(packet)

    # wait for the 1-byte action response
    response = ser.read(1)
    if len(response) == 0:
        raise TimeoutError("No response from FPGA")
    action = response[0] & 0x03  # only 2 bits matter (0-3)
    return action


def main():
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1.0)
    time.sleep(2) 

    env = gym.make("LunarLander-v3", render_mode="human")

    for ep in range(5):
        obs, _ = env.reset()
        done = False
        total = 0
        while not done:
            action = get_action_from_fpga(ser, obs)
            obs, r, term, trunc, _ = env.step(action)
            total += r
            done = term or trunc
        print(f"Episode {ep}: reward={total:.1f}")

    env.close()
    ser.close()


if __name__ == "__main__":
    main()