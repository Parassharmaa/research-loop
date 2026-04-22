# Model merging — often cheaper than another training run

When you have two or more fine-tuned variants of the same base model and want to combine their capabilities without paying for more training: **merge them.** 2026's dirty secret is that a good merge often beats another training run.

## When to consider it

- You trained two variants (e.g. one on code, one on chat) and want both capabilities.
- A community has already fine-tuned strong variants and you want to combine them.
- You want to add a "personality" or domain flavor on top of a strong base without risking catastrophic forgetting from a new run.
- You're out of GPU budget but have usable checkpoints lying around.

## Tool: `mergekit`

```bash
pip install mergekit
```

Runs on CPU for models up to ~30B (slow but free). Uses `safetensors` streaming so it doesn't OOM.

### Minimal merge config

```yaml
# configs/merge/ties.yaml
merge_method: ties
base_model: meta-llama/Llama-3.1-8B
dtype: bfloat16
models:
  - model: user/llama-3.1-8b-code
    parameters:
      density: 0.5
      weight: 0.5
  - model: user/llama-3.1-8b-chat
    parameters:
      density: 0.5
      weight: 0.5
parameters:
  normalize: true
```

Run:

```bash
mergekit-yaml configs/merge/ties.yaml ./merged-model \
  --cuda --copy-tokenizer --allow-crimes
huggingface-cli upload user/llama-3.1-8b-merged ./merged-model
```

## Merge methods (picking one)

| Method | When to use |
|---|---|
| **SLERP** | Merging exactly 2 models. Spherical interpolation in weight space. Fast, usually works. |
| **TIES** | Merging 3+ models. Resolves sign conflicts between task vectors. The 2026 default. |
| **DARE** / **DARE-TIES** | TIES + random pruning of task vectors. Slightly better than TIES when merging many models. |
| **Linear** | Simple weighted average. Baseline; SLERP usually beats it. |
| **Passthrough** | Frankenmerge — stitch layers from different models into one taller model. Risky. |
| **Model stock** | Recent method; averages multiple SFT variants trained from the same base to reduce variance. |

## Hyperparameters worth tuning

- **`density`** (TIES/DARE) — fraction of parameters to keep from each task vector. 0.5 is a good default; tune 0.3–0.7.
- **`weight`** — per-model importance. If you care more about A than B, weight it higher but keep `normalize: true`.
- **`int8_mask`** (DARE) — enables INT8 Bernoulli mask, cuts memory.

## Evaluate merges with the same protocol as training

Merging can silently degrade the model's calibration or break instruction-following even when per-task benchmarks look fine. Always:

1. Run `lm-eval-harness` on the merged model with the same tasks you used to evaluate the sources.
2. Eyeball 30–50 generations against prompts from each source model's target domain.
3. Check MT-Bench / AlpacaEval for chat quality if a chat model is in the mix.

Log the merge config in `LEARNINGS.md` under a "merges" section. Include: base, source models with Hub revs, method, density, weights, eval deltas vs each source.

## Frankenmerge caveats (passthrough method)

Stitching layers from two models into a taller model (e.g. 8B → 11B) can work — Goliath-120B, SOLAR-10.7B — but:

- The resulting model has no pretraining signal for the new depth; quality is fragile.
- Usually needs a short continued-pretraining pass to re-stabilize.
- Don't do this unless you're willing to accept a 10–20 % chance the output is broken.

## Budget framing

A TIES merge of two 8B models on a CPU box takes ~20 minutes and $0. Even if it's 5 % behind a new training run, it might buy you 95 % of the gain at 0 % of the cost. **Always try a merge before scheduling another run.**
