# Post-training methods — decision tree

In 2026 there are many alignment methods and they look similar on paper. Picking the wrong one burns a run. Walk this tree before stage 2.

## Start: what do you have?

```
Do you have an existing supervised dataset of (input, good-output) pairs?
├── No  → go to "Supervised data creation" below.
└── Yes → what's the next step?
    │
    ├── Nothing aligned yet → SFT first.
    ├── Have SFT model, want preference alignment → what kind of preference data?
    │   ├── Binary pairwise (chosen / rejected) → DPO, IPO, or SimPO.
    │   ├── Scalar ratings (1–5 stars, scores) → KTO.
    │   ├── No preference pairs yet, only prompts + a verifiable reward → GRPO / RLHF-PPO.
    │   └── Single-preference (one good, don't want another "rejected") → ORPO (merges SFT + DPO in one step).
    └── Have SFT + DPO model, want reasoning → GRPO with verifiable rewards (math, code, format).
```

## Method-by-method

### SFT — Supervised Fine-Tuning
- **Use when:** you have `(input, good-output)` pairs. Baseline before any preference method.
- **`trl`:** `SFTTrainer`.
- **Gotchas:** chat template must match inference-time template exactly. Mask the prompt tokens for loss (default in `SFTTrainer` with `packing=False` + `response_template=`).
- **Data budget:** 1k–100k examples. Diminishing returns above 100k for most tasks.

### DPO — Direct Preference Optimization
- **Use when:** you have binary `(prompt, chosen, rejected)` pairs.
- **`trl`:** `DPOTrainer`.
- **Hyperparams:** `beta ≈ 0.1` (0.05–0.3). LR `5e-7` to `5e-6` — much lower than SFT. 1 epoch usually.
- **Gotcha:** tokenize chosen + rejected with the same chat template used at inference.

### IPO — Identity Preference Optimization
- **Use when:** DPO overfits (train reward margins blow up, eval regresses).
- **Trade-off:** less aggressive; smoother convergence.

### SimPO — Simple Preference Optimization
- **Use when:** you want DPO quality without a reference model (half the memory).
- **2026 default** for many teams. Pair with length normalization.

### KTO — Kahneman-Tversky Optimization
- **Use when:** you have scalar "desirable / undesirable" labels, not pairs.
- **Data efficiency:** works with ~1:10 good-to-bad imbalance.

### ORPO — Odds Ratio Preference Optimization
- **Use when:** you want a single-stage alternative to SFT → DPO.
- **Effect:** merges SFT and preference loss. Faster pipeline, slightly worse peak quality than SFT + DPO.

### GRPO — Group Relative Policy Optimization
- **Use when:** you have prompts + a **verifiable reward function** (unit-test pass, regex match, math-grader, format-checker). No preference pairs needed.
- **This is the DeepSeek R1 method** — the 2026 reasoning-training story.
- **`trl`:** `GRPOTrainer` (≥ 0.13).
- **Hyperparams:** `num_generations ≈ 8–16` per prompt, `beta ≈ 0.04`, LR `1e-6`. Needs much more compute than DPO because of per-prompt sampling.
- **Scales to:** math (GSM8K, MATH), code (HumanEval), formatted output.

### PPO — the classic RLHF
- **Use when:** you need a trained reward model (not verifiable rewards). Legacy path.
- **Generally replaced by DPO/GRPO** unless you have a specific reason.

## Full pipeline templates

### "Align a chat model" (generic)

```
1. SFT on instruction data                    (1–2 epochs, LR 2e-5)
2. DPO or SimPO on preference data             (1 epoch, LR 5e-7, beta 0.1)
3. [optional] GRPO on verifiable-reward tasks  (reasoning / format)
```

### "Teach reasoning" (R1-style)

```
1. Cold-start SFT on a few thousand CoT traces from a strong teacher
2. GRPO with verifiable rewards (math / code / format)
3. [optional] Rejection sampling → SFT on only the best GRPO rollouts
4. [optional] Another DPO pass to match preferences
```

### "Domain-adapt a base model"

```
1. Continued pretraining on the domain corpus  (if > 100M tokens)
2. SFT on domain-specific (input, output)
3. DPO on preference data from domain experts
```

## Supervised data creation (when you have none)

If you got "No" at the first branch:

1. **Distill from a strong teacher.** Use `distilabel` or a scripted loop with GPT-4.x / Claude / a strong OSS model to generate `(prompt, good-output)` pairs. Filter aggressively.
2. **Magpie-style self-distillation.** Prompt the base model with just its chat template's `user` turn — it will hallucinate a prompt. Then complete it. Cheap, surprisingly effective.
3. **Synthetic preference data.** Teacher model labels pairs of outputs from weaker models as chosen/rejected. Cheaper than human labels, ~85 % of the quality for most tasks.
4. **Public datasets.** Start here: UltraFeedback, HH-RLHF, OpenHermes, tulu-3. Not a substitute for task-specific data, but a strong base.

See `synthetic-data.md` for tooling.

## Picking `beta` (DPO / SimPO / GRPO) — the knob everyone misses

- `beta` too low → model ignores the reference, collapses toward whatever the preference data encodes (often length or repetition).
- `beta` too high → model barely moves, you wasted the run.
- **Start at 0.1 for DPO, 0.04 for GRPO**, log `reward/margins` and `kl` every step. If `kl` is < 0.01 after 100 steps, lower beta. If `kl` is > 5, raise it.

## Red flags to catch in sandbox (stage 3)

- DPO `reward/margins` stays ~0 → tokenizer mismatch between chosen and rejected.
- Loss goes to NaN → learning rate too high, or `bf16` instability on Turing.
- GRPO `reward` stays at baseline → verifiable reward function has a bug. Print 3 sample outputs + reward scores and check manually.
- Training loss decreasing but eval regressing → length hacking; add length penalty or switch to IPO/SimPO.
