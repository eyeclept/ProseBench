# Rater agreement

Rows rated by all three raters: 22680

Reference = Grok and GPT verdict where they agree. On a split, Jev decides only when confident (P <= 0.1 or P >= 0.9); other splits are unresolved and excluded from scorer-vs-reference rows. A rule passes the reliability gate when scorer vs reference kappa >= 0.7. All labels are automated; there is no human validation.

## Pairwise agreement

| pair                | rule   |     n |   agreement |   kappa |   ci_low |   ci_high |
|:--------------------|:-------|------:|------------:|--------:|---------:|----------:|
| grok vs gpt         | all    | 22680 |       0.966 |   0.935 |    0.931 |     0.94  |
| grok vs gpt         | 1      |  3132 |       0.835 |   0.65  |    0.623 |     0.677 |
| grok vs gpt         | 2      |  1080 |       0.995 |   0.992 |    0.983 |     0.998 |
| grok vs gpt         | 3      |   972 |       0.935 |   0.86  |    0.825 |     0.892 |
| grok vs gpt         | 4      | 15552 |       0.991 |   0.983 |    0.98  |     0.986 |
| grok vs gpt         | 5      |  1944 |       0.977 |   0.948 |    0.932 |     0.962 |
| grok vs jev         | all    | 22680 |       0.909 |   0.827 |    0.82  |     0.834 |
| grok vs jev         | 1      |  3132 |       0.837 |   0.662 |    0.634 |     0.688 |
| grok vs jev         | 2      |  1080 |       0.996 |   0.993 |    0.986 |     0.998 |
| grok vs jev         | 3      |   972 |       0.868 |   0.737 |    0.697 |     0.778 |
| grok vs jev         | 4      | 15552 |       0.91  |   0.824 |    0.815 |     0.833 |
| grok vs jev         | 5      |  1944 |       0.99  |   0.976 |    0.964 |     0.986 |
| gpt vs jev          | all    | 22680 |       0.906 |   0.82  |    0.813 |     0.827 |
| gpt vs jev          | 1      |  3132 |       0.824 |   0.592 |    0.561 |     0.621 |
| gpt vs jev          | 2      |  1080 |       0.997 |   0.995 |    0.988 |     1     |
| gpt vs jev          | 3      |   972 |       0.845 |   0.689 |    0.647 |     0.737 |
| gpt vs jev          | 4      | 15552 |       0.91  |   0.824 |    0.815 |     0.833 |
| gpt vs jev          | 5      |  1944 |       0.978 |   0.95  |    0.935 |     0.965 |
| scorer vs grok      | all    | 22680 |       0.939 |   0.884 |    0.878 |     0.89  |
| scorer vs grok      | 1      |  3132 |       0.825 |   0.646 |    0.619 |     0.672 |
| scorer vs grok      | 2      |  1080 |       0.989 |   0.98  |    0.969 |     0.99  |
| scorer vs grok      | 3      |   972 |       0.87  |   0.73  |    0.686 |     0.773 |
| scorer vs grok      | 4      | 15552 |       0.963 |   0.927 |    0.921 |     0.932 |
| scorer vs grok      | 5      |  1944 |       0.94  |   0.847 |    0.817 |     0.872 |
| scorer vs gpt       | all    | 22680 |       0.935 |   0.877 |    0.871 |     0.883 |
| scorer vs gpt       | 1      |  3132 |       0.792 |   0.538 |    0.505 |     0.567 |
| scorer vs gpt       | 2      |  1080 |       0.992 |   0.985 |    0.974 |     0.994 |
| scorer vs gpt       | 3      |   972 |       0.834 |   0.652 |    0.601 |     0.699 |
| scorer vs gpt       | 4      | 15552 |       0.968 |   0.938 |    0.932 |     0.943 |
| scorer vs gpt       | 5      |  1944 |       0.922 |   0.809 |    0.778 |     0.837 |
| scorer vs jev       | all    | 22680 |       0.881 |   0.773 |    0.765 |     0.781 |
| scorer vs jev       | 1      |  3132 |       0.8   |   0.568 |    0.536 |     0.599 |
| scorer vs jev       | 2      |  1080 |       0.991 |   0.984 |    0.973 |     0.993 |
| scorer vs jev       | 3      |   972 |       0.879 |   0.757 |    0.716 |     0.798 |
| scorer vs jev       | 4      | 15552 |       0.883 |   0.77  |    0.759 |     0.78  |
| scorer vs jev       | 5      |  1944 |       0.935 |   0.834 |    0.804 |     0.861 |
| scorer vs reference | all    | 22038 |       0.95  |   0.905 |    0.899 |     0.91  |
| scorer vs reference | 1      |  2699 |       0.859 |   0.664 |    0.632 |     0.694 |
| scorer vs reference | 2      |  1077 |       0.993 |   0.987 |    0.977 |     0.995 |
| scorer vs reference | 3      |   912 |       0.877 |   0.741 |    0.692 |     0.784 |
| scorer vs reference | 4      | 15435 |       0.969 |   0.939 |    0.934 |     0.944 |
| scorer vs reference | 5      |  1915 |       0.94  |   0.85  |    0.822 |     0.876 |

## Tie-breaks (reference labels decided by Jev)

