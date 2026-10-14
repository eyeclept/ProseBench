# Rater agreement

Rows rated by all three raters: 23544

Reference = Grok and GPT verdict where they agree. On a split, Jev decides only when confident (P <= 0.1 or P >= 0.9); other splits are unresolved and excluded from scorer-vs-reference rows. All labels are automated; there is no human validation.

## Pairwise agreement

| pair                | rule   |     n |   agreement |   kappa |   ci_low |   ci_high |
|:--------------------|:-------|------:|------------:|--------:|---------:|----------:|
| grok vs gpt         | all    | 23544 |       0.974 |   0.951 |    0.947 |     0.954 |
| grok vs gpt         | 1      |  3996 |       0.909 |   0.838 |    0.822 |     0.853 |
| grok vs gpt         | 2      |  1080 |       0.995 |   0.992 |    0.983 |     0.998 |
| grok vs gpt         | 3      |   972 |       0.935 |   0.86  |    0.825 |     0.892 |
| grok vs gpt         | 4      | 15552 |       0.991 |   0.983 |    0.98  |     0.986 |
| grok vs gpt         | 5      |  1944 |       0.977 |   0.948 |    0.932 |     0.962 |
| grok vs jev         | all    | 23544 |       0.886 |   0.784 |    0.776 |     0.791 |
| grok vs jev         | 1      |  3996 |       0.715 |   0.489 |    0.463 |     0.514 |
| grok vs jev         | 2      |  1080 |       0.996 |   0.993 |    0.986 |     0.998 |
| grok vs jev         | 3      |   972 |       0.868 |   0.737 |    0.697 |     0.778 |
| grok vs jev         | 4      | 15552 |       0.91  |   0.824 |    0.815 |     0.833 |
| grok vs jev         | 5      |  1944 |       0.99  |   0.976 |    0.964 |     0.986 |
| gpt vs jev          | all    | 23544 |       0.881 |   0.775 |    0.767 |     0.782 |
| gpt vs jev          | 1      |  3996 |       0.698 |   0.446 |    0.419 |     0.471 |
| gpt vs jev          | 2      |  1080 |       0.997 |   0.995 |    0.988 |     1     |
| gpt vs jev          | 3      |   972 |       0.845 |   0.689 |    0.647 |     0.737 |
| gpt vs jev          | 4      | 15552 |       0.91  |   0.824 |    0.815 |     0.833 |
| gpt vs jev          | 5      |  1944 |       0.978 |   0.95  |    0.935 |     0.965 |
| scorer vs grok      | all    | 23544 |       0.895 |   0.801 |    0.793 |     0.808 |
| scorer vs grok      | 1      |  3996 |       0.59  |   0.264 |    0.234 |     0.292 |
| scorer vs grok      | 2      |  1080 |       0.989 |   0.98  |    0.969 |     0.99  |
| scorer vs grok      | 3      |   972 |       0.87  |   0.73  |    0.686 |     0.773 |
| scorer vs grok      | 4      | 15552 |       0.963 |   0.927 |    0.921 |     0.932 |
| scorer vs grok      | 5      |  1944 |       0.94  |   0.847 |    0.817 |     0.872 |
| scorer vs gpt       | all    | 23544 |       0.9   |   0.81  |    0.803 |     0.817 |
| scorer vs gpt       | 1      |  3996 |       0.615 |   0.291 |    0.262 |     0.318 |
| scorer vs gpt       | 2      |  1080 |       0.992 |   0.985 |    0.974 |     0.994 |
| scorer vs gpt       | 3      |   972 |       0.834 |   0.652 |    0.601 |     0.699 |
| scorer vs gpt       | 4      | 15552 |       0.968 |   0.938 |    0.932 |     0.943 |
| scorer vs gpt       | 5      |  1944 |       0.922 |   0.809 |    0.778 |     0.837 |
| scorer vs jev       | all    | 23544 |       0.846 |   0.707 |    0.698 |     0.716 |
| scorer vs jev       | 1      |  3996 |       0.612 |   0.255 |    0.224 |     0.285 |
| scorer vs jev       | 2      |  1080 |       0.991 |   0.984 |    0.973 |     0.993 |
| scorer vs jev       | 3      |   972 |       0.879 |   0.757 |    0.716 |     0.798 |
| scorer vs jev       | 4      | 15552 |       0.883 |   0.77  |    0.759 |     0.78  |
| scorer vs jev       | 5      |  1944 |       0.935 |   0.834 |    0.804 |     0.861 |
| scorer vs reference | all    | 22989 |       0.907 |   0.824 |    0.816 |     0.831 |
| scorer vs reference | 1      |  3650 |       0.612 |   0.284 |    0.252 |     0.315 |
| scorer vs reference | 2      |  1077 |       0.993 |   0.987 |    0.977 |     0.995 |
| scorer vs reference | 3      |   912 |       0.877 |   0.741 |    0.692 |     0.784 |
| scorer vs reference | 4      | 15435 |       0.969 |   0.939 |    0.934 |     0.944 |
| scorer vs reference | 5      |  1915 |       0.94  |   0.85  |    0.822 |     0.876 |

