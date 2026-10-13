# Finding the Minimum Viable Model for Rule-Governed Prose Editing

Richard Baldwin

Department of Computer Science, Frostburg State University

COSC-645: Data Mining

Dr. Chung-Chi (Edwin) Huang

October 12, 2026

## The Project

`ProseCleanup` is a local prose-editing tool. I build it to replace routine use of `no-ai-slop`. That standard is a 16-rule editing skill I wrote and run daily. The tool sends each rule to a language model on its own. No single model handles the whole document in one call.

The design question is which model each rule needs. It is the cheapest one that still applies that rule correctly and consistently.

Over summer 2026 I ran a first attempt (Baldwin, 2026a). It used 16 one-shot queries against 8 models, 128 runs, hand-scored 0 to 2. It produced a usable tier ranking. Three defects limit what it can support.

Every cell is a single sample, so no cell has a variance estimate. One query rerun three times against Granite 4.1 8B split one pass and two fails on identical input. The three models served through Ollama likely ran at a 4,096-token context window. The harness never sends `num_ctx` on the wire. And 78% of every prompt was harness scaffolding.

This semester rebuilds that measurement so its results survive scrutiny. The research question is narrow and falsifiable. What is the smallest, cheapest model that applies a given `no-ai-slop` rule correctly and consistently?

`ProseCleanup` already decomposes. It calls one model per rule rather than one model over a whole document. This project measures that production shape. Daily use of the full 16-rule skill shows a repeated pattern. A model applies the mechanical rules and skips the ones that need judgment. Those skipped rules must be requested one at a time.

The matrix below does not re-test that observation. It measures which model each already-isolated rule needs. The week-4 proposal used a different open-weight roster (Baldwin, 2026c). This plan keeps the method and replaces the models. Claude controls are the 5.5 line. Open-weight columns now pair Chinese and European labs at the same hardware rungs.

## Method

**Scope.** Rules 1 through 5 of `no-ai-slop`: banned words and phrases, padded negation, redundant antonym trailers, non-keyboard characters, and intensifiers. These five fail most often in my daily use of the standard. The remaining eleven are out of scope. The report will say so.

**Paired constructs.** The v1 suite planted one violation per query. Nine of sixteen queries then scored a clean 2 out of 2 across every tier. Version 2 pairs every planted violation with a surface-identical instance that must not change.

Rule 1 pairs two phrases. "significantly streamlines the workflow" must be cut or replaced with a real number. "statistically significant (p = .003)" must survive. Rule 2 pairs a windup clause that loses nothing on deletion against a negation that carries a checkable fact. Rule 5 pairs an intensifier standing in for a number present in the text against one with no number available. Inventing a number in that second case would violate the standard's accuracy rule.

Pairing converts each rule from an ordinal score into a confusion matrix: true positive, false negative, false positive, true negative. That yields precision and recall per rule per model. It also makes over-application visible. Over-application is the failure mode the tool suffers from. Version 1 had no way to see it.

**Invocation.** Every call sends exactly one rule's text plus one passage. That matches `ProseCleanup`'s production shape. No call asks a model to apply more than one rule. Each passage carries violations of all five rules.

A call scoped to one rule can still touch a different rule's catalogued instance. It can also edit text that carries no catalogued violation. Either counts as a collateral edit. I score collateral-edit rate alongside precision and recall. Decomposition narrows scope creep. It does not remove it by itself.

**Corpus.** Three source essays in unrelated fields: cybersecurity, power systems, and botany. I generated each from the bare prompt "generate me a 1600 word essay about X" against `openai/gpt-oss-120b` through OpenRouter. No system prompt. No conversation history. The three run 1,715, 2,289, and 2,267 words. Those files already sit in `Essays/gpt-oss-120b/`.

Grok 4.6 then makes two passes over each, through my existing xAI OAuth subscription. Grok is not a scored column, so neither writing step contaminates a measured one.

The generator is a pinned OpenRouter identifier. I record the model behind each essay. It cannot change between essays. That choice also sets how much native Rule 4 material the corpus carries. `gpt-oss-120b` produced 422 non-keyboard characters across its three essays. They span 12 codepoints: non-breaking hyphens, dashes, curly quotes, scientific subscripts. The rejected candidate, `meta-llama/llama-4-maverick`, produced zero across 4,843 words on the same three prompts.

The first Grok pass is an inventory. Generated prose already violates these five rules on its own. An unlabeled violation in the base text would count as scope creep when a model correctly fixes it. So Grok catalogues every native instance of rules 1 through 5 already present. It records rule number, sentence, and classification before I add anything.

The second pass injects the paired constructs the inventory does not already supply. The must-not-change halves come first. Generated prose has no reason to contain them.

