# Provider — Lambda Labs / CoreWeave / Together / bare metal

Grouped together because they share a pattern: **you get a machine, you SSH in, you run things.** No MCP server. The skill drives them via `ssh` + `rsync` + the provider's REST API (if any) for provisioning.

## When to pick each

| Provider | Best for | $/hr (H100) | Notes |
|---|---|---|---|
| **Lambda Labs** | Reliable H100/A100 at predictable prices | ~$2.49 | No egress fees. On-demand can be out-of-stock. 1-click Jupyter. |
| **CoreWeave** | Enterprise runs, multi-node, InfiniBand | ~$3.50+ | Kubernetes-native. SOC2. Needs a sales conversation. |
| **Together AI** | Training-as-a-service (managed) + inference | Managed | You submit a config, they run it. GB200 clusters available. |
| **Vast.ai** | Dirt-cheap spot GPUs | varies wildly | Consumer GPUs, variable quality. Good for sandbox GPU. |
| **Paperspace / Gradient** | Notebook-first workflows | ~$3+ | Getting phased out — check before committing. |

## Lambda — submit pattern

Assumes the user has an on-demand instance or reserves one:

```bash
# 1. Identify the instance (user provides IP + SSH key path, or you call Lambda Cloud API)
HOST=ubuntu@<ip>
KEY=~/.ssh/lambda.pem

# 2. Sync code
rsync -az --exclude '.git' --exclude 'wandb/' --exclude '__pycache__' \
    ./ "$HOST:~/work/"

# 3. Set up env (first run only) — capture in a setup.sh the skill writes
ssh -i $KEY $HOST 'bash -s' <<'EOF'
cd ~/work
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
EOF

# 4. Launch in tmux so SSH drops don't kill it
ssh -i $KEY $HOST "cd ~/work && tmux new -d -s train \
    'source .venv/bin/activate && \
     python train.py --output_dir outputs 2>&1 | tee train.log'"

# 5. Monitor
ssh -i $KEY $HOST "tail -f ~/work/train.log"
#   or: ssh -i $KEY $HOST "tmux capture-pane -t train -p | tail -50"

# 6. Pull checkpoints back OR push_to_hub from the instance
ssh -i $KEY $HOST "cd ~/work && huggingface-cli upload user/model outputs"
```

## CoreWeave — submit pattern

CoreWeave is Kubernetes-native. You either:

1. **Use their managed training product** (submit a YAML job spec via `kubectl` against their cluster). Good fit for the skill — treat it like HF Jobs but with a different CLI.
2. **SSH into a Virtual Server node** — same pattern as Lambda above.

If the user has a CoreWeave cluster already, ask which mode, and ask for `kubectl` context or the Virtual Server IP.

## Together AI — training API

Together exposes a fine-tuning API:

```bash
curl -s -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.xyz/v1/fine-tunes \
  -d '{
    "training_file": "file-abc",
    "model": "meta-llama/Meta-Llama-3.1-8B",
    "n_epochs": 3,
    "learning_rate": 1e-5,
    "lora": true
  }'
```

Less flexibility than submitting a custom script, but zero infrastructure work. Good for standard SFT/LoRA on supported base models.

## GPU flavor reference (cross-provider)

See `../hardware-sizing.md` — the "needed VRAM" column applies regardless of provider. Then pick the closest SKU your chosen provider offers.

## Gotchas

- **Lambda on-demand stockouts** — H100 frequently unavailable. Always check availability before committing to a deadline.
- **CoreWeave onboarding** — enterprise contracts, not self-serve. If the user doesn't already have access, route to a self-serve provider.
- **Vast.ai reliability** — individual hosts can go offline mid-run. Only use for sandbox or non-critical work, and checkpoint aggressively.
- **Egress fees** — Lambda has none; AWS/GCP/Azure will bill you for checkpoint download. Factor in.
- **Instance left running** — same as RunPod, a forgotten H100 is expensive. Approval template must remind teardown.

## When to pick one of these over HF/RunPod/Modal

- **Multi-node / InfiniBand** training (70B+ pretraining): CoreWeave or Lambda reserved clusters.
- **Hands-on debugging** with SSH, `nvtop`, `py-spy`: anything SSH-able.
- **Fully-managed fine-tuning** with no code: Together.
- **Long-running persistent environments** for research (weeks-long runs, custom kernels, custom CUDA): Lambda reserved or CoreWeave.
