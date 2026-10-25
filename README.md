# ProseBench

ProseBench is the testing harness and data for the COSC-645 project, *Finding the Minimum Viable Model for Rule-Governed Prose Editing*. The project asks: what is the smallest, cheapest model that applies a given `no-ai-slop` rule correctly and consistently? The harness tests rules 1 through 5 with paired items that must change or must stay unchanged.

**Status:** Testing phase complete. All 972 runs are scored and rated. The report has not yet been written. Analysis outputs are generated and await interpretation.

## Repository layout

| Path | Contents |
| --- | --- |
| `bench/` | Corpus pipeline, runner, scorer, and analysis code. |
| `container/` | Pinned omp container and run tools. |
| `runs/` | Raw run records and event logs. |
| `scores/` | Scored instances, rater labels, and caches. |
| `analysis_out/` | Generated tables and plots, not yet interpreted. |
| `archive/` | Discarded pilots and the discarded Ornith matrix. |
| `Essays/` | Source essays. |
| `plan.md` | Revised working plan. |

## Requirements

- Python 3.14 virtual environment with `pandas`, `scipy`, `statsmodels`, and `PyYAML`.
- Podman.
- omp 18.10.3.
- Set `OPENROUTER_API_KEY` in the shell for OpenRouter access.

## Tests

From the repository root, run the test suite:

```sh
python -m pytest bench
```

The suite has 38 tests.

## Guides

- [Corpus pipeline](bench/corpus/README.md)
- [Container setup and runner](container/README.md)
- [Prompt rules](bench/prompts/README.md)
- [Score analysis](bench/analysis/README.md)

`bench/runner/run_matrix.py` drives the run matrix. `container/omp-run.sh` runs one omp call inside the pinned container. `bench/score/score_runs.py` scores the run records. The analysis output files are generated data. They have not yet been interpreted for the report.
