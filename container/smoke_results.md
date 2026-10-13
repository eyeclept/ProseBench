# Smoke results

Prompt: `Reply with the single word: ok`.
Prompt tokens include cached input and cache-write tokens. All costs are US dollars.

| Model | Status | Exit | Final text | Prompt tokens | Reasoning tokens | Cost (USD) | Minimum thinking |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| qwen36 | pass | 0 | ok | 16551 | 0 | 0.00165690 | off |
| qwen36_high | pass | 0 |   ok | 16608 | 0 | 0.00169050 | high |
| qwen38flash_high | pass | 0 | ok | 16389 | 0 | 0.00260499 | high |
| mistral_small4_high | pass | 0 | ```json {"response": "ok"} ``` | 16532 | 0 | 0.00251280 | high |
| glm53flash_high | pass | 0 | ok | 15594 | 0 | 0.00234010 | high |
| mimo26pro_high | pass | 0 | ok | 16272 | 0 | 0.00724188 | high |
| mistral_large4_high | pass | 0 | ok | 15950 | 0 | 0.01465816 | high |
| haiku55_high | pass | 0 | {"result": "ok"} | 24291 | 0 | 0.00486330 | high |
| sonnet55_high | pass | 0 | {"result": "ok"} | 24292 | 0 | 0.09727000 | high |
| opus55_high | pass | 0 | {"result": "ok"} | 24290 | 0 | 0.19684400 | high |

Total model-reported cost: $0.33168263.

