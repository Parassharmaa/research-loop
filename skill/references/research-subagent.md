# Research sub-agent — prompts

Stage 1 of the loop spawns a research sub-agent via `Agent(subagent_type: "Explore")`. Its job is literature mining in isolation, so the main context stays clean.

## Template — paper-to-recipe

```
You are mining the literature for a reproduction task. The user wants to: {{TASK}}.

Deliverables, in this exact order:

1. **Landmark papers** — 2–3 most-cited papers that define this task or introduce the target method. For each:
   - Title, authors, year, arXiv ID, HF Papers URL if available.
   - From sections 3–5 (methodology + experiments, NOT the abstract), extract:
     - Exact datasets used (name, size, splits).
     - Base model(s) used.
     - Training hyperparameters: batch size, learning rate, schedule, steps/epochs, optimizer, precision.
     - Hardware reported (GPU type + count + hours).
     - Headline metric(s) and values.

2. **One canonical reference implementation.** Search GitHub and the HF Hub. Prefer: official author code → widely-forked community repo → HF `trl` / `transformers` example. Report:
   - Repo URL.
   - Entry-point script / command.
   - Framework (Transformers, trl, axolotl, etc.) and version pin if any.
   - Any non-obvious gotchas from the README or issues.

3. **Dataset availability.** For each dataset in (1), report whether it's on the HF Hub and the exact repo ID. If not on the Hub, report the original source and licensing.

4. **Discrepancies.** If the 2–3 papers disagree on method or hyperparameters, flag the disagreement and which one the reference implementation follows.

Return a compact markdown table for (1) and bulleted answers for (2)–(4). No preamble. Under 1000 words total.

Do NOT write training code. Do NOT propose a plan. Just report findings.
```

## Template — dataset investigation

```
Investigate the dataset {{DATASET_ID}} on the Hugging Face Hub.

Report:
1. Row count per split.
2. Columns and types.
3. For text columns: token-length p50/p95/max using the {{TOKENIZER}} tokenizer.
4. For label columns: value distribution.
5. Sample 3 random rows, pretty-printed.
6. License and any usage restrictions from the dataset card.
7. Known issues from the dataset card or discussion tab.

Use HF MCP tools. Do not download the full dataset — stream or sample.
Under 500 words.
```

## Why a sub-agent vs inline

- Keeps the main context free of paper PDFs and repo file dumps.
- Lets you parallelize: spawn two sub-agents for two competing methods, compare results.
- Returns a structured digest, not raw search results.

## Anti-patterns

- Don't ask the sub-agent to "plan the training run." That's your job — you have the user's context.
- Don't let it write code. Research only.
- If it comes back with hedged claims ("the paper *suggests* ~2e-5 learning rate"), ask for the exact quote and section number before trusting it.