The combined catalogue is the answer key. It exists before any scored model sees the text. I tag each entry native or planted. GPT-6.1 Sol (`openai/gpt-6.1-sol`) audits each finished essay against the key. It confirms catalogued violations are present and flags anything the key missed. I hand-check every disagreement before the essay enters the scored corpus.

Both corpus models sit outside the measured roster. The auditor also comes from a different lab than the injector, so it does not grade its own work. I exclude Claude Opus 5.5 from the audit even though it is the strongest available reader. A scored control that certifies the answer key cannot be graded against it cleanly. A pilot run through Ornith precedes the audit to supply concrete failure examples.

**Roster.** Six open-weight columns and three Claude 5.5 controls. Open columns sit on four hardware rungs. Two of those rungs carry a Chinese model and a European model side by side. Most current open-weight releases at these sizes come from Chinese labs. Mistral Small 4 and Mistral Large 4 are the European counterparts at the single-GB10 rung and the 1T cloud rung.

Anthropic does not publish parameter counts. The Claude placements below are size-class estimates. I use them to sit each control next to an open column. They are not disclosed sizes.

| Rung | Open model | Lab | Total / active | GB10 boxes | OpenRouter id | API price per million tokens |
|---|---|---|---|---|---|---|
| T1, 35B class | Qwen3.6 35B-A3B | Alibaba | 35B / 3B | 1 | `qwen/qwen3.6-35b-a3b` | $0.10 / $0.95 |
| T2, 1 GB10 | Qwen3.8 Flash | Alibaba | 125B / 6B, plus 51B n-gram | 1 | `qwen/qwen3.8-flash` | $0.15 / $0.47 |
| T2, 1 GB10 | Mistral Small 4 | Mistral | 119B / 6B | 1 | `mistralai/mistral-small-2603` | $0.15 / $0.60 |
| T3, 2 GB10 | GLM-5.3-Flash | Z.ai | 320B / 18B | 2 | `z-ai/glm-5.3-flash` | $0.026 / $0.90 |
| T4, cloud 1T | MiMo-V2.6-Pro | Xiaomi | >1T | n/a | `xiaomi/mimo-v2.6-pro` | $0.44 / $0.87 |
| T4, cloud 1T | Mistral Large 4 | Mistral | 1.05T / 52B | n/a | `mistralai/mistral-large-4-0` | $0.68 / $2.09 |
| Control, T1 class | Claude Haiku 5.5 | Anthropic | undisclosed (35B-class estimate) | n/a | `anthropic/claude-haiku-5.5` | $0.10 / $0.50 |
| Control, T3 class | Claude Sonnet 5.5 | Anthropic | undisclosed (1-2 GB10, ~380B estimate) | n/a | `anthropic/claude-sonnet-5.5` | $2.00 / $10.00 |
| Control, T4 class | Claude Opus 5.5 | Anthropic | undisclosed (1T-class estimate) | n/a | `anthropic/claude-opus-5.5` | $4.00 / $20.00 |

Prices are OpenRouter list prices fetched 2026-10-12. Haiku 5.5 is $0.10 / $0.50 for prompts under 100,000 tokens. Scored calls stay under that cliff. Mistral Small 4 reports 6B active parameters, 8B if embeddings and the output layer are counted (Mistral AI, 2026a). Qwen3.8 Flash on OpenRouter is the production SKU for the Qwen3.8-Flash-Next weights (Qwen Team, 2026a). Flash-Next is 125B total with 6B active, plus 51B n-gram embedding and 4B multi-token prediction.

Ornith is the model I currently run in production. It ran the first full matrix in the T1 column. I then moved the T1 column in full to Qwen3.6 35B-A3B (`qwen/qwen3.6-35b-a3b`) for the reasoning-level comparison. Qwen3.6 is the same 35B total, 3B active class, with 262,144 tokens of context. The Ornith results are archived and not scored.

Working pairings, not findings. I treat GLM-5.3-Flash as a Sonnet 5.5-class open model, a step weaker. I treat MiMo-V2.6-Pro as an Opus 5.5-class open model, also a step weaker. That gap is the present difference between US frontier labs and Chinese open-weight labs. The matrix tests both pairings on this editing task.

Mistral Large 4 is the European 1T example next to MiMo. Mistral Small 4 plays the same role next to Qwen3.8 Flash at one GB10.

Mistral published Large 4 as an API preview on 6 October 2026. Weights are due 27 October 2026 (Mistral AI, 2026b). The final report is due week 15. Scoring starts on the API now. The hardware-cost axis for Large 4 stays analytic until the weights land.

**Design.** Three passages times three repeat runs per cell separates item variance from sampling variance. Version 1 conflated the two. The base matrix is 5 rules times 3 passages times 3 repeats, or 45 runs per model. Rule 3's second prompt framing adds 9 more, for 54 runs per model. Each of the nine models runs twice: once at its lowest reasoning level and once at high. That gives 18 scored columns and 972 runs.

