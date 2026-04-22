# Approval template — before submitting a GPU job

At stage 4 of the loop, STOP and paste a message like this to the user. Wait for explicit "yes" / "go" before calling the HF Jobs submit tool.

## Template

```
Ready to submit the training job. Please confirm before I run it.

**Task:** {{ONE_LINE_SUMMARY}}

**Script:** {{PATH_TO_SCRIPT or inline snippet of the trainer kwargs}}

**Base model:** {{HF_MODEL_ID}}
**Dataset:** {{HF_DATASET_ID}} — {{N_ROWS}} rows, {{SPLIT}} split
**Tokenizer max length:** {{MAX_LEN}} (p95 of dataset: {{P95}})

**Training config:**
- LR: {{LR}} ({{SCHEDULE}})
- Batch size: {{BS_PER_DEVICE}} × {{N_DEVICES}} devices × {{GRAD_ACCUM}} accum = **{{EFFECTIVE_BS}} effective**
- Steps / epochs: {{MAX_STEPS_OR_EPOCHS}}
- Precision: {{BF16_OR_FP16}}
- Eval: every {{EVAL_STEPS}} steps on {{EVAL_SET}}
- Save: every {{SAVE_STEPS}} steps, keep last {{SAVE_TOTAL_LIMIT}}

**Infrastructure:**
- Flavor: `{{GPU_FLAVOR}}` ({{N_GPUS}} × {{GPU_MODEL}})
- Timeout: {{TIMEOUT}} (expected wall-time: {{EXPECTED}})
- Estimated cost: ~${{COST}} at listed HF rates

**Outputs:**
- Checkpoints pushed to: `{{HUB_REPO_ID}}` ({{EXISTS_OR_WILL_CREATE}})
- `push_to_hub`: `{{TRUE_OR_FALSE}}`
- Model card: {{WILL_GENERATE_AFTER_RUN or path}}

**Sandbox dry-run result:** {{LOSS_AT_STEP_2}} at step 2 on {{SANDBOX_FLAVOR}} — looks sane / flag concerns

**Reply `go` to submit, or push back on any of the above.**
```

## Why every field matters

- **Effective batch size** — most reproduction failures trace to this being different from the paper.
- **Eval strategy** — without it, you can't tell a broken run from a slow-learning one until it's too late.
- **Save strategy** — without it, a single crash 20 hours in costs the whole run.
- **Timeout** — HF Jobs kills silently. Under-spec'd timeout = the most expensive lesson.
- **Sandbox result** — if you didn't actually run the dry-run, say so and do it first.

## If the user says "just go"

Still show the config. You can skip the "reply go" line if they've preapproved in this session, but never skip the summary — it's the last chance to catch a wrong-dataset or wrong-model typo.
