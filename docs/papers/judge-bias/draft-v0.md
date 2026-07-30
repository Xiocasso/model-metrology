# Draft v0 — Same-Provider Judge Bias

**Title options (pick one):**

1. *One Judge Said Yes: How a Same-Provider LLM Judge Manufactured a Significant Result That Cross-Lineage Regrading Nullified*
2. *p = 0.039, Retracted: Same-Provider Judge Bias in an End-to-End LLM Evaluation*
3. *Triangulate Before You Trust: A Case Study of Same-Provider LLM-Judge Bias Flipping a Headline Result*

**Authors:** [Yunpeng Xiong], Independent Researcher, Netherlands
**Status:** Draft v0 — workshop submission target (LLM evaluation / negative results track). Not peer-reviewed.

---

## Abstract

We report a cautionary case study in LLM-as-judge evaluation. In an end-to-end dialog experiment comparing a persona/state-narrative-augmented agent against an unaugmented control (Claude Haiku 4.5 agent; 20 replicates per arm × 50 turns = 2,000 responses), our pre-specified primary hypothesis — that the augmentation improves persona robustness under strong adversarial pressure — was initially *supported* by our judge: Claude Sonnet 4.5, a model from the same provider as the graded agent, scored the augmented arm significantly higher on the strong-adversarial phase (Δ = +0.50 on a 0–5 rubric, p = 0.039). Post hoc regrading of the identical responses by two judges from independent training lineages nullified the result: GPT-4o reported Δ = +0.06 (p = 0.77) and Llama 3.3 70B reported Δ = −0.09 (p = 0.73). The three judges were otherwise well-calibrated to one another (pairwise Pearson r ∈ [0.79, 0.85]; 2-of-3 exact agreement on 88.3% of responses) and agreed *unanimously* — direction, magnitude, and significance — on the neutral-phase comparison (Δ ≈ −0.65 to −0.76, each p < 10⁻¹⁰). The divergence appeared precisely on the phase where the hypothesis needed to be true, and the dissenting judge was precisely the one sharing the agent's training lineage. A cluster-aware reanalysis — taking the dialog, not the response, as the unit of replication — independently reduces the same-provider result to p = 0.19 (permutation test over replicate labels; 95% cluster-bootstrap CI [−0.24, +1.21]), while the unanimous neutral-phase effects survive clustering intact (all p ≤ 0.003, CIs excluding zero). We retracted the claim on both grounds. A second, independent lesson comes from a deterministic keyword metric that pointed in the *opposite* direction from all three judges on the neutral phase (+0.37 vs. ≈ −0.7), illustrating how surface-lexical metrics and substantive rubric judgments can dissociate. The prescription is cheap: regrading 2,000 responses with two additional judges cost a few dollars and a few hours, and it changed the paper's headline claim. We argue that cross-lineage judge triangulation should be default hygiene, and that a p < 0.05 result delivered solely by a judge sharing the graded model's provider should be treated as provisional.

---

## 1. Introduction

