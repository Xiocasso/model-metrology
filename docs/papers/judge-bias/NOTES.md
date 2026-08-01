# Submission notes (not part of the paper)

## Venue

- **Primary: JUDGe 2026** (NeurIPS 2026 workshop, "Can We Trust the Judge?").
  Deadline **2026-08-29 AoE**, OpenReview, double-blind, ≥3 reviews,
  non-archival. Full paper 6pp + refs (oral) or short 4pp (poster).
  CFP fit: "sycophancy and self-preference detection"; "negative results,
  practitioner case studies … particularly encouraged."
- arXiv preprint at submission time (non-archival venue permits).
- Backup: EMNLP 2026 cycle.

## Pre-submission checklist

- [ ] Verify author lists: Shi et al. 2406.07791, Ye et al. 2410.02736,
      Chen et al. 2504.03846, Xu et al. 2508.06709 (against arXiv)
- [ ] Cite van Miltenburg et al. 2021 inline in §5.3 item 5
- [ ] Trim abstract to ~200 words
- [ ] Convert to NeurIPS 2026 LaTeX (6pp target); decide full vs short after
      length check
- [ ] ANONYMIZE: remove author line, replace repo URL with
      anonymous.4open.science mirror, rewrite self-citation to the
      originating preprint in anonymized style
- [ ] Make repo public + upload corpus (already built: corpus/corpus.jsonl)
- [ ] Ordinal-robustness check (proportional-odds or rank-based) for the
      neutral-phase effects — reviewer W7a; optional but cheap

## Review outcomes (internal adversarial review, 2026-07-31)

As-drafted estimates: full paper ~55% → ~75% after fixes; short paper ~80%.
Fixes applied 2026-07-31: interaction test (§4.7, p=0.0055), Holm (§4.6),
abstract corrections, provenance note, title mechanism-neutralized,
Gelman & Stern cited, corpus rebuilt with all rationales, Appendix A,
panel-history statement, lineage-independence caveat moved inline.
