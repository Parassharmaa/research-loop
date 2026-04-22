# Example session — reproduce DPO on UltraFeedback

A walkthrough of what the `research-loop` skill does on a concrete task.

**User:** "Reproduce the DPO paper on UltraFeedback with llama-3.2-1b as the base."

## Stage 1 — literature

Skill spawns `Agent(subagent_type: "Explore")` with the paper-to-recipe
template. Sub-agent returns:

| Paper | Dataset | Base model | LR | Effective BS | Steps | Hardware |
|---|---|---|---|---|---|---|
| Rafailov 2023 (DPO) | Anthropic HH | Pythia 2.8B / 6.9B | 1e-6 | 64 | 1 epoch | 8× A100 |
| Tunstall 2023 (Zephyr) | UltraFeedback binarized | Mistral-7B-SFT | 5e-7 | 32 | 3 epochs | 16× A100 |

Reference implementation: `huggingface/trl` — `examples/scripts/dpo.py`,
trl ≥ 0.11. Key gotcha from issues: `beta=0.1` works for most setups;
0.5 from the original paper overfits on UltraFeedback.

## Stage 2 — validation

- `HuggingFaceH4/ultrafeedback_binarized` — 61 k train rows, columns
  `chosen` / `rejected` (list of chat messages) + `score_chosen` / `score_rejected`.
- Token lengths with llama-3.2 tokenizer: p50=310, p95=820, max=2048.
- `max_length=1024` covers p95 — safe default.

## Stage 3 — sandbox

100-row slice, 2 steps on `t4-small`. Loss drops from 0.69 → 0.64. Logs
show `reward/margins` is positive. Config sane.

## Stage 4 — approval ask

Skill posts the template from `references/approval-template.md`:

> Flavor: `a10g-largex2` (2× A10G, 24 GB each)
> Effective BS: 2 × 2 × 8 accum = 32
> LR: 5e-7 cosine, warmup 0.1
> max_steps: 1500 (≈ 1 epoch over 48k filtered rows)
> push_to_hub: `Parassharmaa/llama-3.2-1b-dpo-ultrafeedback`
> Timeout: 4h (expected wall-time ~1.5h)
> Estimated cost: ~$3.50
> **Reply `go` to submit.**

User replies `go`.

## Stage 5 — ship

Skill submits via HF MCP, polls logs every 60s, posts back on completion
with eval metrics (MT-Bench, AlpacaEval 2). Generates model card,
confirms checkpoint is live at the pushed repo.

---

Total GPU spend: ~$3.50. Total wall-clock for Claude: ~15 min of
literature + validation + approval, then monitoring.
