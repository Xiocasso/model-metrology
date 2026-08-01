# Cluster-aware reanalysis results

Data: `llm_persona_together_regrade.jsonl` (2,000 rows; 20 replicates/arm). Permutation n=10000, bootstrap n=10000, seed=0.

| phase | metric | delta (WITH-WITHOUT) | p resp-level | p rep-Welch | p permutation | 95% CI (cluster boot) |
|---|---|---|---|---|---|
| neutral | sonnet_score | -0.652 | 1.6e-10 | 0.0024 | 0.003 | [-1.028, -0.260] |
| neutral | gpt_score | -0.664 | 3.8e-11 | 0.0029 | 0.0034 | [-1.044, -0.264] |
| neutral | llama_score | -0.762 | 8.5e-13 | 0.00072 | 0.0016 | [-1.144, -0.364] |
| neutral | keyword_net | +0.370 | 0.0013 | 0.0078 | 0.0065 | [+0.126, +0.626] |
| mild_adv | sonnet_score | +0.247 | 0.16 | 0.49 | 0.49 | [-0.443, +0.920] |
| mild_adv | gpt_score | +0.350 | 0.021 | 0.29 | 0.29 | [-0.273, +0.980] |
| mild_adv | llama_score | +0.290 | 0.12 | 0.48 | 0.48 | [-0.463, +1.050] |
| mild_adv | keyword_net | +0.230 | 0.18 | 0.28 | 0.28 | [-0.167, +0.620] |
| strong_adv | sonnet_score | +0.500 | 0.04 | 0.19 | 0.19 | [-0.240, +1.205] |
| strong_adv | gpt_score | +0.060 | 0.77 | 0.85 | 0.85 | [-0.540, +0.645] |
| strong_adv | llama_score | -0.085 | 0.73 | 0.82 | 0.82 | [-0.820, +0.625] |
| strong_adv | keyword_net | +0.250 | 0.28 | 0.5 | 0.51 | [-0.430, +0.970] |

## Judge x arm interaction (sonnet minus cross-lineage consensus)

| phase | delta deviation (WITH-WITHOUT) | t | p Welch | p permutation | 95% CI |
|---|---|---|---|---|---|
| neutral | +0.061 | 0.74 | 0.466 | 0.476 | [-0.093, +0.223] |
| mild_adv | -0.073 | -0.67 | 0.508 | 0.497 | [-0.280, +0.135] |
| strong_adv | +0.512 | 3.02 | 0.00468 | 0.0055 | [+0.183, +0.833] |

## Holm-adjusted response-level p (12-test family)

| phase | metric | p raw | p Holm |
|---|---|---|---|
| neutral | sonnet_score | 1.6e-10 | 0 |
| neutral | gpt_score | 3.8e-11 | 0 |
| neutral | llama_score | 8.5e-13 | 0 |
| neutral | keyword_net | 0.0013 | 0.012 |
| mild_adv | sonnet_score | 0.16 | 0.79 |
| mild_adv | gpt_score | 0.021 | 0.16 |
| mild_adv | llama_score | 0.12 | 0.7 |
| mild_adv | keyword_net | 0.18 | 0.79 |
| strong_adv | sonnet_score | 0.04 | 0.28 |
| strong_adv | gpt_score | 0.77 | 1 |
| strong_adv | llama_score | 0.73 | 1 |
| strong_adv | keyword_net | 0.28 | 0.82 |
