# Synthetic data — when you don't have a dataset yet

Insert this stage between 1 (literature) and 2 (validate) if the user is starting from prompts only, or has < 1k labeled examples.

## Decision: buy, borrow, or make?

| Starting point | Recommended |
|---|---|
| Have a similar public dataset | Start there, augment later. |
| Have prompts but no outputs | Distill from a strong teacher (GPT-4.x / Claude / Llama-3.3-70B). |
| Have inputs but no labels | LLM-as-annotator with 2–3 models voting. |
| Have nothing, only a task definition | Magpie-style self-prompting + teacher completion. |
| Need preference pairs | Teacher ranks weak-model outputs. |

## Tooling

### `distilabel` (recommended default)

```python
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration, UltraFeedback
from distilabel.models import OpenAILLM

with Pipeline("my-sft-data") as pipeline:
    generate = TextGeneration(
        llm=OpenAILLM(model="gpt-4o"),
        input_batch_size=8,
    )
    rate = UltraFeedback(
        llm=OpenAILLM(model="gpt-4o"),
    )
    generate >> rate

distiset = pipeline.run(dataset=my_prompts)
distiset.push_to_hub("Parassharmaa/my-sft-dataset")
```

Distilabel is batteries-included for: generation, rating, critique, evolution (evol-instruct), preference triplets, structured output. Push directly to the Hub.

### Magpie — self-distillation from base models

No teacher needed. Prompt a base chat model with *just* its template's user-turn start tokens:

```
<|start_header_id|>user<|end_header_id|>\n
```

The model hallucinates a user prompt. Feed that back and collect the assistant response. You now have a `(prompt, completion)` pair from the model's own distribution. Filter for quality.

Implemented in `distilabel` as `MagpieGenerator`.

### LLM-as-judge for preferences

```python
from distilabel.steps.tasks import UltraFeedback

# Given two candidate outputs A and B from weak models,
# ask a strong teacher to pick chosen / rejected.
rater = UltraFeedback(llm=OpenAILLM(model="gpt-4o"))
```

Use 2–3 different teachers and keep only pairs they agree on. ~85 % of human-label quality at 1 % of the cost.

## Quality gates (don't skip)

1. **Dedup** — near-duplicates kill diversity. Use `datasketch` MinHash or embedding-based clustering before training.
2. **Toxicity / PII filter** — `detoxify`, Presidio. Strip PII before pushing.
3. **Length filter** — drop outputs < 10 tokens or > 2× p99 of your real distribution.
4. **Eyeball 50 examples.** Non-negotiable. Synthetic data bugs are invisible from aggregate stats.
5. **Teacher-eval gap.** If your eval metric uses the same model family as your teacher, you may have contaminated eval. Use a different eval-model.

## Preference-pair construction recipes

### Recipe: DPO data from a frozen SFT model

```
1. Sample N=4 responses per prompt from the SFT model with temperature 0.9.
2. Score each with a teacher / reward model.
3. Take chosen = highest score, rejected = random from bottom-50 %.
4. Filter pairs where score_gap < threshold (e.g. 2 on a 1–10 scale).
```

### Recipe: Reasoning data for GRPO

No preferences needed. Just generate many rollouts per prompt and let GRPO's verifiable reward do the work:

```
1. Collect math / code prompts with verifiable answers.
2. That's it — pass to GRPOTrainer with your reward_fn(prompt, completion) → float.
```

## Cost estimation

Rule of thumb: GPT-4.x / Claude costs ~$1–3 per 1k training examples depending on length. A 10k-example SFT set costs ~$20. A 50k-pair preference set with UltraFeedback rating costs ~$150.

Open-source teachers (Llama-3.3-70B via vLLM on a rented H100) are 10–30× cheaper if you're already paying for a GPU.

## Anti-patterns

- **Generating without filtering.** Half your data will be boilerplate LLM slop. Filter first.
- **Teacher == eval model.** Contaminated benchmarks. Use different models for train vs eval.
- **Too narrow a prompt distribution.** Evol-instruct one round minimum.
- **Pushing unfiltered synthetic data to the Hub as public.** PII risk + dataset-card obligations. Start private.
