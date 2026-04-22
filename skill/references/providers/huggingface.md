# Provider — Hugging Face Jobs

**Strengths:** tightest integration with Hub (models, datasets, Papers). Free CPU tier on Spaces for sandbox. Pay-per-second GPU billing. One-command `push_to_hub`.

**Weaknesses:** fewer GPU flavor options than RunPod. A100x8 is the ceiling (no H100 clusters as of writing).

## Tool surface (via HF MCP)

Install per `setup.md`. Relevant tools (names may vary by MCP version — use `/mcp` to list):

| Purpose | Tool family |
|---|---|
| Search papers / fetch full text | `mcp__huggingface__paper_*` |
| Search / inspect datasets | `mcp__huggingface__dataset_*` |
| Search / inspect models | `mcp__huggingface__model_*` |
| Read files in a Hub repo | `mcp__huggingface__repo_file_*` |
| Submit HF Jobs | `mcp__huggingface__jobs_submit` |
| Jobs status + logs | `mcp__huggingface__jobs_logs`, `jobs_status` |
| Create / update Hub repos | `mcp__huggingface__repo_*` |

If a capability is missing from your MCP version, fall back to Python:

```python
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(folder_path="./checkpoint", repo_id="user/model", repo_type="model")
```

## GPU flavors (current)

| Flavor | GPU | VRAM | Notes |
|---|---|---|---|
| `cpu-basic` | — | — | Free tier, sandbox dry-runs |
| `cpu-upgrade` | — | — | More RAM, still free-ish |
| `t4-small` | 1× T4 | 16 GB | Turing, fp16 only (no bf16) |
| `t4-medium` | 1× T4 | 16 GB | More RAM |
| `l4x1` / `l4x4` | 1/4× L4 | 24 GB ea | bf16, great value |
| `a10g-small` / `a10g-large` / `a10g-largex2` / `a10g-largex4` | A10G | 24 GB ea | Ampere, stable |
| `a100-largex1` / `a100-largex2` / `a100-largex4` | A100 | 80 GB ea | |
| `a100x8` | 8× A100 | 80 GB ea | Multi-node not exposed |

## Submit pattern

```python
# via MCP (preferred) — approval gate will show this to the user first
await jobs_submit(
    flavor="a10g-largex2",
    timeout_h=4,
    command=["python", "train.py", "--config", "configs/dpo.yaml"],
    source="./",                 # rsyncs local code to the job
    env={"WANDB_PROJECT": "dpo-repro"},
    secrets=["HF_TOKEN", "WANDB_API_KEY"],
)
```

Or via CLI fallback:

```bash
huggingface-cli jobs run \
  --flavor a10g-largex2 --timeout 4h \
  python train.py --config configs/dpo.yaml
```

## Output destination

Write checkpoints to `/data` in the job, set `push_to_hub=True` in `TrainingArguments`, and the training script will upload on save. Verify the repo exists or pass `create_repo=True`.

## When to choose HF Jobs

- The model, dataset, and checkpoint all live on the HF Hub.
- You want `push_to_hub` to be one line, not a script.
- Run is < 24h and fits in a100x8 or smaller.
- You don't want to manage any infrastructure.

## When to skip it

- You need H100s or 16+ GPU clusters → go Lambda / CoreWeave.
- You need serverless inference after training → go Modal or RunPod Serverless.
- You want to keep checkpoints off the Hub for IP reasons → pick a provider with private S3/R2.
