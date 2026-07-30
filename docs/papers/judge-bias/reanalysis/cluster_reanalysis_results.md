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