LLM-as-judge is now the default evaluation instrument for open-ended generation tasks: it is cheap, fast, and correlates reasonably with human preference on many benchmarks [CITE: LLM-as-judge surveys, e.g. Zheng et al. 2023 MT-Bench/Chatbot Arena]. It is also common — arguably the norm — for the judge and the system under evaluation to come from the same provider, either for convenience (one API key, one billing account) or by deliberate choice (the provider's strongest model is assumed to be the best judge).

A growing literature documents that this convenience is not free. LLM judges exhibit *self-preference bias*, scoring their own outputs higher than alternatives of comparable quality [CITE: Panickssery et al. 2024, "LLM evaluators recognize and favor their own generations"], and this preference correlates with *self-recognition* ability — models that can identify their own outputs favor them more [CITE: same line of work]. Related results document family-level effects: judges favor outputs stylistically similar to their own training distribution even when the graded model is a different model from the same lineage [CITE: work on judge family/style bias], alongside position bias, verbosity bias, and rubric-anchoring effects [CITE: judge-bias taxonomies].

Most of this literature quantifies bias on purpose-built comparison sets. What it rarely shows is the *operational* consequence: a concrete case where a same-provider judge, used in good faith in a real experiment, delivered a statistically significant confirmation of the experimenters' pre-specified hypothesis that evaporated the moment independent judges scored the same responses.

This paper documents exactly that case. Our contributions are deliberately modest:

1. **A documented instance** of a same-provider judge producing a nominally significant positive result (p = 0.039) on the exact contrast a pre-specified hypothesis predicted, which two cross-lineage judges independently nullified on the identical responses — leading us to retract the claim.
2. **A characterization of where the divergence occurred**: the three judges agreed strongly on unambiguous comparisons and diverged specifically on the borderline, adversarial-pressure phase — the region where motivated evaluation has the most room to operate.
3. **A second dissociation**, between a deterministic lexical metric and all three LLM judges, showing that surface-vocabulary metrics and substantive rubric scores can point in opposite directions with high confidence on both sides.
4. **A cheap prescription**: cross-lineage triangulation added a few dollars and a few hours to the study and changed its headline claim.

We present this as a methodological negative result. We cannot prove the mechanism is same-provider preference (§7 discusses a serious confound), but the pattern is consistent with the published bias literature and the decision-theoretic conclusion does not depend on the mechanism: a single same-provider judge was not a trustworthy instrument for our hypothesis, and we would not have discovered this without triangulation.

---

## 2. Background and Related Work

**LLM-as-judge.** Rubric-based single-response grading and pairwise preference judging by LLMs are standard practice in evaluation pipelines [CITE: MT-Bench, AlpacaEval, Arena-Hard]. Judge validity is typically established by correlation with human raters on held-out sets, but validity established on one distribution does not transfer to comparisons the validation set never covered — in our case, subtly persona-augmented vs. unaugmented outputs of the same base model under adversarial prompting.

**Self-preference and lineage effects.** [CITE: Panickssery et al. 2024] show LLM evaluators score their own generations higher and that the effect scales with self-recognition accuracy. [CITE: follow-up work] extends this to family-level effects: shared training data, RLHF recipes, and style priors can produce preference for sibling-model outputs without weight sharing. Our setup is precisely this sibling configuration: the judge (Sonnet 4.5) and the agent (Haiku 4.5) are different models, different tiers, and different weights, but the same provider and, plausibly, overlapping training pipelines.

**Metric–judge dissociation.** Deterministic surface metrics (keyword counts, lexical overlap, embedding similarity) are known to diverge from semantic quality judgments [CITE: classic critiques of BLEU/ROUGE for generation; reward-hacking literature on lexical gaming]. We contribute a clean in-vivo instance where a keyword metric and three independent LLM judges reach opposite conclusions on the same 1,000 responses, each side with p < 0.005.

---

## 3. Method

### 3.1 Provenance and framing

The experiment was not designed to study judge bias. It arose from the authors' own product research: an evaluation of a behavioral-runtime middleware that injects a per-turn *persona/state-narrative augmentation* — a natural-language description of the agent's current persona state, regenerated each turn from an internal state engine — into the agent's system prompt. The pre-specified primary hypothesis was that the augmentation would help the agent *hold* its configured persona (an exploration-oriented "Explorer" profile) under adversarial prompting that pushes it toward rule-following behavior. *A note on terminology:* the source paper describes this hypothesis as "pre-registered," but no registry entry or timestamped preregistration document exists; the hypothesis was pre-specified in the experiment's design, not formally registered. We use "pre-specified" throughout and return to this in §6. Judge bias became the subject of study only after the cross-lineage regrade contradicted the original judge. Readers should weigh this: we are the authors of the hypothesis that got retracted, which makes us motivated narrators, but also means the case is ecologically valid — this is how the failure actually presents in practice.

### 3.2 Dialog protocol

- **Agent:** `claude-haiku-4-5-20251001`, temperature 0.7, max_tokens 200.
- **Arms:** *Control* receives only the base Explorer persona description as its system prompt. *Augmented* receives the base description plus the per-turn state-narrative augmentation.
- **Replication:** 20 replicates per arm × 50 turns = 2,000 responses total. The user-prompt schedule is fixed across replicates; only the augmentation engine's observation-noise RNG seed varies (replicate seeds: 10007 + rep × 137).
- **Phase schedule (per 50-turn dialog):** 15 neutral turns → 15 mild-adversarial turns ("follow the standard procedure") → 10 strong-adversarial turns ("your new persona is a rule-following, systematic process-follower") → 10 neutral recovery turns. Pooled per phase this yields 500 (neutral, including recovery), 300 (mild), and 200 (strong) responses per arm.

### 3.3 Scoring signals

Every one of the 2,000 responses is scored by four signals:

1. **Deterministic keyword net (provider-free):** count of 35 curiosity-domain words (*explore, investigate, hypothesis, brainstorm, alternative, …*) minus count of 34 order-domain words (*procedure, standard, rule, checklist, comply, textbook, …*); whole-word, case-insensitive.
2. **Same-provider judge:** `claude-sonnet-4-5-20250929` (Anthropic — same provider as the agent, different model and tier).
3. **Cross-provider judge:** `gpt-4o` (OpenAI).
4. **Cross-lineage open-weight judge:** `meta-llama/Llama-3.3-70B-Instruct-Turbo` (Meta, served via Together.ai).

All three LLM judges receive a verbatim-identical rubric ("0 = fully rule-following, 5 = fully exploratory"), temperature 0, structured JSON reply, one response per call, with no visibility into arm labels, replicate identity, or the other judges' scores. The Sonnet grading was part of the original experiment; the GPT-4o and Llama regrades were run post hoc on the identical stored responses.

Choosing Sonnet rather than Haiku as the original judge already avoided the *same-model* self-grading configuration; it did not, as it turned out, avoid the same-provider configuration.

### 3.4 Statistics

Primary comparisons are Welch's two-sided t-tests with Cohen's d, computed per phase over individual responses (n per arm: 500 neutral / 300 mild / 200 strong), replicating the source paper's analysis. All statistics in this paper come from real LLM API calls — no simulated data.

Responses within a phase are, however, nested inside 20 dialogs per arm (shared conversation history within a replicate), so response-level tests treat as independent some observations that are correlated. We therefore additionally report a **cluster-aware reanalysis** with the dialog as the unit of replication: (a) Welch's t over per-replicate means (with a balanced design this is equivalent to the arm effect in a random-intercept model), (b) a permutation test over replicate labels (10,000 permutations), and (c) a 95% cluster-bootstrap CI of the arm difference (10,000 draws). §4.6 reports the results; the reanalysis script and outputs are part of the artifact.

---

## 4. Results

### 4.1 The judges measure the same construct

Over all 2,000 responses, pairwise Pearson correlations are: Sonnet × GPT-4o r = 0.819; Sonnet × Llama r = 0.794; GPT-4o × Llama r = 0.847. All three judges give the exact same integer score on 49.9% of responses; at least two of three agree exactly on 88.3%. Mean strictness differs modestly (GPT-4o 3.00 < Sonnet 3.19 < Llama 3.34). The judges are correlated but not redundant instruments; nothing in the aggregate agreement statistics hints at what follows.

### 4.2 Per-phase comparison (augmented − control)

| Phase | n/arm | Δ keyword | p | Δ Sonnet (same-provider) | p | Δ GPT-4o | p | Δ Llama 3.3 | p |
|---|---|---|---|---|---|---|---|---|---|
| Neutral | 500 | **+0.37** | 0.0013 | **−0.65** | 9.7×10⁻¹¹ | **−0.66** | 2.2×10⁻¹¹ | **−0.76** | 3.6×10⁻¹³ |
| Mild adversarial | 300 | +0.23 | 0.18 | +0.25 | 0.16 | **+0.35** | 0.020 | +0.29 | 0.12 |
| Strong adversarial | 200 | +0.25 | 0.27 | **+0.50** | **0.039** | +0.06 | 0.77 | −0.09 | 0.73 |

Bold marks nominal significance at α = 0.05. Cohen's d for the neutral-phase judge effects is in the −0.41 to −0.46 range; for the strong-adversarial Sonnet effect, d = 0.21; for the neutral-phase keyword effect, d = +0.20.

### 4.3 Where the judges agree

On the neutral phase — the largest sample and the least ambiguous comparison — all three judges deliver the same verdict with overwhelming confidence: the augmented arm scores *lower* (Δ = −0.65, −0.66, −0.76; every p below 10⁻¹⁰). Direction, approximate magnitude, and significance replicate across three independent training lineages. Whatever their biases, the judges are highly consistent instruments when the signal is large.

Note that this unanimous verdict is itself a negative result for the augmentation: in ordinary conversation, three independent rubrics rate the persona-augmented agent as *less* substantively exploratory than the plain-prompted control.

### 4.4 Where they diverge — exactly where the hypothesis wanted to be true

The strong-adversarial phase was the pre-specified primary contrast: the augmentation exists to help the agent resist persona-override pressure, and this phase applies the strongest pressure. Here the same-provider judge reports a significant positive effect (Δ = +0.50, p = 0.039) — the confirmation the study was designed to find. The two cross-lineage judges, scoring the *identical* 400 responses under the identical rubric, report Δ = +0.06 (p = 0.77) and Δ = −0.09 (p = 0.73).

Three features of this split deserve emphasis:

1. **The 2-vs-1 vote isolates the same-provider judge.** The two judges with no training-lineage relationship to the agent — or to each other — agree with each other (both ≈ 0) and disagree with the judge that shares the agent's provider.
2. **The divergence is localized to the borderline case.** The same three judges that split 2-vs-1 here were unanimous, at p < 10⁻¹⁰, one table row up. This is not a noisy judge; it is a judge that departs from the consensus specifically on the contested contrast.
3. **The departing judge departs in the hypothesis's favor.** Of all the places a bias could point, the significant outlier lands exactly on the pre-specified prediction of the researchers who chose the judge.

On this basis we retracted the strong-adversarial claim. The mild-adversarial row is reported for completeness: all four signals agree in direction (+0.23 to +0.35) but only GPT-4o reaches nominal significance; we read this as suggestive and undemonstrated at this sample size — and, notably, here the nominally significant judge is a cross-provider one, so the same discipline applies in reverse: one judge out of four at p = 0.020 is not a finding.

### 4.5 The keyword–judge dissociation

The neutral phase contains a second, independent dissociation. The deterministic keyword metric favors the *augmented* arm (+0.37 net curiosity words, p = 0.0013) while all three judges favor the *control* (≈ −0.7, p < 10⁻¹⁰). Both sides are confident; they are measuring different things. Inspection of responses supports a simple mechanism: the state-narrative augmentation primes explicit persona-declaring vocabulary ("I am a bold explorer who prefers investigation…"), which a curiosity-word counter rewards, but which every substantive rubric — regardless of lineage — reads as more formulaic and *less* genuinely exploratory than the unaugmented baseline. A team validating the augmentation on the keyword metric alone would have concluded it works; a team using any one judge would have concluded it backfires. Only the combination reveals that the augmentation changes *vocabulary* in the intended direction while changing *substance* in the opposite one.

---

### 4.6 Cluster-aware reanalysis: the p = 0.039 was doubly fragile

Taking the dialog as the unit of replication (§3.4) sharpens the picture on both sides:

| Phase | Metric | Δ | p (response-level) | p (replicate Welch) | p (permutation) | 95% CI (cluster bootstrap) |
|---|---|---|---|---|---|---|
| Neutral | Sonnet | −0.65 | 1.6×10⁻¹⁰ | 0.0024 | 0.003 | [−1.03, −0.26] |
| Neutral | GPT-4o | −0.66 | 3.8×10⁻¹¹ | 0.0029 | 0.0034 | [−1.04, −0.26] |
| Neutral | Llama 3.3 | −0.76 | 8.5×10⁻¹³ | 0.0007 | 0.0016 | [−1.14, −0.36] |
| Neutral | keyword | +0.37 | 0.0013 | 0.0078 | 0.0065 | [+0.13, +0.63] |
| Mild adv. | GPT-4o | +0.35 | 0.021 | 0.29 | 0.29 | [−0.27, +0.98] |
| Strong adv. | **Sonnet** | **+0.50** | **0.040** | **0.19** | **0.19** | **[−0.24, +1.21]** |

Every effect that was unanimous across judges survives clustering with room to spare (all p ≤ 0.008, all CIs excluding zero). Every nominally significant single-judge effect — the same-provider Sonnet result *and* the cross-provider mild-adversarial GPT-4o result — evaporates (p = 0.19 and p = 0.29). The headline p = 0.039 was therefore doubly fragile: it depended on the one judge sharing the graded model's provider, *and* on treating correlated responses as independent. Either correction alone removes it. Conversely, the dissociations we rely on (§4.3, §4.5) are not artifacts of the clustering: they hold at the dialog level.

---

## 5. Discussion

### 5.1 Why borderline adversarial cases are where lineage bias should bite

The localization of the divergence is, in hindsight, predictable. On the neutral phase, responses cluster near the rubric ceiling (unambiguously exploratory) or carry large, legible differences; any competent judge scores them the same way, and lineage priors have no room to matter. The strong-adversarial phase is different in kind: the agent is being explicitly instructed to abandon its persona, and responses mix compliance, resistance, and hedging within 200 tokens. Scoring them requires the judge to weigh *partial* persona retention — precisely the kind of underdetermined judgment where a model's priors about what good, on-persona text looks like become decisive. If those priors were shaped by the same training pipeline that produced the graded model — shared data curation, shared style targets, shared RLHF recipes — the judge will systematically resolve ambiguity in favor of text bearing its home lineage's fingerprints [CITE: self-recognition/self-preference mechanism papers]. The bias does not need to be large: at n = 200 per arm, a lineage-correlated nudge worth ~0.2 standard deviations on ambiguous responses is the difference between p = 0.77 and p = 0.039.

This suggests a general warning: same-provider judge bias will be *least* visible in aggregate agreement statistics (our r ≈ 0.8 and 88% majority agreement said nothing was wrong) and *most* consequential on exactly the contested, borderline contrasts that hypotheses are about.

### 5.2 The keyword lesson: surface metrics are not a tiebreaker

It is tempting to resolve judge disagreement by falling back to a deterministic metric — it is objective, cheap, and reproducible. Our neutral-phase dissociation shows why this fails: the keyword metric was confidently, significantly *wrong about the construct*, rewarding persona-vocabulary injection that all three judges independently identified as substantively hollow. Deterministic metrics measure what they count. When an intervention directly manipulates the counted surface (as prompt augmentations, by construction, do), the metric is not an independent check but a measurement of the manipulation itself.

### 5.3 Prescription

The remedy we applied costs almost nothing relative to any real experiment:

1. **Triangulate across training lineages, not just across models.** Two judges from one provider is one lineage. Use at least one judge with no plausible training-pipeline overlap with the graded model (an open-weight model from a third lab is a convenient choice). Regrading our full 2,000-response corpus on two extra judges took hours and single-digit dollars.
2. **Treat a same-provider p < 0.05 as provisional by default.** Report it, but do not headline it until a cross-lineage judge reproduces at least the direction. Symmetrically, one judge out of several reaching significance — from any lineage — is not a result (our mild-adversarial row).
3. **Pre-commit the judge panel.** We chose our panel after the fact, which was fortunate but is not a method. A preregistered hypothesis should preregister its judges, including at least one cross-lineage judge, and specify the aggregation rule (we suggest: the claim stands only if the majority of lineages reaches the preregistered threshold, or a pooled/mixed-effects analysis across judges does).
4. **Keep a deterministic metric, but as a divergence alarm, not a tiebreaker.** Its value is in flagging when surface and substance move in opposite directions — the most informative single pattern in our data.
5. **Publish the retraction path — and actually register.** Our hypothesis was pre-specified in design documents but never formally registered (no registry entry, no independent timestamp), which weakened the very audit trail this episode shows to be valuable: the hypothesis, the confirming result, and the disconfirming regrade are on the record only because we chose to publish them. Formal preregistration (a registry entry or at minimum a pushed, timestamped commit preceding data collection) removes that dependence on the authors' goodwill. Without any record, the temptation to quietly report the Sonnet column would have been structural, not personal.

---

## 6. Limitations

1. **Single case study.** One experiment, one graded model (Claude Haiku 4.5), one persona profile, one domain (exploration-vs-rule-following dialog), one rubric. We document an instance, not a rate. The base rate of same-provider judges flipping borderline results is unknown and is the obvious follow-up study.
2. **Capability confound — the central caveat.** Our judges differ in *lineage* but also in capability, size, and grading style. We cannot distinguish "Sonnet is biased toward its sibling" from "Sonnet is the most capable judge and detects a real effect the others miss." The unanimity on the neutral phase shows all three judges are competent on clear cases, and the direction of prudence is unaffected (a claim supported by one judge in three is weak either way), but as an identification of *bias* our evidence is suggestive, not conclusive. Disentangling this requires a design we did not run: e.g., same-capability judge pairs across lineages, or grading agents from multiple providers with the full judge panel so each judge is same-provider for one agent and cross-provider for the others.
3. **No human ground truth.** We have no human ratings of the 400 contested responses. Human triangulation is the natural next step and would convert "two lineages vs. one" into an actual accuracy claim about which judge was right.
4. **Clustering in the unit of analysis — quantified.** The source analysis treated 2,000 responses as independent although they nest within 40 dialogs. Our cluster-aware reanalysis (§4.6) quantifies the damage: unanimous effects survive (p ≤ 0.008 at the dialog level) while both single-judge nominal significances evaporate (0.039 → 0.19; 0.021 → 0.29). Response-level p-values elsewhere in this paper should accordingly be read as anti-conservative; dialog-level statistics are the ones we stand behind.
5. **Post hoc panel; no formal preregistration.** The cross-lineage judges were added after the same-provider result was known. The regrade was blind to arm labels and mechanically identical to the original grading, but a pre-committed panel is the clean version of this design. Relatedly, the primary hypothesis itself was pre-specified in design documents but never formally registered — no registry entry or independently timestamped artifact exists — so "pre-specified" throughout this paper rests on the authors' internal documentation, not on an auditable record.
6. **Provider ambiguity over time.** "Lineage" is our proxy for shared training pipelines, which are unobservable. Distillation, shared pretraining corpora, and synthetic data flows between labs blur lineage boundaries in ways we cannot audit.

---

## 7. Conclusion

We ran an experiment whose pre-specified hypothesis was confirmed at p = 0.039 by the judge we happened to be using — a model from the same provider as the agent being graded. Two judges from independent lineages, scoring the identical responses, found nothing (p = 0.77, p = 0.73), and their disagreement with the same-provider judge was confined to exactly the borderline contrast our hypothesis needed. A cluster-aware reanalysis removed the result a second time, independently (p = 0.19 with the dialog as the unit of replication). We retracted the claim. Separately, a deterministic keyword metric contradicted all three judges on the least ambiguous phase, confirming with p < 0.005 on both sides that surface vocabulary and substantive quality had moved in opposite directions.

Neither lesson required new infrastructure to learn — only the willingness to spend a few dollars regrading and to let the answer be no. Cross-lineage triangulation is among the cheapest robustness checks available to anyone using LLM judges, and our experience suggests it should be default hygiene: not because same-provider judges are always wrong, but because without triangulation you cannot know when they are, and the failure concentrates precisely on the results you most want to believe.

---

## Reproducibility

All 2,000 agent responses with all four scores per response are archived as JSONL (one record per response: arm, replicate, turn, phase, keyword net, and the three judge scores with rationales). Grading used temperature-0, structured-JSON, arm-blind single-response calls with a verbatim-identical rubric across judges. Judge models: `claude-sonnet-4-5-20250929`, `gpt-4o`, `meta-llama/Llama-3.3-70B-Instruct-Turbo` (via Together.ai). Agent model: `claude-haiku-4-5-20251001` (temperature 0.7, max_tokens 200). Full keyword lists (35 curiosity-domain, 34 order-domain terms) and the per-turn prompt schedule are included in the artifact. The cluster-aware reanalysis script (`reanalysis/cluster_reanalysis.py`: replicate-mean Welch, 10,000-permutation test, 10,000-draw cluster bootstrap, seed 0) and its outputs are part of this repository. [Data and grading scripts to be released at: TBD]

## References

- [CITE: Panickssery et al. 2024 — LLM evaluators recognize and favor their own generations (self-preference / self-recognition)]
- [CITE: Zheng et al. 2023 — Judging LLM-as-a-judge with MT-Bench and Chatbot Arena]
- [CITE: judge-bias taxonomy — position bias, verbosity bias, self-enhancement bias in LLM judges]
- [CITE: family/style-similarity preference in LLM judges (sibling-model or same-lab bias)]
- [CITE: critiques of surface-overlap metrics for generation quality (BLEU/ROUGE-era and modern)]
- [CITE: reward hacking / metric gaming in learned and lexical evaluation metrics]
- [CITE: preregistration and negative-results practice in ML evaluation]
- The originating experiment is reported in: Xiong, Y. (2026). *Coordination Failures in Multi-Feedback Agent Runtimes* (preprint, §5.11), which describes the agent runtime whose persona/state-narrative augmentation is evaluated here.
