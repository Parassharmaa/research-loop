# Provider — Modal

**Strengths:** best developer experience. Functions-as-a-service for GPUs: decorate a Python function with `@app.function(gpu="A100")` and it runs remotely. Built-in persistent volumes, secrets, scheduling, web endpoints. No pod management.

**Weaknesses:** no MCP server (as of writing) — drive via CLI + Python. Slightly higher per-hour cost than RunPod community tier. GPU selection less granular.

## Setup

```bash
pip install modal                # version-pin in your project's requirements
modal token new                  # browser auth → ~/.modal.toml
modal profile current            # verify
```

## GPU options (`gpu=` string)

| Value | GPU | VRAM | Notes |
|---|---|---|---|
| `"T4"` | T4 | 16 GB | Cheapest; sandbox only |
| `"L4"` | L4 | 24 GB | bf16, good value |
| `"A10G"` | A10G | 24 GB | Stable choice |
| `"A100"` / `"A100-40GB"` | A100 | 40 GB | |
| `"A100-80GB"` | A100 | 80 GB | |
| `"H100"` | H100 | 80 GB | |
| `"H100!"` | H100 | 80 GB | Strict — fail fast if unavailable |
| `"H200"` | H200 | 141 GB | |
| `"B200"` | B200 | 192 GB | Blackwell, limited availability |

Multi-GPU: `gpu="H100:8"` for 8× H100 on one node.

## Submit pattern

```python
# train_modal.py
import modal

app = modal.App("my-finetune")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "torch==2.5.1",
        "transformers==4.48.0",
        "trl==0.13.0",
        "datasets==3.2.0",
        "accelerate==1.2.1",
        "peft==0.14.0",
        "wandb",
    )
)

vol = modal.Volume.from_name("ft-checkpoints", create_if_missing=True)

@app.function(
    image=image,
    gpu="H100:2",
    timeout=4 * 60 * 60,           # 4h, hard kill at this
    volumes={"/ckpt": vol},
    secrets=[
        modal.Secret.from_name("huggingface"),   # HF_TOKEN
        modal.Secret.from_name("wandb"),         # WANDB_API_KEY
    ],
)
def train():
    import subprocess
    subprocess.run(["python", "train.py", "--output_dir", "/ckpt/run1"], check=True)

@app.local_entrypoint()
def main():
    train.remote()
```

Run:

```bash
modal run train_modal.py        # blocks, streams logs
modal run --detach train_modal.py    # fire-and-forget
modal app logs my-finetune      # later
modal volume ls ft-checkpoints  # find outputs
```

## Secrets

Create once, referenced by name:

```bash
modal secret create huggingface HF_TOKEN=hf_xxx
modal secret create wandb WANDB_API_KEY=...
```

## Output / checkpoint strategy

1. **Modal Volume** (above) — persists, mounted at `/ckpt`. Cheap storage.
2. **`push_to_hub` from inside the function** — `HF_TOKEN` from the secret.
3. **Cloud storage mount** — Modal supports S3, R2, GCS via `modal.CloudBucketMount`.

```python
volumes={
    "/data": modal.CloudBucketMount("my-bucket", secret=modal.Secret.from_name("aws")),
}
```

## Gotchas

- **Cold-start on first call** — pulling a 10 GB image + CUDA can take 60–120s. Use `.persist_new_layers_after` and build images with pinned versions to keep this predictable.
- **Timeout kills are hard.** Set higher than you think. No grace period.
- **Two billing modes** — "startup" and "pay-as-you-go". Check your account.
- **`@app.function` is picklable** — arguments and return values cross the wire. For large tensors, write to a volume instead of returning.
- **`.remote()` vs `.spawn()`** — `remote()` blocks until done; `spawn()` returns a handle for `.get()` later. Use `spawn()` for long runs with a polling loop.

## Finding the right version pins

Modal's examples repo is the best reference:

```
https://github.com/modal-labs/modal-examples
```

For current HF ecosystem versions at the time you run, ask Claude to fetch the relevant package's PyPI JSON endpoint before writing the image. Example: `curl -s https://pypi.org/pypi/trl/json | jq -r .info.version`.

## When to choose Modal

- You want to write training code, not infra code.
- You need to expose the trained model as an HTTP endpoint (`@app.function` + `@web_endpoint` is trivial).
- You're doing many short runs (Modal scales to zero between calls).
- You want H100 / H200 / B200 with first-class multi-GPU.

## When to skip

- You need the absolute cheapest per-hour price → RunPod spot.
- You need MCP-based approval flow that a junior teammate can walk through → HF Jobs.
- You need SSH-able bare metal → Lambda / CoreWeave.
