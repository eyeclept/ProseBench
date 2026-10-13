# Smoke results

Prompt: `Reply with the single word: ok`.
Prompt tokens include cached input and cache-write tokens. All costs are US dollars.

| Model | Status | Exit | Final text | Prompt tokens | Reasoning tokens | Cost (USD) | Minimum thinking |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| ornith | pass | 0 | ```json {   "text": "ok" } ``` | 16332 | 0 | 0.00000000 | off |
| qwen38flash | pass | 0 | ok | 16389 | 0 | 0.00029767 | off |
| mistral_small4 | pass (first probe) | 0 | {"response": "ok"} | 16590 | 0 | 0.00249270 | off |
| glm53flash | pass | 0 | {"reply":"ok"} | 15661 | 0 | 0.00109767 | off |
| mimo26pro | pass | 0 | ok | 16255 | 0 | 0.00707266 | off |
| mistral_large4 | pass | 0 | {"ok": true} | 15985 | 0 | 0.00152494 | off |
| haiku55 | needs-login | - | - | - | - | - | unverified |
| sonnet55 | needs-login | - | - | - | - | - | unverified |
| opus55 | needs-login | - | - | - | - | - | unverified |
| qwen36 | pass | 0 | ok | 16587 | 0 | 0.00166050 | off |

Total model-reported cost for the selected successful probes: $0.01414614.

Mistral Small returned `{"response": "ok"}` at `off` on the first smoke call.
That call passed the file as an omp attachment. The corrected stdin call returned
HTTP 429 `Provider returned error`; no retry followed. The other table rows come
from the corrected stdin call. The `off` level is confirmed by the first HTTP 200.
The local Ornith endpoint returned `reasoning_content: null` with
`chat_template_kwargs.enable_thinking=false` in a direct endpoint request.

## Correction (2026-10-13)

The smoke prompt cannot show whether a level is honored, only whether the endpoint accepts it.
GLM-5.3-Flash accepted `off` here, but OpenRouter makes its reasoning mandatory:
`reasoning.enabled=false` and `reasoning.effort=none` return HTTP 400 "Reasoning is mandatory for this endpoint and cannot be disabled".
With omp `--thinking off`, GLM reasoned at its default (pilot Rule 1: 2,812 reasoning tokens; Rule 4: 5,532).
`--thinking minimal` gives 38 reasoning tokens on a counting prompt. `bench/roster.yml` now sets GLM to `minimal`.
The other five OpenRouter columns reported 0 reasoning tokens across both pilots at `off`.

## Claude levels (2026-10-13, after owner login)

Probed with `container/omp-run.sh` on two short reasoning prompts. Haiku 5.5 and Sonnet 5.5 honor `off` (no thinking; 11 and 10 output tokens vs 263 and 227 at `low`). Opus 5.5 accepts `off` but still returns a thinking block, and output at `off` exceeded `low` (511 vs 227 tokens), so `off` omits the effort setting and Anthropic applies its default. `bench/roster.yml` sets Haiku and Sonnet to `off`, Opus to `low`.
