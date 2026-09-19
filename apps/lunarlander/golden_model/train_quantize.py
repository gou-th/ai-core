import numpy as np
import gymnasium as gym
from stable_baselines3 import PPO
import torch
import json
import os

os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"

env = gym.make("LunarLander-v3")
model = PPO(
    "MlpPolicy",
    env,
    policy_kwargs=dict(net_arch=[128, 128], activation_fn=torch.nn.ReLU),
    verbose=1,
    device="cpu",
)
model.learn(total_timesteps=300_000)

eval_env = gym.make("LunarLander-v3")
rewards = []
for _ in range(20):
    obs, _ = eval_env.reset()
    done = False
    total = 0
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, r, term, trunc, _ = eval_env.step(action)
        total += r
        done = term or trunc
    rewards.append(total)
print(f"Mean eval reward over 20 episodes: {np.mean(rewards):.1f}")

policy_net = model.policy.mlp_extractor.policy_net
action_net = model.policy.action_net
linear1 = policy_net[0]
linear2 = policy_net[2]
linear3 = action_net

w1_f32 = linear1.weight.detach().numpy().T
b1_f32 = linear1.bias.detach().numpy()
w2_f32 = linear2.weight.detach().numpy().T
b2_f32 = linear2.bias.detach().numpy()
w3_f32 = linear3.weight.detach().numpy().T
b3_f32 = linear3.bias.detach().numpy()

def quantize(x_f32):
    scale = np.abs(x_f32).max() / 127
    x_int8 = np.clip(np.round(x_f32 / scale), -128, 127).astype(np.int8)
    return x_int8, scale

def quantize_at_scale(x_f32, scale):
    x_int8 = np.clip(np.round(x_f32 / scale), -128, 127).astype(np.int8)
    clip_pct = 100 * np.mean(np.abs(x_f32 / scale) > 127)
    return x_int8, clip_pct

def append_bias_row(w_f32, b_f32, scale_input):
    bias_row = (b_f32 * scale_input).reshape(1, -1)
    return np.concatenate([w_f32, bias_row], axis=0)

obs_low = env.observation_space.low
obs_high = env.observation_space.high
scale_obs = np.max(np.maximum(np.abs(obs_low), np.abs(obs_high))) / 127.0

w1_with_bias = append_bias_row(w1_f32, b1_f32, scale_obs)  #(9,128)
w1_int8, scale_w1 = quantize(w1_with_bias)
np.save('w1.npy', w1_int8)

test_obs, test_actions = [], []
obs, _ = eval_env.reset()
for _ in range(200):
    action, _ = model.predict(obs, deterministic=True)
    test_obs.append(obs.copy())
    test_actions.append(int(action))
    obs, _, term, trunc, _ = eval_env.step(action)
    if term or trunc:
        obs, _ = eval_env.reset()
test_obs = np.array(test_obs, dtype=np.float32)
test_actions = np.array(test_actions, dtype=np.int32)
np.save('test_observations.npy', test_obs)
np.save('test_actions.npy', test_actions)

sample_obs = []
obs, _ = eval_env.reset()
for _ in range(500):
    action, _ = model.predict(obs, deterministic=True)
    sample_obs.append(obs.copy())
    obs, _, term, trunc, _ = eval_env.step(action)
    if term or trunc:
        obs, _ = eval_env.reset()
fit_obs = np.concatenate([np.array(sample_obs), test_obs], axis=0)

fit_int8 = np.clip(np.round(fit_obs / scale_obs), -128, 127).astype(np.int32)
const_col = np.full((fit_int8.shape[0], 1), 127, dtype=np.int32)
fit_int8_aug = np.concatenate([fit_int8, const_col], axis=1)

acc1 = fit_int8_aug @ w1_int8.astype(np.int32)
real1 = acc1.astype(np.float64) * scale_obs * scale_w1
scale_act = np.maximum(real1, 0).max() / 127.0

#hardware has ONE requant unit (fixed M,S) shared by both layer boundaries so deriving scale_w2 (instead of computing it from w2's own range) so that
#ratio1 = ratio2 exactly: scale_w2 = scale_obs*scale_w1/scale_act
scale_w2 = scale_obs * scale_w1 / scale_act
w2_with_bias = append_bias_row(w2_f32, b2_f32, scale_act)  #(129,128)
w2_int8, w2_clip_pct = quantize_at_scale(w2_with_bias, scale_w2)
print(f"w2 clipped at derived scale: {w2_clip_pct:.2f}%")
np.save('w2.npy', w2_int8)

layer1_int8_fit = np.clip(np.round(acc1 * (scale_obs * scale_w1) / scale_act), 0, 127).astype(np.int32)

with torch.no_grad():
    float_layer1 = linear1(torch.tensor(fit_obs, dtype=torch.float32))
    float_layer1_relu = torch.relu(float_layer1).numpy()
nonzero_match = np.mean((layer1_int8_fit > 0) == (float_layer1_relu > 0))
print(f"Layer1 ReLU sign agreement: {nonzero_match*100:.1f}%")

#final layer - no requant needed, argmax is scale-invariant, quantize normally
w3_with_bias = append_bias_row(w3_f32, b3_f32, scale_act)  #(129,4)
w3_int8, scale_w3 = quantize(w3_with_bias)
np.save('w3.npy', w3_int8)

S = 24
M = int(round(scale_w2 * (1 << S)))

scales = {
    'scale_obs': float(scale_obs),
    'scale_act': float(scale_act),
    'scale_w1': float(scale_w1),
    'scale_w2': float(scale_w2),
    'scale_w3': float(scale_w3),
    'M': M,
    'S': S,
}
with open('scales.json', 'w') as f:
    json.dump(scales, f, indent=2)

print(f"scale_obs={scale_obs:.6f}  scale_w1={scale_w1:.6f}  scale_w2={scale_w2:.6f}  scale_w3={scale_w3:.6f}")
print(f"M={M}  S={S}")