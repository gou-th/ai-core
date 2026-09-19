import numpy as np
import json
import gymnasium as gym

w1 = np.load('w1.npy').astype(np.int32)  #(9,128)
w2 = np.load('w2.npy').astype(np.int32)  #(129,128)
w3 = np.load('w3.npy').astype(np.int32)  #(129,4)

with open('scales.json') as f:
    scales = json.load(f)
scale_obs = scales['scale_obs']
M = scales['M']
S = scales['S']

CONST_INPUT = 127

def tile_matmul(act_4, weight_4x4):
    act = act_4.astype(np.int32)
    w = weight_4x4.astype(np.int32)
    psum = np.zeros(4, dtype=np.int32)
    for out_idx in range(4):
        psum[out_idx] = np.dot(act, w[:, out_idx])
    return psum

def requant(acc):
    #mirrors hardware's requant module exactly: negative clips to 0 (ReLU), then (acc*M)>>S, then clip to 127
    scaled = np.where(acc < 0, 0, acc.astype(np.int64) * M) >> S
    return np.clip(scaled, 0, 127).astype(np.int32)

def forward(obs_f32):
    obs_int8 = np.clip(np.round(obs_f32 / scale_obs), -128, 127).astype(np.int32)
    obs_int8_aug = np.append(obs_int8, CONST_INPUT)

    layer1_acc = np.dot(obs_int8_aug, w1)
    layer1_int8 = requant(layer1_acc)
    layer1_int8_aug = np.append(layer1_int8, CONST_INPUT)

    layer2_acc = np.dot(layer1_int8_aug, w2)
    layer2_int8 = requant(layer2_acc)
    layer2_int8_aug = np.append(layer2_int8, CONST_INPUT)

    layer3_acc = np.dot(layer2_int8_aug, w3)
    return int(np.argmax(layer3_acc))  


if __name__ == "__main__":
    test_obs = np.load('test_observations.npy')
    test_actions = np.load('test_actions.npy')
    correct = 0
    n = len(test_obs)
    for i in range(n):
        pred = forward(test_obs[i])
        actual = int(test_actions[i])
        if pred == actual:
            correct += 1
    print(f"Offline agreement: {correct}/{n} ({100*correct/n:.1f}%)")

    env = gym.make("LunarLander-v3")
    rewards = []
    for ep in range(20):
        obs, _ = env.reset()
        done = False
        total = 0
        while not done:
            action = forward(obs)
            obs, r, term, trunc, _ = env.step(action)
            total += r
            done = term or trunc
        rewards.append(total)
        print(f"Episode {ep}: reward={total:.1f}")

    print(f"\nMean INT8 reward over 20 episodes: {np.mean(rewards):.1f}")