import gymnasium as gym
import numpy as np
import sys
sys.path.insert(0, '.') 
from golden import forward

env = gym.make("LunarLander-v3", render_mode="human")
obs, _ = env.reset()
done = False
total = 0
while not done:
    action = forward(obs)
    obs, r, term, trunc, _ = env.step(action)
    total += r
    done = term or trunc
env.close()
print(f"Reward: {total:.1f}")