# Project scaffold — the layout the loop assumes

Enforce this layout for any non-trivial run. Small one-off experiments can skip it; anything with a paper, a benchmark, or > 1 GPU day of compute should not.

## Top-level layout

```
<project>/
├── CLAUDE.md                # goal + stack + conventions (see below)
├── LEARNINGS.md             # live decision log (see learnings-log.md)
├── README.md                # public-facing, generated / maintained
├── configs/                 # all hyperparameters. No magic numbers in code.
│   ├── base.yaml
│   └── ablations/           # variant A / B / C… as separate files
├── scripts/                 # numbered, ordered execution
│   ├── 00_config.py         # (or just configs/base.yaml)
│   ├── 01_download_data.py
│   ├── 02_preprocess.py
│   ├── 03_features.py
│   ├── 04_baseline.py
│   ├── 05_model.py          # the novel contribution
│   ├── 06_uncertainty.py
│   ├── 07_explain.py
│   ├── 08_eval.py
│   └── 09_paper_figures.py
├── src/<pkg>/               # reusable library code
│   ├── data/
│   ├── models/
│   ├── training/
│   └── analysis/
├── data/
│   ├── raw/                 # immutable, gitignored
│   └── processed/           # derived, reproducible from scripts
├── literature/
│   ├── markdown/            # one .md per paper (notes + quotes)
│   └── 00_synthesis.md      # aggregate + gaps + selected approach
├── runs/                    # or runs_v5/, runs_v6/ for major iterations
│   └── <timestamp>/
│       ├── config.yaml      # snapshot of configs used
│       ├── git_sha.txt
│       ├── metadata.json    # metrics + env + wall-time
│       └── checkpoints/     # or link to remote (Hub, S3, Modal volume)
├── results/                 # figures, tables, final artifacts (gitignored)
└── paper/                   # LaTeX manuscript — forces honesty
    ├── main.tex
    ├── figures/
    └── references.bib
```

## Naming rules

- **Numbered scripts** (`00_`, `01_`, … `NN_`). The number encodes execution order. If a new step slots between 03 and 04, renumber — don't do `03b_`.
- **kebab-case** for file names, **snake_case** for Python identifiers.
- **`runs_v<N>/`** for major methodology iterations (not minor hyperparameter sweeps — those go inside a single `runs/` as timestamped subdirs).
- **No hardcoded paths.** Read from a config. `data/processed/` is a config value, not a literal in a script.

## `CLAUDE.md` — project-level directives

Short and directive, not a README. Example skeleton:

```md
# <project>

## Goal
<one sentence — who is the user of this work, what decision does it inform>

## Outcome
<what artifact ships — a model, a dashboard, a paper, a dataset>

## Stack
- Data: <GEE / HF datasets / local>
- Modeling: <PyTorch, PyG, trl, ...>
- Eval: <MAPIE for CP, SHAP for explainability, ...>
- Infra: <provider — see research-loop skill>

## Conventions
- Config-driven — all hyperparameters in configs/, nothing hardcoded.
- Tests mirror source structure.
- Scripts are numbered and idempotent — rerunning must not corrupt state.
- No Claude email in commits.

## Plan
See LEARNINGS.md for decisions to date.
See docs/task_plan.md for the remaining task list.
```

## When to scaffold vs not

Scaffold when:
- Run will produce a paper, a dashboard, or an external deliverable.
- Multiple ablation variants are planned.
- Compute budget > 1 GPU-day.
- Reproducibility matters (shared work, public release).

Skip the scaffold when:
- One-shot "does this fine-tune at all" check.
- Notebook exploration that won't ship.
- Using someone else's repo as the entry point (then live inside *their* scaffold).

## Checkpoint — before writing any training code

After stage 1 (literature) and before stage 2 (validate), confirm with the user:

```
I'll scaffold the project as:
  configs/         — {files I plan to create}
  scripts/         — {numbered scripts I plan to create}
  src/<pkg>/       — {modules I plan to create}
  LEARNINGS.md     — decision log, first entry: "chose <method> because {rationale from literature pass}"

Reply `scaffold` to create, or tell me what to change.
```
