# Setup — MCP servers and CLIs per provider

The `research-loop` skill is provider-agnostic. Install whichever backends you want to use. At least one is required. HF is recommended regardless because its paper/dataset/model search MCP is useful for stage 1 even if you train elsewhere.

## Hugging Face (recommended — at minimum for paper + dataset search)

Remote HTTP MCP server, no local install:

```bash
claude mcp add --transport http huggingface https://huggingface.co/mcp
huggingface-cli login
```

Tools appear as `mcp__huggingface__*`. Covers: paper search, dataset/model inspection, repo file read/write, HF Jobs submit and logs, Spaces.

See `providers/huggingface.md`.

## RunPod

Official local MCP server over stdio:

```bash
claude mcp add runpod npx '@runpod/mcp-server@latest' \
  -e RUNPOD_API_KEY=rpa_...
```

Get an API key at <https://www.runpod.io/console/user/settings>. Tools cover Pods, Serverless endpoints, templates, network volumes, container registries.

See `providers/runpod.md`.

## Modal

No official MCP server as of this writing. Use the Modal CLI directly via Bash — Claude Code can drive it fine.

```bash
pip install modal                   # latest; pin in your project if needed
modal token new                     # browser auth flow, writes ~/.modal.toml
```

Verify: `modal profile current`. See `providers/modal.md` for the `@app.function(gpu=...)` patterns the skill will generate.

## Lambda Labs / CoreWeave / Together / bare metal

No MCP servers. The skill falls back to SSH + `scp` (Lambda, CoreWeave) or their REST APIs via `curl`/`requests` (Together). For Lambda:

```bash
# ensure you have ssh keys uploaded to Lambda, and an active instance
ssh -i ~/.ssh/lambda.pem ubuntu@<instance-ip>
```

See `providers/lambda.md` for the full submit pattern (rsync code, run tmux + training script, rsync checkpoints back).

## GitHub MCP (optional but recommended)

Code search is how stage 1 finds reference implementations. If you already have `gh` CLI authed, Claude Code can use it via Bash — no MCP needed. If you want richer search, install the GitHub MCP:

```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp
```

(Requires GitHub Copilot. Otherwise rely on `gh search code` + WebFetch.)

## Verify

Inside a Claude Code session:

```
/mcp
```

Should list every server you installed as **connected**. If a server shows **disconnected**, check the relevant API key in env.

## Token hygiene

- Never commit `~/.modal.toml`, `RUNPOD_API_KEY`, or HF tokens.
- Prefer scoped tokens: HF tokens should be read + write, not admin. RunPod supports restricted keys per pod.
- Rotate after any shared-screen demo.
