# Rater agreement

Rows rated by all three raters: 23220

Reference = Grok and GPT verdict where they agree. On a split, Jev decides only when confident (P <= 0.1 or P >= 0.9); other splits are unresolved and excluded from scorer-vs-reference rows. A rule passes the reliability gate when scorer vs reference kappa >= 0.7. All labels are automated; there is no human validation.

## Pairwise agreement

| pair                | rule   |     n |   agreement |   kappa |   ci_low |   ci_high |
|:--------------------|:-------|------:|------------:|--------:|---------:|----------:|
| grok vs gpt         | all    | 23220 |       0.969 |   0.941 |    0.937 |     0.945 |
| grok vs gpt         | 1      |  3672 |       0.865 |   0.707 |    0.683 |     0.73  |
| grok vs gpt         | 2      |  1080 |       0.995 |   0.992 |    0.983 |     0.998 |
| grok vs gpt         | 3      |   972 |       0.935 |   0.86  |    0.825 |     0.892 |
| grok vs gpt         | 4      | 15606 |       0.994 |   0.988 |    0.986 |     0.991 |
| grok vs gpt         | 5      |  1890 |       0.971 |   0.934 |    0.917 |     0.95  |
| grok vs jev         | all    | 23220 |       0.93  |   0.865 |    0.859 |     0.872 |
| grok vs jev         | 1      |  3672 |       0.849 |   0.675 |    0.65  |     0.7   |
| grok vs jev         | 2      |  1080 |       0.996 |   0.993 |    0.986 |     0.998 |
| grok vs jev         | 3      |   972 |       0.868 |   0.737 |    0.697 |     0.778 |
| grok vs jev         | 4      | 15606 |       0.941 |   0.885 |    0.878 |     0.892 |
| grok vs jev         | 5      |  1890 |       0.984 |   0.963 |    0.949 |     0.975 |
| gpt vs jev          | all    | 23220 |       0.927 |   0.861 |    0.854 |     0.867 |
| gpt vs jev          | 1      |  3672 |       0.84  |   0.62  |    0.592 |     0.646 |
| gpt vs jev          | 2      |  1080 |       0.997 |   0.995 |    0.988 |     1     |
| gpt vs jev          | 3      |   972 |       0.845 |   0.689 |    0.647 |     0.737 |
| gpt vs jev          | 4      | 15606 |       0.943 |   0.888 |    0.88  |     0.895 |
| gpt vs jev          | 5      |  1890 |       0.974 |   0.942 |    0.925 |     0.956 |
| scorer vs grok      | all    | 23220 |       0.927 |   0.86  |    0.854 |     0.867 |
| scorer vs grok      | 1      |  3672 |       0.846 |   0.679 |    0.654 |     0.702 |
| scorer vs grok      | 2      |  1080 |       0.989 |   0.98  |    0.969 |     0.99  |
| scorer vs grok      | 3      |   972 |       0.87  |   0.73  |    0.686 |     0.773 |
| scorer vs grok      | 4      | 15606 |       0.944 |   0.891 |    0.884 |     0.898 |
| scorer vs grok      | 5      |  1890 |       0.938 |   0.844 |    0.817 |     0.869 |
| scorer vs gpt       | all    | 23220 |       0.922 |   0.851 |    0.844 |     0.857 |
| scorer vs gpt       | 1      |  3672 |       0.819 |   0.592 |    0.564 |     0.618 |
| scorer vs gpt       | 2      |  1080 |       0.992 |   0.985 |    0.974 |     0.994 |
| scorer vs gpt       | 3      |   972 |       0.834 |   0.652 |    0.601 |     0.699 |
| scorer vs gpt       | 4      | 15606 |       0.948 |   0.898 |    0.891 |     0.905 |
| scorer vs gpt       | 5      |  1890 |       0.917 |   0.801 |    0.773 |     0.828 |
| scorer vs jev       | all    | 23220 |       0.89  |   0.791 |    0.783 |     0.798 |
| scorer vs jev       | 1      |  3672 |       0.818 |   0.592 |    0.564 |     0.62  |
| scorer vs jev       | 2      |  1080 |       0.991 |   0.984 |    0.973 |     0.993 |
| scorer vs jev       | 3      |   972 |       0.879 |   0.757 |    0.716 |     0.798 |
| scorer vs jev       | 4      | 15606 |       0.896 |   0.797 |    0.788 |     0.806 |
| scorer vs jev       | 5      |  1890 |       0.932 |   0.832 |    0.805 |     0.858 |
| scorer vs reference | all    | 22601 |       0.937 |   0.878 |    0.872 |     0.884 |
| scorer vs reference | 1      |  3237 |       0.878 |   0.704 |    0.676 |     0.731 |
| scorer vs reference | 2      |  1077 |       0.993 |   0.987 |    0.977 |     0.995 |
| scorer vs reference | 3      |   912 |       0.877 |   0.741 |    0.692 |     0.784 |
| scorer vs reference | 4      | 15519 |       0.949 |   0.9   |    0.893 |     0.906 |
| scorer vs reference | 5      |  1856 |       0.938 |   0.848 |    0.82  |     0.874 |

## Tie-breaks (reference labels decided by Jev)

