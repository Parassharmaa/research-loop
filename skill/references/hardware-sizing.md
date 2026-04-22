# Hardware sizing for HF Jobs

Pick the smallest flavor that fits. Over-provisioning wastes money; under-provisioning loses the whole run to OOM halfway through.

## Quick table (fine-tuning, bf16, LoRA or full)

| Model params | LoRA/QLoRA | Full FT | Notes |
|---|---|---|---|
| ≤ 1B | `t4-small` | `t4-medium` | t4 is Turing — no bf16, use fp16. |
| 1–3B | `l4x1` | `a10g-large` | l4 is great value. |
| 3–7B | `l4x1` / `a10g-large` | `a10g-largex2` | 7B full FT needs ≥ 48 GB VRAM in bf16. |
| 7–13B | `a10g-largex2` | `a100-largex1` | QLoRA fits 13B on one a10g. |
| 13–34B | `a100-largex1` | `a100-largex2` | Consider DeepSpeed ZeRO-3. |
| 34–70B | `a100-largex2` | `a100-largex4` | FSDP or ZeRO-3 mandatory. |
| 70B+ | `a100-largex4` | `a100x8` | Expect multi-day runs. |

## Timeouts

HF Jobs will kill your run at the timeout — no warning. Rule of thumb: request **2× your estimated wall-time**, minimum 2h. For runs > 24h, checkpoint every N steps and be ready to resume.

## Sandbox / dry-run flavors

| Purpose | Flavor |
|---|---|
| Config sanity check, 1–2 steps | `cpu-basic` |
| Small-model end-to-end | `t4-small` |
| Debugging distributed setup | `a10g-largex2` (2 GPUs, cheapest multi-GPU) |

## Cost / speed heuristics

- A `t4-small` is ~10× cheaper than `a100-largex1` and ~5× slower for training. For code shake-out, t4 wins on cost-per-debug-iteration.
- `l4x1` has bf16 and 24 GB VRAM at roughly half the price of `a10g-large`. For 1–7B QLoRA it's usually the sweet spot.
- `a100x8` is ~8× the hourly cost of `a100-largex1` but only ~6–7× the throughput for most workloads. Only scale out when the model actually needs it.

## Red flags in a user request

Push back before submitting if you see any of these:

- "Full fine-tune 70B on a single GPU" — won't fit.
- "Train for 10 epochs" on a 10M-example dataset — probably 100× what's needed; suggest `max_steps` instead.
- "Just run it on `a100x8` to be safe" — 8× cost for no benefit on most jobs.
- No `eval_strategy` set — you won't know if it's learning until it's done.
- No `save_steps` on a > 4h run — one crash and you lose everything.
