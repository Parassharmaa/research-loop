# Provider — RunPod

**Strengths:** lowest $/GPU-hour of the managed providers. H100 available. Both long-running Pods and autoscaled Serverless endpoints. Real MCP server.

**Weaknesses:** less polished Hub-style integration — you bring your own storage (network volume, S3, or push to HF Hub at the end). Spot pods can be preempted.

## Tool surface (via RunPod MCP)

Install per `setup.md`. Tools (confirm names with `/mcp`):

| Purpose | Tool |
|---|---|
| List / create / start / stop Pods | `mcp__runpod__pod_*` |
| Deploy Serverless endpoints | `mcp__runpod__serverless_*` |
| Manage templates (Docker image + env) | `mcp__runpod__template_*` |
| Network volumes | `mcp__runpod__volume_*` |
| Container registries | `mcp__runpod__registry_*` |

If missing, fall back to the REST API:

```bash
curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
  https://rest.runpod.io/v1/pods | jq .
```

## GPU options (current, indicative)

| GPU | VRAM | Community $/hr | Secure $/hr |
|---|---|---|---|
| RTX 4090 | 24 GB | ~$0.34 | ~$0.69 |
| RTX A6000 | 48 GB | ~$0.49 | ~$0.79 |
| L40S | 48 GB | ~$0.79 | ~$1.19 |
| A100 80 GB | 80 GB | ~$1.19 | ~$1.89 |
| H100 80 GB PCIe | 80 GB | ~$1.99 | ~$2.99 |
| H100 SXM / H200 | 80–141 GB | ~$2.49+ | ~$3.79+ |

(Check <https://www.runpod.io/pricing> — spot/community prices move.)

## Submit pattern — long-running Pod

```python
# 1. Create a pod from a template (approval gate first!)
pod = await pod_create(
    gpu_type_id="NVIDIA H100 80GB HBM3",
    cloud_type="COMMUNITY",         # or "SECURE" for SLA
    image_name="runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
    volume_mount_path="/workspace",
    volume_in_gb=200,
    env={"HF_TOKEN": "...", "WANDB_API_KEY": "..."},
    docker_args="",
    ports="22/tcp,8888/http",
)

# 2. rsync code → pod (via ssh details returned by the API)
#    ssh root@<pod-ip> -p <port>  +  rsync -az ./ root@<pod-ip>:/workspace/
# 3. Run training in tmux so SSH dropouts don't kill it
#    ssh ... "cd /workspace && tmux new -d -s train 'python train.py ...'"
# 4. Poll `pod_get` for status; tail logs with ssh tail -f
# 5. Rsync checkpoints back, or push_to_hub from inside the pod
# 6. **Stop the pod** (pod_stop) or you keep paying
```

## Submit pattern — Serverless (for inference after training)

```python
endpoint = await serverless_create(
    name="my-finetuned-model",
    template_id="...",           # or inline image + env
    gpu_ids=["NVIDIA L40S"],
    min_workers=0,               # scale to zero
    max_workers=3,
    idle_timeout_s=5,
)
```

## Output / checkpoint strategy

Three options, pick one up-front and tell the user:

1. **`push_to_hub` from inside the pod** — simplest. Set `HF_TOKEN` env, training script uses `TrainingArguments(push_to_hub=True)`.
2. **Network volume** — persists across pod restarts, stays on RunPod. Good for multi-stage pipelines.
3. **S3 / R2 sync at end** — cheapest long-term storage, requires AWS CLI or `rclone` in the container.

## Gotchas

- **Spot pods preempt.** Use `cloud_type="SECURE"` for runs > 6h, or checkpoint every N steps and rely on resume.
- **`/workspace` is ephemeral on some templates.** Mount a volume at `/workspace` explicitly, or your work is gone on restart.
- **Container CUDA must match PyTorch CUDA.** Use RunPod's official `runpod/pytorch:*` images unless you have a reason not to.
- **Always stop pods after the run.** A forgotten H100 at $2/hr is $48/day. The skill's approval template includes an explicit teardown reminder.

## When to choose RunPod

- You want the lowest price per GPU-hour.
- You need H100/H200s.
- You want persistent pods you can SSH into for debugging.
- You plan to expose the trained model via Serverless inference.

## When to skip

- You only want Hub integration → HF Jobs.
- You hate managing pods → Modal.
- You need enterprise SOC2 / dedicated nodes → CoreWeave.
