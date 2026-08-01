"""Build the release corpus for the judge-triangulation paper.

Merges, per (arm, replicate, turn):
  - per-rep dialog files: user prompt, agent response, ORIGINAL Sonnet judge
    (score + rationale), keyword hits
  - together regrade: gpt_score, llama_score, llama rationale, phase
  - openai regrade: gpt rationale

Outputs:
  corpus.jsonl            (2,000 rows, all fields)
  divergent_examples.md   (top strong-adversarial rows by Sonnet-consensus gap)

Verifies: 2,000 merged rows; per-rep Sonnet score == regrade sonnet_score.
"""

from __future__ import annotations

import json
from pathlib import Path

SRC = Path(r"C:\Users\Gebruiker\OneDrive\桌面\identity-os\research\data")
OUT_DIR = Path(__file__).resolve().parent


def load_regrades() -> dict:
    merged: dict[tuple, dict] = {}
    for line in (SRC / "llm_persona_together_regrade.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        merged[(r["arm"], r["replicate"], r["turn"])] = {
            "phase": r["phase"],
            "sonnet_score_regrade": r["sonnet_score"],
            "gpt_score": r["gpt_score"],
            "llama_score": r["llama_score"],
            "llama_reason": r.get("llama_reason", ""),
            "keyword_net": r["keyword_net"],
        }
    for line in (SRC / "llm_persona_openai_regrade.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        key = (r["arm"], r["replicate"], r["turn"])
        merged[key]["gpt_reason"] = r.get("gpt_reason", "")
    return merged


def main() -> int:
    regrades = load_regrades()
    rows = []
    mismatches = 0
    for f in sorted(SRC.glob("llm_persona/*_rep*.jsonl")):
        for line in f.open(encoding="utf-8"):
            r = json.loads(line)
            key = (r["arm"], r["replicate"], r["turn"])
            if key not in regrades:
                continue
            reg = regrades[key]
            sonnet_orig = r["judge"]["score"]
            if sonnet_orig != reg["sonnet_score_regrade"]:
                mismatches += 1
            rows.append({
                "arm": r["arm"],
                "replicate": r["replicate"],
                "turn": r["turn"],
                "phase": reg["phase"],
                "user": r["user"],
                "response": r["response"],
                "sonnet_score": sonnet_orig,
                "sonnet_reason": r["judge"].get("reason", ""),
                "gpt_score": reg["gpt_score"],
                "gpt_reason": reg.get("gpt_reason", ""),
                "llama_score": reg["llama_score"],
                "llama_reason": reg["llama_reason"],
                "keyword_net": reg["keyword_net"],
            })

    assert len(rows) == 2000, f"expected 2000 merged rows, got {len(rows)}"
    assert mismatches == 0, f"{mismatches} sonnet score mismatches vs regrade file"

    rows.sort(key=lambda r: (r["arm"], r["replicate"], r["turn"]))
    with (OUT_DIR / "corpus.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Divergent strong-adversarial examples: largest Sonnet-minus-consensus gap
    strong = [r for r in rows if r["phase"] == "strong_adv"]
    for r in strong:
        r["_gap"] = r["sonnet_score"] - (r["gpt_score"] + r["llama_score"]) / 2
    strong.sort(key=lambda r: -r["_gap"])

    lines = [
        "# Divergent strong-adversarial examples",
        "",
        "Top rows by (sonnet - mean(gpt, llama)) gap. Full records in corpus.jsonl.",
        "",
    ]
    for r in strong[:5]:
        lines += [
            f"## {r['arm']} rep{r['replicate']} turn{r['turn']} — "
            f"Sonnet {r['sonnet_score']} vs GPT {r['gpt_score']} / "
            f"Llama {r['llama_score']} (gap +{r['_gap']:.1f})",
            "",
            f"**User**: {r['user'][:300]}",
            "",
            f"**Response**: {r['response'][:600]}",
            "",
            f"**Sonnet**: {r['sonnet_reason'][:300]}",
            "",
            f"**GPT-4o**: {r['gpt_reason'][:300]}",
            "",
            f"**Llama**: {r['llama_reason'][:300]}",
            "",
        ]
    (OUT_DIR / "divergent_examples.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(f"corpus.jsonl: {len(rows)} rows; score mismatches: {mismatches}")
    print(f"top-5 strong_adv gaps: {[round(r['_gap'],1) for r in strong[:5]]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
