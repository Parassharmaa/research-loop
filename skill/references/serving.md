# Serving — what to run after training

Stage 5 isn't always "push to Hub and done." Often the deliverable is a **running endpoint** — a chat API, a batch inference service, a UI demo. Pick the serving stack to match.

## Decision table

| Deliverable | Pick |
|---|---|
| "Let me curl a model" — dev-internal, small traffic | `vLLM` on any GPU box |
| Production REST API, autoscaling, low ops | **Modal `@web_endpoint`** or **RunPod Serverless** |
| Max throughput, fixed capacity | **`vLLM` + `vllm serve`** or **TGI** on dedicated GPU |
| HF-integrated demo for stakeholders | **Hugging Face Spaces** with Gradio |
| Free demo on HF's dime (low-traffic) | **Spaces ZeroGPU** (shared A10G, auto-sleep) |
| Llama.cpp / CPU / laptop | `llama.cpp` + `llamafile` |
| Structured generation (JSON, regex) | `Outlines` / `xgrammar` in front of vLLM |

## vLLM (default for GPU serving)

```bash
pip install vllm                  # pin latest; fast-moving
vllm serve <org>/<model> \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --tensor-parallel-size 1
```

OpenAI-compatible endpoint on :8000. Add `--quantization awq` for AWQ-quantized weights on smaller cards. For batched throughput testing: `vllm bench throughput ...`.

## TGI (Hugging Face Text Generation Inference)

```bash
docker run --gpus all -p 8080:80 \
  -v $HOME/.cache/huggingface:/data \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id <org>/<model>
```

Slightly more opinionated than vLLM. Strong on Hub integration and streaming.

## Modal — serverless with a decorator

```python
import modal

app = modal.App("my-chat")
image = modal.Image.debian_slim().pip_install("vllm", "fastapi")

@app.cls(image=image, gpu="H100", scaledown_window=60, max_containers=4)
class Engine:
    @modal.enter()
    def load(self):
        from vllm import LLM
        self.llm = LLM(model="<org>/<model>", dtype="bfloat16")

    @modal.fastapi_endpoint(method="POST")
    def chat(self, data: dict):
        from vllm import SamplingParams
        out = self.llm.generate(data["prompt"], SamplingParams(max_tokens=512))
        return {"text": out[0].outputs[0].text}
```

`modal deploy` gives you a public HTTPS URL. Scales to zero; pays per-second of GPU time used.

## RunPod Serverless

1. Package your handler in a Docker image (`pip install runpod`, implement `handler(job)`).
2. Push to a registry.
3. `runpod_serverless_create(...)` via MCP, or the web console.
4. Endpoints autoscale to zero; cold-start ~10–30s depending on image size.

Best when you're already on RunPod and want inference close to the training pod.

## Hugging Face Spaces

- Free CPU Spaces for demos.
- **ZeroGPU** — shared A10G, free for community users, rate-limited. Great for showing a model to non-technical stakeholders.
- Paid GPU Spaces for persistent demos.

Gradio is the standard UI:

```python
import gradio as gr
from transformers import pipeline
pipe = pipeline("text-generation", model="<org>/<model>")
gr.Interface(fn=lambda q: pipe(q)[0]["generated_text"], inputs="text", outputs="text").launch()
```

## Structured generation layer (often overlooked)

If the model's output needs to be valid JSON / XML / regex-conformant / a specific grammar:

- **`outlines`** — regex + Pydantic + JSON-schema-constrained generation. Works with vLLM as a backend.
- **`xgrammar`** — faster, GPU-accelerated grammar. Newer.

Add to the endpoint, don't rely on prompt engineering alone.

## Monitoring

For any production endpoint, set up:

- **Throughput + latency p50/p95/p99** — Prometheus + Grafana, or the provider's built-in dashboard.
- **Input / output logging** — to a dataset on the Hub (PRIVATE!) for future fine-tuning data. `datasets.Dataset.push_to_hub` with rate-limiting.
- **Content filter** — Llama Guard 3 / Prompt Guard in front of user input for public endpoints.

## Cost heuristics

- A 7B model on a single L4 (24 GB) serves ~20 rps at short prompts, fp16 KV cache.
- vLLM's PagedAttention is essential for batching — don't compare against naive `model.generate()` baselines.
- Serverless cold-starts add $0 base cost but ~10–30s latency on first request. For chat, pre-warm with `min_containers=1`.

## When to skip a serving layer entirely

- Research deliverable is a model card + eval numbers → don't build serving.
- One-off batch inference over a static dataset → just run `vllm generate ...` in a Modal/RunPod job.
- Private use by 1–5 people → they can run vLLM locally.
