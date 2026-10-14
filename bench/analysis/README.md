# Score analysis

`analyze.py` reads `instances.csv` and `runs.csv` from `--scores`. These files use the schema in `bench/score/score_runs.py`. It writes Markdown tables and six PNG figures to `--out`. Figures show precision and recall for each rule, plus cost against F1.

Generate sample data and analyze it from the repository root:

```sh
/home/eyeclept/Documents/School/DataMining-645/Project/.venv/bin/python -m bench.analysis.fixtures --out synthetic_scores
/home/eyeclept/Documents/School/DataMining-645/Project/.venv/bin/python -m bench.analysis.analyze --scores synthetic_scores --out analysis_out
```

The routing table includes Wilson lower-bound thresholds of 0.70, 0.90, and `--min-lower` (default 0.80). Cost counts API charges, not hardware costs. Claude cost is a list-price equivalent under subscription.

The reasoning-effect table compares each model's min-reasoning and high-reasoning runs on quality and API cost. One row is one model and one rule, plus an all-rules headline.

To check hand-scoring agreement, fill the `owner_label` column in the worksheet from `bench/score/diff_report.py`. Use `TP`, `FN`, `FP`, `TN`, or `correct` and `incorrect`. The command joins rows to scorer labels by model, run, and instance. It prints Cohen's kappa, a paired-row bootstrap 95% interval, and PASS at kappa 0.7 or higher:

```sh
/home/eyeclept/Documents/School/DataMining-645/Project/.venv/bin/python -m bench.analysis.kappa --worksheet scores/hand_review.csv --instances scores/instances.csv
```

Test the synthetic structure with:

```sh
/home/eyeclept/Documents/School/DataMining-645/Project/.venv/bin/python -m pytest bench/analysis/tests
```

## Rater agreement

Three blind AI raters label every scored instance through `bench/score/ai_rater.py`. The raters are Grok 4.6, GPT-6.1 Sol, and TypeSafe Jev 1.13. Run each rater, then compare:

```sh
.venv/bin/python -m bench.score.ai_rater --rater grok
.venv/bin/python -m bench.score.ai_rater --rater gpt
.venv/bin/python -m bench.score.ai_rater --rater jev --workers 10
.venv/bin/python -m bench.analysis.rater_agreement
```

The report goes to `analysis_out/rater_agreement.md`. It gives kappa and percent agreement for each pair of labelers, overall and per rule. The reference label is the Grok and GPT verdict where they agree. Where they disagree, Jev's vote decides. The report counts these tie-breaks per rule. It also shows Jev's agreement with the Grok and GPT consensus, split by Jev confidence. All labels are automated, so the report is not human validation.
