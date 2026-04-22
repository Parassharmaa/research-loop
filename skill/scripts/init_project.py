#!/usr/bin/env python3
"""Scaffold a research-loop project.

Creates the standard layout described in references/project-scaffold.md:
  CLAUDE.md, LEARNINGS.md, README.md,
  configs/, scripts/, src/<pkg>/,
  data/{raw,processed}/, literature/markdown/,
  runs/, results/, paper/

Usage:
    python init_project.py <project_dir> [--pkg <python_package_name>]

Idempotent — won't overwrite existing files.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

DIRS = [
    "configs",
    "configs/ablations",
    "scripts",
    "data/raw",
    "data/processed",
    "literature/markdown",
    "runs",
    "results",
    "paper/figures",
]

CLAUDE_MD = """# {name}

## Goal
<one sentence — who uses this work, what decision does it inform>

## Outcome
<what ships — a model, a dashboard, a paper, a dataset>

## Stack
- Data: <source>
- Modeling: <framework + key libraries>
- Eval: <leakage-aware protocol + benchmark target>
- Infra: <provider — HF Jobs / RunPod / Modal / Lambda / local>

## Conventions
- Config-driven — all hyperparameters in `configs/`, nothing hardcoded.
- Numbered scripts in `scripts/NN_*.py`, idempotent.
- Tests mirror source structure.
- No Claude email in commits.

## Plan
See `LEARNINGS.md` for decisions to date.
"""

LEARNINGS_MD = """# LEARNINGS

Append-only decision log. Newest first. Format:

## YYYY-MM-DD — <short headline>
**Decision:** <what>
**Why:** <the reason, grounded in data or literature>
**Alternatives considered:** <what was rejected and why>
**Reference:** <paper / doc / issue; point at literature/markdown/*.md>
**Next:** <immediate follow-up>

---

## {today} — Project initialized
**Decision:** Scaffolded with research-loop skill.
**Why:** Starting a new ML research project; enforcing staged workflow.
**Next:** Run stage 1 (literature pass).
"""

README_MD = """# {name}

<one-line description>

## Status
Scaffolded {today}. See `LEARNINGS.md` for decision log and `CLAUDE.md` for
stack + conventions.

## Layout
```
configs/               hyperparameters — no magic numbers in code
scripts/NN_*.py        numbered, ordered execution
src/{pkg}/             reusable library code
data/{{raw,processed}}   raw is immutable + gitignored; processed reproducible
literature/markdown/   one .md per paper + 00_synthesis.md
runs/<timestamp>/      per-run config + metadata + checkpoints
results/               figures, tables (gitignored)
paper/                 LaTeX manuscript
```
"""

GITIGNORE = """# research-loop default ignores
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
.DS_Store
.env
.env.local

# data: raw is immutable but not versioned
data/raw/*
!data/raw/.gitkeep

# derived data
data/processed/*
!data/processed/.gitkeep

# runs + results
runs/*
!runs/.gitkeep
results/*
!results/.gitkeep

# model checkpoints
*.bin
*.safetensors
*.pt
*.ckpt

# tracking
wandb/
mlruns/
"""

BASE_YAML = """# configs/base.yaml — edit to fit your task
model:
  name_or_path: <base-model-hub-id>
  trust_remote_code: false

data:
  dataset_id: <dataset-hub-id>
  split: train
  max_length: 1024

train:
  method: sft           # sft | dpo | simpo | kto | orpo | grpo
  lr: 2.0e-5
  epochs: 1
  per_device_train_batch_size: 4
  gradient_accumulation_steps: 8
  bf16: true
  torch_compile: true
  gradient_checkpointing: true
  seed: 0

eval:
  strategy: block        # block | walk-forward | groupkfold | random (justify!)
  benchmark: "<author year> <metric> <value> on <dataset>"
  seeds: [0, 1, 2]       # minimum 3; 5 preferred
  tasks: [mmlu, gsm8k]   # lm-eval-harness task names

infra:
  provider: huggingface  # huggingface | runpod | modal | lambda | local
  gpu_flavor: <pick from hardware-sizing.md>
  timeout_hours: 4
  output_repo: <your-username>/<model-name>
"""

SYNTHESIS_MD = """# Literature synthesis

Filled during stage 1. One section per landmark paper, plus a final
"selected approach" section tying decisions to LEARNINGS.md.

## Papers

<filled by research sub-agent>

## Selected approach
<filled after literature pass>
"""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("target", type=Path, help="Project directory (will be created).")
    p.add_argument("--pkg", default=None, help="Python package name under src/.")
    args = p.parse_args()

    target: Path = args.target.resolve()
    pkg = args.pkg or target.name.replace("-", "_").replace(" ", "_")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    target.mkdir(parents=True, exist_ok=True)

    for d in DIRS + [f"src/{pkg}"]:
        (target / d).mkdir(parents=True, exist_ok=True)

    # .gitkeep for empty dirs that should persist
    for d in ["data/raw", "data/processed", "runs", "results"]:
        (target / d / ".gitkeep").touch(exist_ok=True)

    files = {
        "CLAUDE.md": CLAUDE_MD.format(name=target.name),
        "LEARNINGS.md": LEARNINGS_MD.format(today=today),
        "README.md": README_MD.format(name=target.name, pkg=pkg, today=today),
        ".gitignore": GITIGNORE,
        "configs/base.yaml": BASE_YAML,
        "literature/markdown/00_synthesis.md": SYNTHESIS_MD,
        f"src/{pkg}/__init__.py": "",
    }

    created, skipped = [], []
    for rel, body in files.items():
        f = target / rel
        if f.exists():
            skipped.append(rel)
            continue
        f.write_text(body)
        created.append(rel)

    print(f"Scaffolded at: {target}")
    if created:
        print("  created:")
        for r in created:
            print(f"    {r}")
    if skipped:
        print("  skipped (already present):")
        for r in skipped:
            print(f"    {r}")
    print()
    print("Next: stage 1 (literature pass). See research-loop SKILL.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
