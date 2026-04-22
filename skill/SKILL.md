---
name: research-loop
description: "USE THIS SKILL whenever the user wants to train, fine-tune, post-train (SFT, DPO, GRPO, ORPO, KTO, SimPO, LoRA, QLoRA, DoRA), pretrain, reproduce a paper, benchmark models, generate synthetic data, merge models, or serve a trained model. Provider-agnostic across Hugging Face Jobs, RunPod, Modal, Lambda, CoreWeave, Together, and local GPUs. Enforces a five-stage loop — literature → validate → sandbox → approval → ship — plus project scaffolding (numbered scripts, configs/, runs/, LEARNINGS.md) and leakage-aware evaluation so GPU hours aren't burned on preventable bugs."
when_to_use: 'Trigger on any ML training, fine-tuning, post-training, pretraining, evaluation, synthetic-data, model-merging, or model-serving request. Keywords: "train", "fine-tune", "pretrain", "reproduce this paper", "SFT", "DPO", "GRPO", "ORPO", "KTO", "SimPO", "LoRA", "QLoRA", "DoRA", "benchmark", "push to the Hub", "run this on RunPod / Modal / HF Jobs / Lambda", "synthetic data", "distilabel", "mergekit", "serve this model", "vLLM", "TGI". Invoke proactively the moment GPUs or training frameworks are mentioned — do not wait for the user to ask for the skill by name.'
argument-hint: "[paper-or-task] [dataset?] [base-model?] [provider?]"
allowed-tools: Read Write Edit Glob Grep Bash Agent WebFetch WebSearch
---

# research-loop

An opinionated ML-engineering workflow for Claude Code. The name is literal — you **loop between literature and code** before ever touching a GPU.

This skill is **provider-agnostic**. Pick the GPU backend that fits the job:

- **Hugging Face Jobs** — cheapest CPU dry-runs, tight Hub integration, hosted sandbox, no infra to manage.
- **RunPod** — lowest per-hour cost, pods or serverless, exposes a real MCP server.
- **Modal** — best DX if you hate YAML and want `@app.function(gpu=...)` decorators.
- **Lambda / CoreWeave / Together** — bare-metal or managed H100/H200 at transparent pricing.
- **Local** — fastest feedback for < 7B models with a capable local GPU.

The skill doesn't force a choice. Ask the user, or infer from context (existing `modal.toml`, `runpod.yaml`, HF token in env, etc.), and route to the matching provider reference.

See `references/providers/` for per-provider setup, tool surface, and submit commands.

## The five stages

You MUST execute these in order. Skipping a stage is the single biggest cause of wasted GPU hours.

### 1. Literature pass (BEFORE any code)

Spawn a research sub-agent via `Agent(subagent_type: "Explore")` with a focused brief. Template in `references/research-subagent.md`. In short: extract exact datasets, hyperparameters, and hardware from sections 3–5 of the 2–3 landmark papers, plus one canonical reference implementation.

**Do not write training code until this table exists.** If the user pushes back, explain that a 10-minute literature pass prevents a 6-hour failed run.

### 2. Dataset + tokenizer validation

Before writing the trainer:
- Inspect the dataset — row count, columns, token-length p50/p95/max, label distribution. Use HF MCP if the dataset is on the Hub; otherwise a small Python script in Bash.
- Load the tokenizer and tokenize 10 random rows. Catch: truncation at the wrong length, missing BOS/EOS, chat-template mismatch.
- If preprocessing is needed, write it as a standalone script and verify output before moving on.

### 3. Sandbox-first training

Write the training script. Run it **on CPU or a single small GPU against a 100-row slice**, for 1–2 steps, before touching real hardware. This catches ~80% of config errors at near-zero cost.

Sandbox options, in order of preference:

1. **Local Python + tiny model** (e.g. `sshleifer/tiny-gpt2`) — fastest iteration, zero cost.
2. **HF Jobs `cpu-basic`** or **RunPod CPU pod** — if local can't fit the data pipeline.
3. **Cheapest GPU on chosen provider** (`t4-small` on HF, RTX 4090 on RunPod, `T4` on Modal) — last resort before the real run.

The script must: load model, load dataset slice, run 1–2 optimizer steps, print loss, save a checkpoint. If any of those fail, fix them here, not in the full run.

### 4. Full training submission (approval gate)

Only now, submit the real job. **ALWAYS stop and confirm with the user before launching a GPU run.** Show them the full config using the template in `references/approval-template.md`.

Pick the provider-specific submit command from `references/providers/<provider>.md`. Common fields across providers:
- Script + entrypoint
- GPU flavor + count + timeout
- Dataset + base model + effective batch size
- Output destination (`push_to_hub`, S3 bucket, Modal volume, etc.)
- Estimated cost

See `references/hardware-sizing.md` for cross-provider GPU selection.

### 5. Ship

- Monitor via the provider's log/status tool. Do not poll faster than once per minute.
- On completion: verify checkpoint uploaded, write a model card, run eval, post metrics back to the user.
- If the run failed: read logs, diagnose, loop back to stage 3. **Do not** immediately resubmit with a "creative" workaround.

## Guardrails (non-negotiable)

