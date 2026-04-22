# Training stack — what to use in 2026

Opinionated defaults. These are the tools that materially change cost / speed / memory for real runs. Pin versions; the ecosystem moves fast.

## Core choices

| Layer | Default | When to deviate |
|---|---|---|
| Framework | **PyTorch ≥ 2.5** + **`transformers`** ≥ 4.48 + **`trl`** ≥ 0.13 | JAX / Flax only if you're reproducing a JAX paper faithfully. |
| Distributed | **FSDP2** (`torch.distributed.fsdp._fully_shard`) | DeepSpeed ZeRO-3 for CPU-offload. Megatron/NeMo for pretraining ≥ 30B. |
| Precision | **bf16 mixed** on Ampere+; **FP8** (Transformer Engine) on H100/H200 for 7B+ | fp16 only on Turing (T4). |
| Compile | **`torch.compile(mode="reduce-overhead")`** — default on | Disable when debugging a custom kernel or tiny model. |
| Attention | **FlashAttention-3** on H100/H200, **FA-2** on Ampere | SDPA default covers most cases now. |
| Fused kernels | **Liger Kernels** — drop-in replacement, ~20 % faster, ~60 % less memory on Llama/Gemma/Qwen/Mistral | Skip if your model family isn't supported yet. |
| LoRA fast-path | **Unsloth** — ~2× faster LoRA/QLoRA, ~50 % less VRAM, single-GPU only | Skip for multi-GPU — Unsloth is single-GPU; use `peft` + FSDP2. |
| Quantization (QLoRA) | **`bitsandbytes`** 4-bit NF4 | AWQ / GPTQ for inference-only. |
| LoRA variants | **DoRA** or **PiSSA** (LoRA successors, usually +1–2 pts for same params) | Plain LoRA when a paper uses it, for comparability. |

## Canonical configs

### Single-GPU LoRA/QLoRA (≤ 24 GB VRAM, model ≤ 13B)

```python
from transformers import TrainingArguments

args = TrainingArguments(
    output_dir="runs/",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,           # effective BS 32
    gradient_checkpointing=True,
    learning_rate=2e-4,                      # higher for LoRA than full FT
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    bf16=True,
    tf32=True,
    torch_compile=True,
    optim="adamw_torch_fused",
    logging_steps=10,
    save_steps=200,
    eval_strategy="steps",
    eval_steps=200,
    report_to=["wandb"],
    push_to_hub=True,
)
```

Pair with Unsloth's `FastLanguageModel.get_peft_model(...)` for the 2× speedup if it's single-GPU.

### Multi-GPU full FT (≥ 2 GPUs, model 7–70B)

```python
args = TrainingArguments(
    # ... as above, minus single-GPU knobs
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    bf16=True,
    fsdp="full_shard auto_wrap",
    fsdp_config={
        "backward_prefetch": "backward_pre",
        "use_orig_params": True,
        "limit_all_gathers": True,
        "transformer_layer_cls_to_wrap": "<YourModelDecoderLayer>",
    },
    ddp_find_unused_parameters=False,
)
```

Liger Kernels are applied with one line before building the model:

```python
from liger_kernel.transformers import apply_liger_kernel_to_llama
apply_liger_kernel_to_llama(rope=True, swiglu=True, cross_entropy=True, fused_linear_cross_entropy=True, rms_norm=True)
```

### FP8 on H100 (7B+ full FT)

```python
from transformer_engine.pytorch import fp8_autocast
# Wrap the forward pass; see NVIDIA TE docs for recipe.
```

Real-world speedup vs bf16: ~1.3–1.7× on H100, ~1.5–2× on H200. Don't attempt on Ampere (no FP8).

## Pre-flight memory estimate (mandatory before every run)

```bash
accelerate estimate-memory <org>/<model> --dtype bf16 --library_name transformers
```

Report training memory ≈ inference × 4 for full FT, × 1.3 for LoRA, × 0.6 for QLoRA. If `estimate-memory` says 80 GB and you picked a 48 GB GPU, stop here — don't discover it at step 50.

## Logging / tracking

Use **`wandb`** (`report_to=["wandb"]`) or **`aim`**. Always log: final metrics, full config, git SHA, wall-time, peak VRAM (from `torch.cuda.max_memory_allocated()`), and `runs/<ts>/metadata.json` (see `evaluation.md`).

## Environment reproducibility

Pin via **`uv`**:

```bash
uv init && uv add torch transformers trl datasets accelerate peft bitsandbytes wandb
uv lock
```

Commit `uv.lock`. The training container (HF Jobs, Modal image, RunPod template) should `uv sync --frozen` from it.

## Anti-patterns

- **Running without `gradient_checkpointing`** on a model > 7B to save wall-time. You'll OOM and waste the whole run.
- **Setting `max_steps` higher "to be safe."** Pick a defensible number from your token budget, don't pad.
- **`num_train_epochs=3` on 10M examples.** That's 30M training examples. Probably not what you want.
- **Skipping the memory estimate.** The single cheapest bug-prevention step.
- **Using `trust_remote_code=True` on an unvetted model.** Read the code or use a trusted mirror.