| rule   |     n |   grok_gpt_split |   split_share |   jev_decided |   unresolved |   jev_sides_grok |   jev_sides_gpt |
|:-------|------:|-----------------:|--------------:|--------------:|-------------:|-----------------:|----------------:|
| all    | 22680 |              767 |        0.0338 |           125 |          642 |               42 |              83 |
| 1      |  3132 |              517 |        0.1651 |            84 |          433 |               20 |              64 |
| 2      |  1080 |                5 |        0.0046 |             2 |            3 |                0 |               2 |
| 3      |   972 |               63 |        0.0648 |             3 |           60 |                2 |               1 |
| 4      | 15552 |              138 |        0.0089 |            21 |          117 |                8 |              13 |
| 5      |  1944 |               44 |        0.0226 |            15 |           29 |               12 |               3 |

## Jev agreement with the Grok+GPT consensus, by Jev confidence

| jev_bucket                   |     n |   share |   agreement_with_consensus |
|:-----------------------------|------:|--------:|---------------------------:|
| confident (P<=0.1 or P>=0.9) | 15452 |   0.705 |                      0.987 |
| uncertain                    |  6461 |   0.295 |                      0.766 |

## Rule 1: FAILS the reliability gate (scorer vs reference kappa 0.664 < 0.7)

Recall is reported as a range across labelers, not a single number.

| model               |   recall_scorer |   recall_grok |   recall_gpt |   recall_low |   recall_high |
|:--------------------|----------------:|--------------:|-------------:|-------------:|--------------:|
| qwen36              |           0.082 |         0.126 |        0.082 |        0.082 |         0.126 |
| qwen38flash         |           0.277 |         0.516 |        0.321 |        0.277 |         0.516 |
| mistral_small4      |           0.113 |         0.252 |        0.17  |        0.113 |         0.252 |
| glm53flash          |           0.245 |         0.22  |        0.132 |        0.132 |         0.245 |
| mimo26pro           |           0.239 |         0.182 |        0.138 |        0.138 |         0.239 |
| mistral_large4      |           0.327 |         0.321 |        0.126 |        0.126 |         0.327 |
| haiku55             |           0.138 |         0.107 |        0.101 |        0.101 |         0.138 |
| sonnet55            |           0.264 |         0.314 |        0.195 |        0.195 |         0.314 |
| opus55              |           0.421 |         0.428 |        0.352 |        0.352 |         0.428 |
| qwen36_high         |           0.019 |         0.057 |        0.019 |        0.019 |         0.057 |
| qwen38flash_high    |           0.176 |         0.321 |        0.17  |        0.17  |         0.321 |
| mistral_small4_high |           0.126 |         0.063 |        0.057 |        0.057 |         0.126 |
| glm53flash_high     |           0.277 |         0.277 |        0.176 |        0.176 |         0.277 |
| mimo26pro_high      |           0.302 |         0.39  |        0.277 |        0.277 |         0.39  |
| mistral_large4_high |           0.296 |         0.314 |        0.226 |        0.226 |         0.314 |
| haiku55_high        |           0.352 |         0.421 |        0.189 |        0.189 |         0.421 |
| sonnet55_high       |           0.491 |         0.491 |        0.252 |        0.252 |         0.491 |
| opus55_high         |           0.421 |         0.56  |        0.333 |        0.333 |         0.56  |

## Recall by labeler

| model               |   recall_scorer |   recall_grok |   recall_gpt |   recall_jev |   recall_reference |
|:--------------------|----------------:|--------------:|-------------:|-------------:|-------------------:|
| qwen36              |           0.155 |         0.16  |        0.151 |        0.202 |              0.152 |
| qwen38flash         |           0.451 |         0.485 |        0.461 |        0.475 |              0.473 |
| mistral_small4      |           0.062 |         0.085 |        0.075 |        0.097 |              0.073 |
| glm53flash          |           0.457 |         0.457 |        0.446 |        0.466 |              0.45  |
| mimo26pro           |           0.483 |         0.476 |        0.469 |        0.47  |              0.472 |
| mistral_large4      |           0.447 |         0.434 |        0.407 |        0.416 |              0.416 |
| haiku55             |           0.215 |         0.208 |        0.214 |        0.212 |              0.205 |
| sonnet55            |           0.497 |         0.467 |        0.463 |        0.488 |              0.46  |
| opus55              |           0.689 |         0.658 |        0.664 |        0.638 |              0.669 |
| qwen36_high         |           0.193 |         0.2   |        0.19  |        0.242 |              0.188 |
| qwen38flash_high    |           0.33  |         0.369 |        0.348 |        0.362 |              0.351 |
| mistral_small4_high |           0.172 |         0.153 |        0.153 |        0.166 |              0.149 |
| glm53flash_high     |           0.557 |         0.562 |        0.554 |        0.556 |              0.556 |
| mimo26pro_high      |           0.639 |         0.653 |        0.638 |        0.639 |              0.648 |
| mistral_large4_high |           0.6   |         0.612 |        0.599 |        0.597 |              0.607 |
| haiku55_high        |           0.672 |         0.683 |        0.659 |        0.664 |              0.675 |
| sonnet55_high       |           0.644 |         0.623 |        0.604 |        0.631 |              0.617 |
| opus55_high         |           0.617 |         0.603 |        0.597 |        0.567 |              0.608 |
