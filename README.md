# research-loop

A Claude Code skill for ML-engineering work. Distills the workflow from
Hugging Face's [`ml-intern`](https://github.com/huggingface/ml-intern) into a
single skill that drives Claude Code + the official Hugging Face MCP server.

**The loop:**

1. **Literature** — research sub-agent mines papers and reference code first.
2. **Validate** — inspect dataset, tokenizer, sample rows.
3. **Sandbox** — dry-run the trainer on CPU or a tiny GPU slice.
4. **Submit** — approval-gated GPU job on HF Jobs with full config shown.
5. **Ship** — monitor, eval, push to the Hub, write a model card.

## Why not just use `ml-intern`?

`ml-intern` is a standalone CLI with its own agent loop, its own LLM client,
its own sandbox. Most of that duplicates what Claude Code already does
better. The real IP is the **workflow discipline** and the **HF tool
surface** — both of which port cleanly to a skill + MCP server.

Trade-offs:

| | `ml-intern` | `research-loop` skill |
|---|---|---|
| LLM | Anthropic API key or HF inference | Your Claude Code session (any model) |
| Tools | Custom implementations | Claude Code native + HF MCP |
| Sandbox | HF Spaces-hosted (free-tier) | Local Bash / Docker / HF Jobs CPU |
| Loop control | `doom_loop` heuristics | Claude Code's native loop |
| Session history | Saved to a HF dataset | Claude Code's native transcript |

If you need HF-Space-backed remote sandbox execution on HF's dime, use
`ml-intern`. For everything else, this skill is leaner.

## Install

```bash
# 1. clone anywhere, or just download the skill/ directory
git clone https://github.com/Parassharmaa/research-loop.git
cd research-loop

# 2. install the skill into your user Claude config
cp -r skill ~/.claude/skills/research-loop

# 3. install the Hugging Face MCP server
claude mcp add --transport http huggingface https://huggingface.co/mcp

# 4. log in so the MCP can use your HF token
huggingface-cli login
```

Verify:

```
# inside a Claude Code session
/mcp          # should list "huggingface" as connected
```

Then invoke the skill by asking Claude something ML-shaped — "reproduce the
DPO paper on UltraFeedback", "fine-tune llama-3.2-1b on my csv", "benchmark
these 3 embedding models". The skill triggers on the keywords listed in its
`when_to_use` field.

## Skill layout

```
skill/
├── SKILL.md                              # entry point, the 5-stage loop
└── references/
    ├── setup.md                          # HF MCP installation + verification
    ├── hardware-sizing.md                # GPU flavor + timeout tables
    ├── research-subagent.md              # prompts for the literature sub-agent
    └── approval-template.md              # the pre-submission checklist
```

## Requirements

- **Claude Code** ≥ 2.0 (skills + MCP support).
- **Hugging Face MCP server** — hosted at `https://huggingface.co/mcp`, no
  local install needed.
- **`huggingface_hub`** ≥ 1.0 if you want to fall back to direct Python API
  calls when the MCP lacks a capability: `pip install 'huggingface_hub>=1.0'`
  (latest at time of writing: 1.11).
- An HF account with a **write**-scoped token (for `push_to_hub` and Jobs).

## Credits

Workflow inspired by [`huggingface/ml-intern`](https://github.com/huggingface/ml-intern).
This repo contains none of its code — just a distilled prompt that points
Claude Code at the same tool surface.

## License

MIT
