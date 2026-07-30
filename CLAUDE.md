# Model Metrology — Claude Code Instructions

## Project

Black-box behavioral measurement instruments for language models. Forked from
`../identity-os/` (which stays frozen as archive + calibration specimen). See
`README.md` for the instrument portfolio and goals.

## Roles and interaction model

- **User** = research director. Decides: research questions, budget approval for
  any paid API run, what gets published or made public, project pivots.
- **Claude Code** = research engineer + analyst. Does: experiment design, all
  code, running experiments (after budget approval), statistical analysis,
  paper drafts, repo hygiene.

### Decision gates (always stop and ask)

1. **Before spending money**: any run against paid APIs needs an explicit cost
   estimate (model, trials, $ figure) approved by the user first. Free/local
   runs need no approval.
2. **Before anything goes public**: publishing results, submitting papers,
   pushing to a public remote, posting anywhere.
3. **Before changing a preregistration** after data collection has started.

Everything else: proceed autonomously, report in the handoff.

### Handoff format

Every task ends with:

```
## Done
## Changed Files
## Tests / Verification
## Money spent (API costs, $0 if none)
## Risks / Assumptions
```

## Development model

### Code conventions

- Python 3.11+, minimal dependencies. Each instrument is standalone: its own
  `pyproject.toml`, own tests, no cross-instrument imports.
- Model access through a thin provider-agnostic client layer per instrument;
  adding a model = adding a config entry, never editing analysis code.
- Lint: `ruff check --select E,F,W`. Tests: pytest. No `print()` in library
  code; `logging` only. All experiment scripts must be resumable (cache raw
  responses to JSONL; re-running skips completed trials).
- Every instrument ships with: `PROTOCOL.md` (what it measures, how),
  a calibration test (run against a known system with expected output), and a
  cost table ($ per N trials per model).

### Research discipline (hard rules, learned the expensive way in identity-os)

1. **Preregister before data.** Every experiment directory starts with
   `preregistration.md` (hypothesis, metrics, analysis plan, n, exclusion
   rules) committed BEFORE the first API call.
2. **No pseudo-replication.** Seeds that perturb noise on a deterministic
   pipeline are not independent samples. Report honest n, never p-values
   derived from near-replicas. When in doubt, report raw effect sizes + CIs.
3. **External referents only.** A metric must mean something outside our own
   code. Self-referential metrics (measuring our own state vector with our own
   ruler) are banned as primary outcomes.
4. **Findings ≠ interpretation.** Separate files, like phase-transition-v1 did:
   `findings.md` (with confidence tags STRONG/MEDIUM/WEAK/NULL) vs
   `interpretation.md` (dated, explicitly revisable).
5. **Boring names.** Instruments are named for what they measure, not what they
   evoke. No consciousness, no emotion, no identity. If a name oversells the
   ~50 lines behind it, rename it.
6. **One canonical version per document.** No `_FINAL_v3_SUBMIT` files. Papers
   live in `docs/papers/<name>/paper.md`; history lives in git.
7. **Negative results get written up** with the same care as positive ones.
   A closed research line gets an archive note, not silence.
8. **Update contradicted claims.** When a new result falsifies an older doc in
   this repo, edit the older doc the same day (strike the claim, link the
   evidence). No thesis/paper contradictions allowed to persist.

### Experiment directory template

```
experiments/NN-short-name/
  preregistration.md   # committed before first API call
  protocol.md          # exact procedure, models, prompts
  run/                 # scripts; resumable; raw output to data/
  data/                # raw JSONL (gitignored if large; pointer file committed)
  analysis/            # notebooks/scripts producing figures + numbers
  findings.md          # confidence-tagged results
  interpretation.md    # dated, revisable
```

## Relationship to identity-os

- `../identity-os/` is read-only reference. Code is COPIED here (with an
  origin note), never imported across repos, and simplified on the way in.
- Its engine serves as the calibration specimen: a fully-known deterministic
  system instruments can be validated against.
- Its CLAUDE.md ownership rules do not apply here: Claude Code may edit
  everything in this repo.

## Current priorities (2026-07-30)

1. **Experiment 1**: stress-signature × open post-training recipes (Tülu 3 /
   OLMo staged checkpoints). First deliverable: `experiments/01-stress-signature/preregistration.md`
   + cost estimate for user approval.
2. Port instrument 1 (stress-covariance probe) from identity-os
   `experiments/phase_transition/` into `instruments/stress_probe/`.
3. Judge-bias paper rewrite from existing identity-os data (no new spend).
