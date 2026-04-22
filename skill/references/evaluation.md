# Evaluation — leakage-aware splits, benchmarks, uncertainty

Standard `train_test_split` is the wrong default for most real research problems. This reference collects the evaluation patterns the user actually employs, so the skill generates the right scaffolding up-front instead of retro-fitting it.

## Pick the right CV **before** training, not after

Ask the user (or infer from the data) which failure mode applies:

| Data has… | Random split leaks | Use instead |
|---|---|---|
| Spatial structure (geo, molecules, graphs) | ✗ | **LOBO** — leave-one-block-out (basin / cluster / chromosome) |
| Temporal structure (time series, logs) | ✗ | **Walk-forward** — train on past, eval on future |
| Grouped users / sessions | ✗ | **GroupKFold** on user_id |
| Domain shift (dataset A → B) | ✗ | **Leave-one-domain-out** |
| Long-range dependencies with gaps | ✗ | **Gapped evaluation** — insert input gaps at eval to stress long-context |
| Truly IID (rare!) | ✓ | Random k-fold is fine |

Default to a leakage-aware split. Only fall back to random if you can argue IID from first principles.

## Always name a benchmark

At the end of stage 1 (literature), record in `LEARNINGS.md`:

```
Benchmark: <Author, Year> — <metric> = <value> on <dataset>. We target
"match or beat <value> under <our stricter eval protocol>."
```

This is a forcing function. Without a benchmark, "it works" is meaningless.

Bonus: when you beat it, the paper writes itself. When you don't, the LEARNINGS log tells you why.

## Uncertainty quantification (when the deliverable is a decision)

If the model's output will inform a human decision (clinical, policy, safety, climate), a point estimate is insufficient. Add:

- **Conformal prediction** (`mapie`, `torchcp`) — distribution-free coverage guarantees.
- **Deep ensembles** — cheapest route to epistemic uncertainty.
- **MC Dropout** — if ensembles are too expensive, last resort.

Plan for this in stage 3, not stage 5. It dictates the model API.

## Explainability (when stakeholders are non-ML)

If the audience includes domain experts, policy folks, or product:

- **SHAP** — baseline. Per-feature attribution.
- **Integrated Gradients** — for deep models.
- **Counterfactual explanations** — "what would need to change for the prediction to flip."

Dedicate a numbered script (`07_explain.py`-style). Figures go in `paper/figures/`.

## Metadata per run

Every `runs/<timestamp>/` must have a `metadata.json` with at minimum:

```json
{
  "timestamp": "2026-04-22T14:03:00Z",
  "git_sha": "<short-hash>",
  "config_path": "configs/ablations/variant_c.yaml",
  "config_snapshot": { ... },           // full config, not just a path
  "seeds": [0, 1, 2, 3, 4],
  "provider": "runpod",
  "gpu": "H100:2",
  "wall_time_s": 4823,
  "env": {
    "python": "3.12.3",
    "torch": "2.5.1",
    "transformers": "4.48.0",
    "trl": "0.13.0",
    "cuda": "12.4"
  },
  "metrics": {
    "final": { "auc": 0.995, "auc_std": 0.004 },
    "per_split": { ... }
  },
  "notes": "LOBO CV across 12 basins. Ran on RunPod H100 SECURE."
}
```

The skill should generate this automatically at the end of any training script — not rely on the user to remember.

## Multi-seed is the default

Single-seed results are anecdotes. For any reportable result:

- **Minimum 3 seeds.** 5 is better. Report mean ± std.
- **Statistical test** when comparing variants (paired t-test, Wilcoxon, or bootstrapped CI). Log the test and p-value in LEARNINGS.
- Effect size (Cohen's d) beats p-value for meaningful comparison.

## Evaluation tooling (2026 stack)

Don't hand-roll eval loops. Use standardized harnesses — results compare cleanly with published numbers.

### Standardized benchmarks

- **`lm-eval-harness`** (EleutherAI) — the de facto standard for LLM evals. Covers MMLU, HellaSwag, GSM8K, HumanEval, ARC, TruthfulQA, BBH, and hundreds more.

  ```bash
  pip install lm-eval
  lm_eval --model vllm \
      --model_args pretrained=<org>/<model>,dtype=bfloat16,tensor_parallel_size=1 \
      --tasks mmlu,gsm8k,hellaswag \
      --batch_size auto \
      --output_path runs/<ts>/eval/
  ```

  Backing with **vLLM** instead of HF `generate` is ~20× faster on the same GPU. Use it unless the eval method requires log-prob scoring of many short completions (where HF direct is fine).

- **`olmes`** (AI2) — newer, better reproducibility discipline (explicit prompt variants, formatted metrics). Worth running alongside `lm-eval-harness` for headline results.

### LLM-as-judge

For open-ended tasks (chat quality, creativity, following nuanced instructions), there's no ground truth. Use a strong model as judge.

- **`trulens`** / **`openevals`** — structured LLM-as-judge with rubrics, confidence, consistency checks.
- **MT-Bench** + **AlpacaEval 2** — community-calibrated chat benchmarks; results compare to public leaderboards.

Guardrails for judge-based eval:

1. **Use a different model family for judge vs. subject.** GPT-4 judging a GPT-4-distilled model is contaminated.
2. **Randomize position.** Judge bias toward the first-presented answer is real; swap A/B halfway.
3. **Multiple judges, majority vote.** Single-judge numbers are noisy; 3 judges + majority ≈ human correlation.
4. **Publish the judge prompt** in your model card. Non-reproducible judges are not results.

### Contamination checks

Before publishing any benchmark number, verify the eval set didn't leak into training data:

- `datasets` + `datasketch` MinHash between training corpus and eval set.
- For chat models, check `LMSYS-1M` contamination specifically (very commonly leaks).
- Log the contamination check result in `LEARNINGS.md` — this is what reviewers will ask.

### Eval budget for a typical run

| Scope | Tasks | Wall-time (vLLM on 1 H100) |
|---|---|---|
| Smoke test | `gsm8k`, `hellaswag` | ~15 min |
| Standard chat eval | MMLU + GSM8K + HumanEval + MT-Bench + AlpacaEval | ~3 h |
| Thorough | Above + `bbh` + `arc_challenge` + `truthfulqa` + `ifeval` | ~8 h |

Budget eval into the training plan — it's often 10–30 % of the total GPU spend on a serious release.

## Stage 5 deliverables

When shipping:

1. `runs/<ts>/metadata.json` populated.
2. `LEARNINGS.md` entry linking to the run.
3. Paper figure regenerated via `scripts/NN_paper_figures.py` (not hand-edited).
4. If pushing to a Hub: model card includes eval protocol, benchmark, and LEARNINGS highlights.
5. Eval numbers in the paper source have **no placeholders** (`XX`, `TODO`, `???`). Grep for them before compile.
