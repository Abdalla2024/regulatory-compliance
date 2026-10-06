#!/usr/bin/env python3
"""Render references/decisions.json (canonical) to references/decisions.md (human-readable view)."""

import json
from pathlib import Path

REFS = Path(__file__).resolve().parents[1] / "references"


def main() -> None:
    doc = json.loads((REFS / "decisions.json").read_text(encoding="utf-8"))
    ev = doc["evidence_index"]
    out = ["# Project decision records", "",
           "<!-- Generated from decisions.json by scripts/render_decisions.py; edit the JSON, then re-render. -->", "",
           f"> {doc['approval_note']}", ""]
    for d in doc["decisions"]:
        out += [f"## {d['id']} — {d['summary']}", "", f"*Decided by:* {d['decided_by']}  ", "",
                "**Concern.** " + d["concern"], "", "**Options considered.**", ""]
        out += [f"{i}. {o['option']} — *{o['assessment']}*" for i, o in enumerate(d["options"], 1)]
        out += ["", "**Source basis.**", ""]
        out += [f"- `{e}` ({ev[e]['locator']}): {ev[e]['statement']}" for e in d["source_basis"]]
        out += ["", "**Chosen behaviour.** " + d["chosen_behavior"], ""]
        if d.get("interview_interpretation_preserved"):
            out += ["**Interview interpretation preserved.** " + d["interview_interpretation_preserved"], ""]
        out += ["**Rationale.** " + d["rationale"], "", "**Trade-offs.**", ""]
        out += [f"- {t}" for t in d["tradeoffs"]]
        out += ["", "**Downstream effect.**", ""]
        out += [f"- {t}" for t in d["downstream_effect"]]
        out += ["", f"*Recorded in snapshot stage(s):* {', '.join(d['stages'])}", ""]
    (REFS / "decisions.md").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {REFS / 'decisions.md'}")


if __name__ == "__main__":
    main()