At a 4,000-input / 3,100-output token budget, OpenRouter list prices project about $7.55. About $6.40 of that falls on the Claude controls. My existing Claude subscription covers those calls. The budget excludes reasoning traces and harness overhead. The pilot measures both, and I re-project the cost from those numbers.

**Scoring.** The scoring rubric is a hybrid. Rule 4 uses deterministic checks. A codepoint scan finds non-keyboard characters. A protected-diacritic check keeps real names intact. A clause parse checks each em-dash replacement. A comma-splice check catches a bad swap.

Rules 2, 3, and 5 need a judge for the interpretive half. Grok 4.6 serves as judge, off the scored roster. I validate it against a stratified 20% subset I score by hand. I report agreement as Cohen's kappa.

An LLM compiles a before/after diff per item to speed the hand-scoring pass. It only extracts and formats the change. It never scores or comments on correctness. I spot-check its diffs against raw output to confirm nothing gets elided.

Rule 3 runs under two prompt framings. One states the standard's escalation instruction verbatim. The other makes escalation mechanically easy. The comparison separates prompt-design failures from capability failures.

**Controlled environment.** Every run executes inside a container. The image pins a harness version, empty context files, no skills, no plugins, and one short system prompt identical across models. Firecrawl stays connected. That matches `ProseCleanup`'s production environment, where it verifies assertions and reduces hallucination.

Rules 1 through 5 are self-contained. Every fact a call needs to satisfy the rubric sits in the passage already. A compliant model has no reason to call search. I log and flag any call that does. A search result that changes between the three repeats of the same cell would confound sampling variance with network variance.

Measured on the development workstation, the default harness injects 27,792 tokens of context for a six-token prompt. The container's pinned configuration, with only Firecrawl attached, cuts that to 16,382 tokens per call. Each run also stops after 600 seconds, so a search loop cannot run unbounded.

Each model runs at two reasoning levels. The first is the minimum each model permits, verified per model. Haiku 5.5 and Sonnet 5.5 accept `off`. Opus 5.5 at `off` omits the effort setting and gets the provider's higher default, so it runs at `low`. Mistral Small 4 accepts `reasoning_effort=none`. OpenRouter makes GLM-5.3-Flash reasoning mandatory and lists only `low`, `high`, and `max`. I set `minimal`, which most likely reaches the provider as `low`. The second level is `high` for every model. The comparison reports, per model, the change in quality and in price between the two levels.

**Cost model.** The cost model has two axes. Per-token API cost comes from the harness's own usage accounting. That accounting reports list-price cost even on subscription-routed calls. I model hardware cost from published specifications: unit price and memory ceiling per box, quantized weight size per model, and published throughput. The hardware axis is analytic. The report will label it as such.

T1 and T2 both fit one GB10. Total parameters, active parameters, and box count are three different axes. Each claim in the report will say which axis it uses.

## Tentative Schedule

Status on 12 October 2026. I submitted the week-4 plan. The three `gpt-oss-120b` source essays exist. Violation injection, the answer-key audit, the container, and the scored matrix have not started. The mid-term report is due next week.

| Week | Dates | Milestone |
|---|---|---|
| 4 | Sep 14-20 | Initial plan submitted |
| 5 | Sep 21-27 | Three source essays generated |
| 6-7 | Sep 28-Oct 11 | Roster revised after new model releases |
| 8 | Oct 12-18 | Violations injected and audited. Container built. Nine endpoints verified. Thinking control confirmed per model |
| 9 | Oct 19-25 | Mid-term progress report submitted. Pilot run on one passage. Rubric calibrated |
| 10 | Oct 26-Nov 1 | Progress meeting. Full matrix started. Mistral Large 4 weights expected 27 Oct |
| 11 | Nov 2-8 | Matrix completed. Human scoring of the validation subset. Judge agreement computed |
| 12 | Nov 9-15 | Hardware and API cost models built |
| 13 | Nov 16-22 | Analysis: per-rule precision and recall, collateral-edit rate, cost per correct edit |
| 14 | Nov 23-29 | Final report drafted. Demonstration video recorded |
| 15 | Nov 30-Dec 6 | Final report and implementation submitted |

## Resources

Models reach the container through two paths. OpenRouter serves the commercial open-weight columns, including the T1 column. My Claude subscription, logged in through OAuth inside the container, serves the three Claude 5.5 controls. The corpus passes and the judge reach Grok 4.6 through my xAI OAuth subscription, outside the container.

Scoring, analysis, and plotting use Python 3.14 with pandas, scipy, and statsmodels for Wilson intervals and paired significance tests. The project repository holds the corpus, the container definition, the runner, the rubrics, and every raw run log.