## Tie-breaks (reference labels decided by Jev)

| rule   |     n |   grok_gpt_split |   split_share |   jev_decided |   unresolved |   jev_sides_grok |   jev_sides_gpt |
|:-------|------:|-----------------:|--------------:|--------------:|-------------:|-----------------:|----------------:|
| all    | 23544 |              613 |        0.026  |            58 |          555 |               33 |              25 |
| 1      |  3996 |              363 |        0.0908 |            17 |          346 |               11 |               6 |
| 2      |  1080 |                5 |        0.0046 |             2 |            3 |                0 |               2 |
| 3      |   972 |               63 |        0.0648 |             3 |           60 |                2 |               1 |
| 4      | 15552 |              138 |        0.0089 |            21 |          117 |                8 |              13 |
| 5      |  1944 |               44 |        0.0226 |            15 |           29 |               12 |               3 |

## Jev agreement with the Grok+GPT consensus, by Jev confidence

| jev_bucket                   |     n |   share |   agreement_with_consensus |
|:-----------------------------|------:|--------:|---------------------------:|
| confident (P<=0.1 or P>=0.9) | 15452 |   0.674 |                      0.983 |
| uncertain                    |  7479 |   0.326 |                      0.71  |

## Recall by labeler

| model               |   recall_scorer |   recall_grok |   recall_gpt |   recall_jev |   recall_reference |
|:--------------------|----------------:|--------------:|-------------:|-------------:|-------------------:|
| qwen36              |           0.155 |         0.17  |        0.158 |        0.231 |              0.158 |
| qwen38flash         |           0.449 |         0.489 |        0.487 |        0.491 |              0.489 |
| mistral_small4      |           0.063 |         0.089 |        0.088 |        0.131 |              0.086 |
| glm53flash          |           0.47  |         0.495 |        0.486 |        0.473 |              0.491 |
| mimo26pro           |           0.48  |         0.502 |        0.484 |        0.488 |              0.494 |
| mistral_large4      |           0.461 |         0.476 |        0.465 |        0.43  |              0.47  |
| haiku55             |           0.224 |         0.233 |        0.227 |        0.231 |              0.222 |
| sonnet55            |           0.495 |         0.499 |        0.504 |        0.504 |              0.501 |
| opus55              |           0.699 |         0.686 |        0.686 |        0.639 |              0.697 |
| qwen36_high         |           0.187 |         0.217 |        0.201 |        0.274 |              0.2   |
| qwen38flash_high    |           0.342 |         0.398 |        0.385 |        0.378 |              0.388 |
| mistral_small4_high |           0.174 |         0.17  |        0.173 |        0.194 |              0.168 |
| glm53flash_high     |           0.57  |         0.594 |        0.581 |        0.555 |              0.589 |
| mimo26pro_high      |           0.651 |         0.691 |        0.687 |        0.643 |              0.692 |
| mistral_large4_high |           0.611 |         0.634 |        0.627 |        0.596 |              0.633 |
| haiku55_high        |           0.684 |         0.708 |        0.707 |        0.665 |              0.711 |
| sonnet55_high       |           0.653 |         0.651 |        0.663 |        0.631 |              0.66  |
| opus55_high         |           0.631 |         0.623 |        0.643 |        0.565 |              0.64  |
