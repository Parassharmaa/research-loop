# research-loop

A Claude Code skill for ML / research engineering. Enforces a disciplined five-stage loop — **literature → validate → sandbox → approval → ship** — so GPU hours aren't burned on preventable bugs.

Provider-agnostic. Drive your training on **Hugging Face Jobs, RunPod, Modal, Lambda, CoreWeave, Together, or local** — same workflow, different backends.

## Why a skill (and not another CLI)

Skills live inside Claude Code, so they ride on your Claude subscription, reuse Claude Code's native tools (`Bash`, `Edit`, `Agent`, `WebFetch`, …), and compose with any MCP servers you already have installed.

The skill itself is just prompts + reference files. The heavy lifting — Hub search, Jobs submit, GPU provisioning, code execution — is delegated to the right MCP server or CLI for each provider. No vendor lock-in.

## The loop

1. **Literature pass** — a research sub-agent mines 2–3 landmark papers + one canonical reference implementation. Extracts exact datasets, hyperparameters, and hardware from the methodology sections.
2. **Validate** — inspect dataset shape, token-length distribution, tokenizer sanity. Catch the silent killers (wrong chat template, wrong max length, label skew) before spending money.
3. **Sandbox** — dry-run the trainer on CPU or a tiny GPU slice for 1–2 steps. Kills ~80 % of config bugs at near-zero cost.
4. **Approval gate** — stop and show the user the full run config (script, flavor, cost, output destination, timeout) before launching anything on a paid GPU. Explicit teardown reminder.
5. **Ship** — monitor logs, verify checkpoints uploaded, write a model card, run eval, post metrics back.

Plus project-scaffolding conventions (numbered scripts, `configs/`, `LEARNINGS.md` decision log, `runs/<timestamp>/metadata.json`) that keep work reproducible weeks later.

## Install

```bash
# 1. clone + install the skill into your user Claude config
git clone https://github.com/Parassharmaa/research-loop.git
cp -r research-loop/skill ~/.claude/skills/research-loop

# 2. install at least one provider (Hugging Face recommended — useful even
#    if you train elsewhere, for paper + dataset + model search)
claude mcp add --transport http huggingface https://huggingface.co/mcp
huggingface-cli login

# 3. add any other providers you use
claude mcp add runpod npx '@runpod/mcp-server@latest' -e RUNPOD_API_KEY=rpa_...
pip install modal && modal token new
# (Lambda / CoreWeave / Together use SSH + CLI; no MCP needed.)
```

Verify inside a Claude Code session:

```
/mcp
```

Then ask Claude something ML-shaped — "reproduce the DPO paper on UltraFeedback", "fine-tune llama-3.2-1b on my csv and push to the Hub", "benchmark 3 embedding models". The skill triggers on training / reproduction / fine-tuning keywords listed in its `when_to_use` field.

## Skill layout

```
skill/
├── SKILL.md                              # entry point, the 5-stage loop + guardrails
└── references/
    ├── setup.md                          # MCP + CLI install per provider
    ├── hardware-sizing.md                # cross-provider GPU map + VRAM budget
    ├── research-subagent.md              # literature-pass sub-agent prompts
    ├── approval-template.md              # the pre-GPU-submit checklist
    ├── project-scaffold.md               # numbered scripts + configs/ + runs/ layout
    ├── learnings-log.md                  # LEARNINGS.md decision-log convention
    ├── evaluation.md                     # leakage-aware CV, benchmarks, uncertainty
    └── providers/
        ├── huggingface.md
        ├── runpod.md
        ├── modal.md
        └── lambda.md                     # Lambda / CoreWeave / Together / bare metal
```

## Requirements

- **Claude Code** ≥ 2.0 (skills + MCP support).
- **At least one GPU backend:**
  - Hugging Face — remote MCP at `https://huggingface.co/mcp`.
  - RunPod — local MCP via `npx @runpod/mcp-server@latest`.
  - Modal — CLI (`pip install modal`).
  - Lambda / CoreWeave / Together — SSH + their REST APIs.
- **`huggingface_hub`** ≥ 1.0 for any Hub fallback (`pip install 'huggingface_hub>=1.0'`; latest at time of writing: 1.11).

## Example

See `example/reproduce-dpo.md` for a worked walkthrough — from "reproduce the DPO paper on UltraFeedback" through literature pass, dataset validation, sandbox dry-run, approval gate, and final submission on RunPod / HF Jobs.

## License

MIT