## Anticipated Problems

**Planted violations may be easier than naturally occurring ones.** This defeated the v1 suite through three revision rounds. Tagging every answer-key entry native or planted converts the worry into a measurement. I compare per-rule recall on violations the generator produced unprompted against recall on the ones Grok injected. A large gap quantifies how much the planted set flatters the models. The report carries both numbers.

Three further mitigations apply. The answer key fixes ground truth before any scored model runs. The audit then compares the essay against a record made in advance. GPT-6.1 Sol audits every essay from outside the scored roster. I hand-check each disagreement.

The paired must-not-change instances cannot be cleared by pattern-matching on the planted form alone. An easy violation still costs a model points if it over-applies.

**Judge agreement may be too low to use.** The 20% hand-scored subset came to 2,355 instances on the full matrix, so I replaced it. Two AI raters, Grok 4.6 and GPT-6.1 Sol, label every instance blind to the scorer and to each other. Kappa below 0.7 between the raters, or between a rater and the scorer, marks a rule whose labels I cannot use. This is agreement among automated raters, not human validation. The report states that limit.

**Mistral Large 4 weights may slip.** Scoring does not wait on the weight files. The API column (`mistralai/mistral-large-4-0`) is live. If weights miss the 27 October date, the hardware-cost line for Large 4 stays labeled analytic. The scored quality column does not depend on the weight files.

**Thinking-mode asymmetry.** The lowest level differs by model, so a uniform low setting is unreachable. The policy is the minimum each model permits, plus `high` for all. I publish the levels as a per-model table. I record reasoning tokens in a separate cost column.

## Final Delivery

The final delivery has three parts. A report covering the measurement and its conclusion about the minimum viable tier. A public repository with the container, the runner, the corpus and answer key, every raw run log, and the analysis notebooks. And a demonstration video.

The practical output is a routing table. It maps each editing rule to the cheapest model tier that applies it reliably. `ProseCleanup` consumes that table directly.

**Project repository:** https://github.com/eyeclept/ProseBench

## References

Anthropic. (2026a). *Introducing Claude Haiku 5.5*. https://www.anthropic.com/claude-haiku-5-5

Anthropic. (2026b). *Claude Sonnet 5.5*. https://openrouter.ai/anthropic/claude-sonnet-5.5

Anthropic. (2026c). *Claude Opus 5.5*. https://openrouter.ai/anthropic/claude-opus-5.5

Baldwin, R. (2026a). *Six-tier LLM capability boundaries for an applied academic prose-editing tool* [Unpublished course paper]. COSC-645: Data Mining, Frostburg State University.

Baldwin, R. (2026b). *ProseCleanup design document* [Unpublished internal documentation].

Baldwin, R. (2026c). *Finding the minimum viable model for rule-governed prose editing: An initial plan* [Unpublished course submission]. COSC-645: Data Mining, Frostburg State University.

Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement, 20*(1), 37-46. https://doi.org/10.1177/001316446002000104

Mirzadeh, I., Alizadeh, K., Shahrokhi, H., Tuzel, O., Bengio, S., & Farajtabar, M. (2024). *GSM-Symbolic: Understanding the limitations of mathematical reasoning in large language models*. arXiv. https://arxiv.org/abs/2410.05229

Mistral AI. (2026a). *Introducing Mistral Small 4*. https://mistral.ai/news/mistral-small-4/

Mistral AI. (2026b). *Mistral Large 4*. https://docs.mistral.ai/models/mistral-large-4

OpenAI. (2026). *GPT-6.1 Sol*. OpenRouter. https://openrouter.ai/openai/gpt-6.1-sol

OpenRouter. (2026). *Models API* [Data set]. https://openrouter.ai/api/v1/models

Qwen Team. (2026a). *Qwen3.8-Flash-Next* [Model card]. Hugging Face. https://huggingface.co/Qwen/Qwen3.8-Flash-Next

Qwen Team. (2026b). *Qwen3.6 35B A3B*. OpenRouter. https://openrouter.ai/qwen/qwen3.6-35b-a3b

Qwen Team. (2026c). *Qwen3.8 Flash*. OpenRouter. https://openrouter.ai/qwen/qwen3.8-flash

Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association, 22*(158), 209-212. https://doi.org/10.1080/01621459.1927.10502953

xAI. (2026). *Grok 4.6*. OpenRouter. https://openrouter.ai/x-ai/grok-4.6

Xiaomi. (2026). *MiMo-V2.6-Pro*. OpenRouter. https://openrouter.ai/xiaomi/mimo-v2.6-pro

Z.ai. (2026). *GLM-5.3-Flash* [Model card]. Hugging Face. https://huggingface.co/zai-org/GLM-5.3-Flash