- **No scope-changing fixes.** When you hit OOM or a tokenizer error, do not silently switch to a smaller model, shorter context, or different dataset to make the error go away. Report the constraint, propose options, let the user decide.
- **No bare `rm`, no force-push, no destructive Hub ops without explicit confirmation.** Destructive = deleting a repo/branch, overwriting an existing file on `main`, terminating a running pod with unsaved checkpoints.
- **Approval required for:** any paid GPU submission, any CPU run > 30 min, any `push_to_hub` to a repo you didn't create this session, any dataset deletion or mass upload, any `modal run` against a non-sandbox app.
- **One task in-progress at a time.** Use `TaskCreate` to track stages. Mark completed the moment a stage is done.

## Anti-patterns (stop if you notice yourself doing these)

- Writing the training loop before the literature table exists.
- Submitting to GPU without a sandbox dry-run.
- Re-submitting a failed job more than once without a root-cause hypothesis.
- Asking the user to approve the same GPU job twice with minor tweaks — batch fixes, then re-request.
- Increasing `max_steps` "just in case."
- Using `trust_remote_code=True` without checking what the code does.
- Spinning up a RunPod pod or Modal GPU and forgetting to tear it down.

## Project scaffolding (before stage 1 for non-trivial work)

For any run that produces a paper, a benchmark, or > 1 GPU-day of compute, scaffold the project layout first. See `references/project-scaffold.md` for the full structure:

- `configs/` — all hyperparameters, no magic numbers in code.
- `scripts/NN_*.py` — numbered, ordered execution (`00_config`, `01_download`, …).
- `src/<pkg>/` — reusable library code; `scripts/` just orchestrates it.
- `data/{raw,processed}/` — raw is immutable + gitignored; processed is reproducible.
- `literature/markdown/` — one `.md` per paper + `00_synthesis.md`.
- `runs/<timestamp>/` — `config.yaml`, `git_sha.txt`, `metadata.json`, checkpoints.
- `LEARNINGS.md` at the root — the decision log (see `references/learnings-log.md`).
- `paper/` — LaTeX if shipping a write-up; forces honesty on the numbers.

## Decision discipline — `LEARNINGS.md`

At every stage boundary, ask: *"Anything from this stage to log? (key decisions, surprises, pivots)"*. One prompt per stage, skip if user says no. See `references/learnings-log.md` for the format — each entry has Decision / Why / Alternatives / Reference / Next. Do not log routine edits or raw metrics (those live in `runs/<ts>/metadata.json`).

## Evaluation discipline (decide BEFORE training)

Standard `train_test_split` is the wrong default for most research problems. Before writing the trainer, pick the CV protocol that prevents leakage for your data shape:

- Spatial / graph / molecular structure → **leave-one-block-out**.
- Time series → **walk-forward**.
- Grouped users / sessions → **GroupKFold on the group id**.
- Domain shift A → B → **leave-one-domain-out**.
- Long-range deps with gaps → **gapped evaluation**.

Always name a benchmark at the end of stage 1. "Match or beat `<author, year>` `<metric>` `<value>` under `<our stricter protocol>`." Without a benchmark, "it works" is meaningless.

Default to **multi-seed** (minimum 3, ideally 5). Single-seed results are anecdotes. Report mean ± std and an effect size when comparing variants. See `references/evaluation.md`.

## Scripts

Runnable helpers that do actual work (not just tell Claude what to do):

- `scripts/init_project.py <dir>` — scaffolds the full project layout (`configs/`, `scripts/`, `src/<pkg>/`, `data/`, `literature/`, `runs/`, `results/`, `paper/`) with `CLAUDE.md`, `LEARNINGS.md`, `README.md`, `.gitignore`, `configs/base.yaml`. Idempotent.
- `scripts/check_placeholders.py [paths…]` — greps for unresolved `XX`, `TODO`, `FIXME`, `???` before shipping a paper or model card. Non-zero exit on any hit. Use as pre-submit check.

## References

- `references/setup.md` — install MCP servers + CLIs for each provider.
- `references/hardware-sizing.md` — pick the right GPU flavor across providers.
- `references/research-subagent.md` — exact prompts for the literature-pass sub-agent.
- `references/approval-template.md` — the message format for the stage-4 approval ask.
- `references/project-scaffold.md` — numbered scripts + `configs/` + `runs/` layout.
- `references/learnings-log.md` — `LEARNINGS.md` decision-log convention.
- `references/training-stack.md` — FSDP2, Liger, Unsloth, FP8, torch.compile, uv.
- `references/post-training-methods.md` — SFT / DPO / SimPO / KTO / ORPO / GRPO decision tree.
- `references/synthetic-data.md` — `distilabel`, Magpie, LLM-as-judge preference pairs.
- `references/model-merging.md` — `mergekit` (SLERP / TIES / DARE) as an alternative to re-training.
- `references/evaluation.md` — leakage-aware CV, benchmarks, `lm-eval-harness`, LLM-as-judge, metadata.
- `references/serving.md` — vLLM / TGI / Modal endpoints / RunPod Serverless / Spaces.
- `references/providers/huggingface.md` — HF Jobs tool surface + submit commands.
- `references/providers/runpod.md` — RunPod MCP + pod/serverless submission.
- `references/providers/modal.md` — Modal CLI + `@app.function` patterns.
- `references/providers/lambda.md` — Lambda Labs / CoreWeave / bare-metal SSH flows.
