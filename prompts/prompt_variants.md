# Prompt variants

Use the same case, model, and generation settings for both versions. Save the exact prompts, model identifier, run date, and raw outputs in the review sheet or an adjacent run archive.

## Baseline

> Complete the following task: `{task}`

## Structured

> **Task:** `{task}`
>
> **Reference context:** `{reference_context}`
>
> **Constraints:** `{constraints}`
>
> Answer only from the information available in the task. If a fact is missing, say so instead of inventing it. Follow the requested output format. Before responding, check that the answer satisfies every listed constraint.

These are comparison templates, not measured results. A structured prompt is not assumed to perform better; the review report should determine what happened for the selected model and settings.
