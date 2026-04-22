# `LEARNINGS.md` — the decision log

Run research as a **staged pipeline with explicit decision points**. Every major decision — model choice, CV strategy, data cutoff, hyperparameter, scope change — is logged in `LEARNINGS.md` at the project root.

This file is **not** a changelog. It's not a README. It's a live, mostly-append-only record of *why things are the way they are*, so that future-you or a collaborator doesn't re-litigate settled questions.

## When to write to it

Prompt the user to log a decision when any of these happen:

- Picking a model family (e.g. "method A over method B because <property> matters for our data").
- Choosing a CV strategy (e.g. "block CV — naive random split leaks structure").
- Fixing a bug that reveals something non-obvious about the data or library.
- A paper suggests approach X, you chose Y — record *why*.
- A sandbox dry-run uncovered a surprise — record the surprise and the fix.
- User says "actually let's switch to …" — capture the pivot + reason.

Do NOT log:
- Routine code edits.
- Typo fixes.
- "Ran experiment, got number" — that goes in `runs/<ts>/metadata.json`.

## Format

Prepend to the file (newest first), dated, with a short heading. Structure loosely:

```md
# LEARNINGS

## YYYY-MM-DD — <short decision headline>
**Decision:** <what was chosen>
**Why:** <the reason, grounded in data or literature, not vibes>
**Alternatives considered:** <what was rejected and why>
**Reference:** <paper / doc / issue link; point at literature/markdown/*.md>
**Next:** <the immediate follow-up action, if any>
```

Worked example:

```md
## 2026-04-22 — Switched model family from <A> to <B>
**Decision:** Use <B> for the main encoder.
**Why:** <A>'s training was unstable on this data shape (NaN loss in 3/5 seeds at step ~400). <B> is stable under the same config and supports the inductive generalization that our eval protocol requires.
**Alternatives considered:** <A> (unstable), <C> (wrong inductive bias), plain MLP baseline (already at benchmark floor).
**Reference:** <Author, Year>, see literature/markdown/<slug>.md.
**Next:** re-run scripts/05_model.py with configs/base.yaml updated.
```

## Checkpoint cadence

At every stage boundary (end of stage 1, 2, 3, 4), the skill should ask:

> "Anything from this stage to log in LEARNINGS.md? (key decisions, surprises, pivots)"

Don't be annoying about it. One prompt per stage, skip if user says "no."

## Coupling with runs/

`LEARNINGS.md` captures the *why*. `runs/<timestamp>/metadata.json` captures the *what + results*. A good LEARNINGS entry links to the run directory it validated against:

```
**Validated by:** runs/2026-04-22T14-03/ — <metric> <value> ± <std> across 5 seeds.
```

## Why this matters for the loop

Stage 1 (literature) reads the field; `LEARNINGS.md` is the project's own accumulated knowledge. After a couple of weeks of work, `LEARNINGS.md` is more useful than re-reading the papers — it already tells you which ideas survived contact with your data.

When a new conversation starts fresh, point Claude at `LEARNINGS.md` first. It's a pre-built context bundle.
