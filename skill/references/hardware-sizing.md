# Hardware sizing — cross-provider

Pick the smallest GPU that fits. Over-provisioning wastes money; under-provisioning loses the run to OOM halfway through.

This table is provider-agnostic — think in **VRAM needed** first, then map to whatever your chosen provider offers. Per-provider flavor details live in `providers/*.md`.

## VRAM budget (rough, bf16 training)

| Model params | LoRA / QLoRA | Full FT | Min VRAM (total) |
|---|---|---|---|
| ≤ 1B | ✓ any 16 GB | ✓ 16 GB | 16 GB |
| 1–3B | ✓ 16 GB | ✓ 24 GB | 24 GB |
| 3–7B | ✓ 24 GB | ✓ 48 GB (48 GB in bf16) | 24 GB LoRA / 48 GB full |
| 7–13B | ✓ 24 GB QLoRA, 48 GB LoRA | ✓ 2× 48 GB | 24 GB QLoRA / 96 GB full |
| 13–34B | ✓ 48 GB, 80 GB | ✓ 2× 80 GB (ZeRO-3) | 48 GB QLoRA / 160 GB full |
| 34–70B | ✓ 2× 80 GB | ✓ 4× 80 GB (FSDP / ZeRO-3) | 160 GB QLoRA / 320 GB full |
| 70B+ | 4× 80 GB | 8× 80 GB | 320–640 GB |

## Cross-provider GPU map (24 GB / 48 GB / 80 GB tiers)

| Tier | HF Jobs | RunPod | Modal | Lambda / CoreWeave |
|---|---|---|---|---|
| 24 GB (bf16 OK) | `l4x1` | RTX 4090 / L40S | `L4` / `A10G` | L4 / A10G SKUs |
| 24 GB (fp16 only) | `t4-small` | RTX 4000 Ada | `T4` | T4 SKUs |
| 48 GB | `a10g-large` / `a10g-largex2` | RTX A6000 | `A10G` + ZeRO | A6000 SKUs |
| 80 GB A100 | `a100-largex1..4` | A100 80GB | `A100-80GB` | A100 SKUs |
| 80 GB H100 | — (not offered) | H100 PCIe/SXM | `H100` / `H100!` | H100 SKUs |
| 141 GB H200 | — | H200 | `H200` | H200 SKUs |
| 192 GB B200 | — | (rolling out) | `B200` | (rolling out) |

## Timeouts

Every provider kills the job at timeout without warning. Request **2× expected wall-time, minimum 2h**. For runs > 24h, checkpoint every N steps and be ready to resume.

## Sandbox / dry-run flavors

| Purpose | Pick |
|---|---|
| Config sanity check, 1–2 steps | `cpu-basic` (HF) / local CPU / Modal CPU |
| Small-model end-to-end | `t4-small` (HF) / RTX 4090 spot (RunPod) / `T4` (Modal) |
| Debugging multi-GPU setup | Cheapest 2-GPU flavor on your target provider |

Match the sandbox architecture to the real run (same CUDA major version, same NCCL, same distributed backend). FSDP bugs do not show up on a single GPU.

## Cost heuristics (ballpark, check current pricing)

- **Cheapest 24 GB GPU**: RunPod community RTX 4090 at ~$0.34/hr. Great sandbox.
- **Cheapest bf16-capable 24 GB**: HF `l4x1` or RunPod L40S.
- **Cheapest 80 GB A100**: RunPod community ~$1.19/hr. HF `a100-largex1` slightly higher but with Hub integration.
- **Cheapest H100**: RunPod community ~$1.99/hr.
- **Multi-H100 cluster with InfiniBand**: Lambda / CoreWeave reserved.

Order-of-magnitude rule: a 7B SFT run on 100k examples is ~$5–15 on a single A100 depending on sequence length. If your estimate is wildly different, double-check the math before submitting.

## Red flags in a user request

Push back before submitting if any of these:

- "Full fine-tune 70B on a single GPU" — won't fit.
- "Train for 10 epochs" on a 10M-example dataset — suggest `max_steps` based on compute budget instead.
- "Just run it on 8× H100 to be safe" — usually 5–8× the cost for no measurable speedup on typical SFT.
- No `eval_strategy` set — you won't know if it's learning until it's done.
- No `save_steps` on a run > 4h — one crash and everything is lost.
- Timeout set to exactly the expected wall-time — zero buffer; first thing that goes wrong kills the run.
