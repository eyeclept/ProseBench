# Score analysis

`analyze.py` reads `instances.csv` and `runs.csv` from `--scores`. These files use the schema in `bench/score/score_runs.py`. It writes Markdown tables and six PNG figures to `--out`. Figures show precision and recall for each rule, plus cost against F1.

Generate sample data and analyze it from the repository root:

```sh
/home/eyeclept/Documents/School/DataMining-645/Project/.venv/bin/python -m bench.analysis.fixtures --out synthetic_scores
/home/eyeclept/Documents/School/DataMining-645/Project/.venv/bin/python -m bench.analysis.analyze --scores synthetic_scores --out analysis_out
```

The routing table includes Wilson lower-bound thresholds of 0.70, 0.90, and `--min-lower` (default 0.80). Routed Ornith runs appear in a separate table. The main Ornith column excludes them unless you pass `--include-routed`. Cost counts API charges, not hardware costs. Claude cost is a list-price equivalent under subscription.

To check hand-scoring agreement, fill the `owner_label` column in the worksheet from `bench/score/diff_report.py`. Use `TP`, `FN`, `FP`, `TN`, or `correct` and `incorrect`. The command joins rows to scorer labels by model, run, and instance. It prints Cohen's kappa, a paired-row bootstrap 95% interval, and PASS at kappa 0.7 or higher:

```sh
/home/eyeclept/Documents/School/DataMining-645/Project/.venv/bin/python -m bench.analysis.kappa --worksheet scores/hand_review.csv --instances scores/instances.csv
```

Test the synthetic structure with:

```sh
/home/eyeclept/Documents/School/DataMining-645/Project/.venv/bin/python -m pytest bench/analysis/tests
```
