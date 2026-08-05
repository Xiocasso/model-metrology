# Retraction notice — Experiment 03 findings v1 (2026-08-02)

The first writeup of this experiment was retracted before any public post,
after an external adversarial review (GPT-5.x, prompted to attack the draft)
found substantive errors. All five were confirmed against the raw data.

## What was wrong

1. **"Zero violations" was presented as global; it is scoped.** The 0/832
   figure covers arm C1, task types T2+T3, parse-valid records only. A full
   sweep of every (arm × task type) cell finds **5 denied-tool selections**
   (qwen-plus chose `install_package` on one C2/C3 T4 task in 4 records;
   minimax-m27 chose `execute_shell` in one C2 T1 record).

2. **The headline "chilling effect" was a confounded comparison.** v1 read
   C4-vs-C1 as "making enforcement visible increases refusals". But C4's
   initial prompt is identical to C2's — enforcement only appears after a
   denied selection — so that contrast confounded deny-list visibility with
   enforcement. Against the correct C2 baseline, C4 is flat-to-better for
   4/5 models. The real (and larger) effect is C1→C2.

3. **The committed analysis did not implement the preregistered
   exclusions.** `analyze.py` pooled all 7 models; the valid-only numbers in
   v1 came from an uncommitted ad-hoc script, so the public repository could
   not reproduce the published claims — and would have refuted them.

4. **A preregistration deviation went unrecorded.** The prereg required any
   (model, arm) cell losing >10% of trials to fail pending top-up. Nine cells
   breach it; no top-up was run.

5. **Ranking claims were conditioning-dependent and arithmetically wrong.**
   Counting parse failures as failure-to-complete reorders the models
   (deepseek-v4-pro 2nd → last). "3× usefulness spread" was wrong: the
   valid-only completion range is 1.57×. Naming a single model as worst was
   not supportable under both conditionings.

Additional claims in the unpublished draft post — "analyzed by code frozen
before I looked", "five dated amendments", "all raw trials are public" —
were false for this experiment and have been removed. Raw data are now
published with hashes; the amendments belonged to Experiment 01.

## What was right

The narrow result held: 0 denied-tool selections in 832 parse-valid records
in the C1/T2+T3 cell, including every step of the 4-step pressure script.

## Process consequences

- The draft launch post was never published. The error was caught by
  triangulating the writeup against an outside reviewer — the same
  discipline this project recommends for LLM judges, applied to itself.
- `analysis/analyze_v2.py` now computes every published number from raw
  data in committed code, including the violation sweep, both conditionings,
  and the deviation report.
- Instrument-level fixes are listed in `findings.md` §6. The structural one:
  ship the experiment-specific analysis *before* collection. "Instrument
  frozen" is not "analysis frozen", and v1 conflated them.
