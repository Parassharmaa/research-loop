# Hugging Face MCP — setup

The `research-loop` skill relies on the official HF MCP server for Hub access (papers, datasets, models, Jobs). Install it once per machine.

## Install (Claude Code)

```bash
claude mcp add --transport http huggingface https://huggingface.co/mcp
```

Then log in via the HF CLI so the MCP can use your token:

```bash
huggingface-cli login
```

Or set `HF_TOKEN` in your shell profile. Get a token at <https://huggingface.co/settings/tokens> — scope: **read + write** (write is needed for `push_to_hub` and Jobs).

## Verify

Inside Claude Code:

```
/mcp
```

You should see `huggingface` listed as connected. Tools will appear as `mcp__huggingface__*` (exact names vary by MCP version — use `/mcp` to list).

## Minimum tool surface the skill expects

Names differ across MCP versions, but the skill assumes the following *capabilities* are reachable. Map them to whatever the current HF MCP exposes:

| Capability | Used in stage |
|---|---|
| Search papers (arXiv / HF Papers) | 1 — literature |
| Fetch paper full text or sections | 1 — literature |
| Search / inspect datasets on the Hub | 2 — validation |
| Search / inspect models on the Hub | 2 — validation |
| Read files from a Hub repo | 1, 2 |
| Submit HF Jobs (CPU + GPU) | 3, 4 |
| Read HF Jobs logs and status | 5 — ship |
| Create / update Hub repos, push files | 5 — ship |

If any are missing in your installed version, fall back to direct HTTP via `huggingface_hub` Python SDK in a Bash step — but prefer MCP so the user sees approval prompts.

## Other MCP servers that play nicely

- **GitHub MCP** (`claude mcp add github ...`) — for finding reference implementations in stage 1, code search in stage 3.
- **Filesystem MCP** — usually not needed; Claude Code's native tools cover this.
