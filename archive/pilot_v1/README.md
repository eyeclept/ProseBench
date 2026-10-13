# Pilot v1 (superseded calibration run)

Runs against the corpus at commit d890824, before the six `replace_with_fact` instances were re-planted.
Scores here do not match the current answer key. Kept as evidence for three harness changes:

- `qwen38flash/R3_P1_r1`: 155 Firecrawl tool calls, 1,390 s, $0.294. Led to `--max-time 600` in `container/omp-run.sh`.
- `mistral_small4/R1_P1_r1`: one of 79 edits lacked `reason`, and the old parser discarded the whole run. Led to per-edit validity (`malformed_edits`).
- `mistral_small4`: 3 of 6 runs failed with OpenRouter `429 Provider returned error`.

Total model-reported spend: $0.4549 (35 runs) plus the $0.0076 smoke run.
