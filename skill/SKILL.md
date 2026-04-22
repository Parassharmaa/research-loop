---
name: research-loop
description: ML-engineering loop — literature-first reproduction and training. Use when the user asks to reproduce a paper, fine-tune or pretrain a model, build a benchmark, ship a model to Hugging Face Hub, or run a training job on HF Jobs. Enforces: (1) read papers and reference code before writing any training code, (2) validate dataset shape and tokenizer, (3) sandbox-test on a small split, (4) only then submit full training. Expects the Hugging Face MCP server to be available (tools prefixed hf_* / mcp__hf*).
when_to_use: Trigger on "reproduce this paper", "fine-tune X on Y", "train a model", "run this on HF Jobs", "build a benchmark", "push this model to the Hub", "SFT / DPO / GRPO / LoRA", "pretraining run", or any request that involves ML training and Hugging Face infrastructure.
argument-hint: [paper-or-task] [dataset?] [base-model?]
allowed-tools: Read Write Edit Glob Grep Bash Agent WebFetch WebSearch
---

# research-loop

An opinionated ML-engineering workflow. The name is literal — you **loop between literature and code** before ever touching a GPU.

This skill does **not** reimplement tools. It composes:
- Claude Code's native tools (Bash, Edit, Agent, etc.)
- The **Hugging Face MCP server** for Hub/papers/datasets/Jobs (install separately — see `references/setup.md`)
- A parallel research sub-agent pattern via the `Agent` tool

## The five stages

You MUST execute these in order. Skipping a stage is the single biggest cause of wasted GPU hours.

### 1. Literature pass (BEFORE any code)

Spawn a research sub-agent via `Agent(subagent_type: "Explore")` with a focused brief:

> "Find the 2–3 landmark papers on <topic>. For each, extract from **sections 3–5** (methodology/experiments, not abstracts): exact datasets used, preprocessing, base model, training hyperparameters, hardware, and reported metrics. Also find one high-quality reference implementation on GitHub or the Hub. Return a table."

Use HF MCP paper tools + WebFetch for arXiv/ar5iv HTML. Crawl citations one hop out for the *original* source of the dataset or recipe.

**Do not write training code until this table exists.** If the user pushes back, explain that a 10-minute literature pass prevents a 6-hour failed run.

### 2. Dataset + tokenizer validation

Before writing the trainer:
- Inspect the dataset via HF MCP (`hf_inspect_dataset` or equivalent). Record: row count, columns, token-length p50/p95/max, label distribution.
- Load the tokenizer and tokenize 10 random rows. Print token counts. Catch: truncation at the wrong length, missing BOS/EOS, chat-template mismatch.
- If the dataset needs preprocessing, write it as a standalone script and verify output before moving on.

### 3. Sandbox-first training

Write the training script. Run it **on CPU or a single small GPU against a 100-row slice**, for 1–2 steps, before touching real hardware. This catches ~80% of config errors at near-zero cost.

Options, in order of preference:
1. Local Python + small model (e.g. `sshleifer/tiny-gpt2`) — fastest iteration.
2. HF Jobs CPU flavor — if local can't fit.
3. HF Jobs smallest GPU (`t4-small`) — last resort.

The script must: load model, load dataset slice, run 1–2 optimizer steps, print loss, save a checkpoint to disk. If any of those fail, fix them here, not in the full run.

### 4. Full training submission (approval gate)

Only now, submit the real job via HF MCP Jobs tools. **ALWAYS stop and confirm with the user before submitting a GPU job.** Show them:
- Full training script (link or quote the relevant section)
- Dataset + size
- Base model
- GPU flavor + estimated cost and wall-time
- `push_to_hub` destination (repo must exist or be created)
- `max_steps` / `num_train_epochs`
- Timeout (at least 2× expected wall-time — HF Jobs defaults bite)

See `references/hardware-sizing.md` for GPU flavor selection.

### 5. Ship

- Monitor via HF MCP job logs. Do not poll faster than once per minute.
- On completion: verify checkpoint pushed, write a model card, run eval, post metrics back to the user.
- If the run failed: read the logs, diagnose, and loop back to stage 3 — **do not** immediately resubmit with a "creative" workaround.

## Guardrails (non-negotiable)

- **No scope-changing fixes.** When you hit OOM or a tokenizer error, do not silently switch to a smaller model, shorter context, or different dataset to make the error go away. Report the constraint, propose options, and let the user decide.
- **No bare `rm`, no force-push, no destructive Hub ops without explicit confirmation.** Destructive Hub operations include: deleting a repo, deleting a branch, overwriting an existing file on `main`. Use `create_pr: true` for changes to shared repos.
- **Approval required for:** any HF Jobs GPU submission, any `hf_jobs` CPU run > 30 min, any `push_to_hub` to a repo you didn't create this session, any dataset deletion or mass upload.
- **One task in-progress at a time.** Use `TaskCreate` to track stages. Mark completed the moment a stage is done.

## Anti-patterns (stop if you notice yourself doing these)

- Writing the training loop before the literature table exists.
- Submitting to GPU without a sandbox dry-run.
- Re-submitting a failed job more than once without a root-cause hypothesis.
- Asking the user to approve the same GPU job twice with minor tweaks — batch fixes, then re-request.
- Increasing `max_steps` "just in case."
- Using `trust_remote_code=True` without checking what the code does.

## References

- `references/setup.md` — install the HF MCP server and verify it's available.
- `references/hardware-sizing.md` — pick the right GPU flavor for the model size.
- `references/research-subagent.md` — exact prompts for the literature-pass sub-agent.
- `references/approval-template.md` — the message format for the stage-4 approval ask.