| rule   |     n |   grok_gpt_split |   split_share |   jev_decided |   unresolved |   jev_sides_grok |   jev_sides_gpt |
|:-------|------:|-----------------:|--------------:|--------------:|-------------:|-----------------:|----------------:|
| all    | 23220 |              713 |        0.0307 |            94 |          619 |               37 |              57 |
| 1      |  3672 |              496 |        0.1351 |            61 |          435 |               17 |              44 |
| 2      |  1080 |                5 |        0.0046 |             2 |            3 |                0 |               2 |
| 3      |   972 |               63 |        0.0648 |             3 |           60 |                2 |               1 |
| 4      | 15606 |               94 |        0.006  |             7 |           87 |                5 |               2 |
| 5      |  1890 |               55 |        0.0291 |            21 |           34 |               13 |               8 |

## Jev agreement with the Grok+GPT consensus, by Jev confidence

| jev_bucket                   |     n |   share |   agreement_with_consensus |
|:-----------------------------|------:|--------:|---------------------------:|
| confident (P<=0.1 or P>=0.9) | 15842 |   0.704 |                      0.989 |
| uncertain                    |  6665 |   0.296 |                      0.83  |

## Rule 1: passes the reliability gate (scorer vs reference kappa 0.704 >= 0.7)

The pass is marginal, so recall is also reported as a range across labelers.

| model               |   recall_scorer |   recall_grok |   recall_gpt |   recall_low |   recall_high |
|:--------------------|----------------:|--------------:|-------------:|-------------:|--------------:|
| qwen36              |           0.095 |         0.122 |        0.095 |        0.095 |         0.122 |
| qwen38flash         |           0.27  |         0.418 |        0.323 |        0.27  |         0.418 |
| mistral_small4      |           0.127 |         0.259 |        0.185 |        0.127 |         0.259 |
| glm53flash          |           0.238 |         0.206 |        0.153 |        0.153 |         0.238 |
| mimo26pro           |           0.228 |         0.19  |        0.138 |        0.138 |         0.228 |
| mistral_large4      |           0.28  |         0.275 |        0.169 |        0.169 |         0.28  |
| haiku55             |           0.116 |         0.106 |        0.085 |        0.085 |         0.116 |
| sonnet55            |           0.307 |         0.333 |        0.243 |        0.243 |         0.333 |
| opus55              |           0.455 |         0.497 |        0.376 |        0.376 |         0.497 |
| qwen36_high         |           0.032 |         0.069 |        0.053 |        0.032 |         0.069 |
| qwen38flash_high    |           0.175 |         0.206 |        0.138 |        0.138 |         0.206 |
| mistral_small4_high |           0.106 |         0.063 |        0.058 |        0.058 |         0.106 |
| glm53flash_high     |           0.265 |         0.296 |        0.164 |        0.164 |         0.296 |
| mimo26pro_high      |           0.286 |         0.381 |        0.265 |        0.265 |         0.381 |
| mistral_large4_high |           0.28  |         0.275 |        0.222 |        0.222 |         0.28  |
| haiku55_high        |           0.333 |         0.386 |        0.175 |        0.175 |         0.386 |
| sonnet55_high       |           0.55  |         0.582 |        0.386 |        0.386 |         0.582 |
| opus55_high         |           0.455 |         0.571 |        0.381 |        0.381 |         0.571 |

## Recall by labeler

| model               |   recall_scorer |   recall_grok |   recall_gpt |   recall_jev |   recall_reference |
|:--------------------|----------------:|--------------:|-------------:|-------------:|-------------------:|
| qwen36              |           0.156 |         0.159 |        0.153 |        0.206 |              0.154 |
| qwen38flash         |           0.448 |         0.473 |        0.459 |        0.49  |              0.465 |
| mistral_small4      |           0.065 |         0.089 |        0.079 |        0.1   |              0.078 |
| glm53flash          |           0.454 |         0.444 |        0.436 |        0.482 |              0.438 |
| mimo26pro           |           0.474 |         0.461 |        0.451 |        0.483 |              0.454 |
| mistral_large4      |           0.432 |         0.411 |        0.395 |        0.417 |              0.399 |
| haiku55             |           0.207 |         0.196 |        0.192 |        0.208 |              0.19  |
| sonnet55            |           0.494 |         0.442 |        0.435 |        0.488 |              0.435 |
| opus55              |           0.679 |         0.603 |        0.593 |        0.63  |              0.601 |
| qwen36_high         |           0.188 |         0.192 |        0.192 |        0.244 |              0.189 |
| qwen38flash_high    |           0.328 |         0.346 |        0.333 |        0.367 |              0.336 |
| mistral_small4_high |           0.166 |         0.148 |        0.15  |        0.164 |              0.146 |
| glm53flash_high     |           0.548 |         0.542 |        0.526 |        0.557 |              0.533 |
| mimo26pro_high      |           0.629 |         0.635 |        0.619 |        0.653 |              0.629 |
| mistral_large4_high |           0.592 |         0.602 |        0.593 |        0.621 |              0.596 |
| haiku55_high        |           0.663 |         0.674 |        0.647 |        0.671 |              0.665 |
| sonnet55_high       |           0.646 |         0.614 |        0.595 |        0.635 |              0.607 |
| opus55_high         |           0.607 |         0.526 |        0.512 |        0.555 |              0.521 |
