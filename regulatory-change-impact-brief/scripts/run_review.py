#!/usr/bin/env python3
"""End-to-end command for the regulatory-change-impact-brief skill.

    python regulatory-change-impact-brief/scripts/run_review.py            # full run (fresh live source attempts)
    python regulatory-change-impact-brief/scripts/run_review.py --verify   # read-only inspection of the current bundle

Exit codes: 0 = complete or partial draft validated; 3 = blocked draft package produced (conclusions withheld);
1 = failed (technical failure or verification failure; see deliverables/failures/ and run-verification.json).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rcib import pipeline, validate  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                    help="repository root containing snapshot.schema.json (default: this repository)")
    ap.add_argument("--reason", help="change/retry reason recorded in stage 01 (default: derived from the prior run)")
    ap.add_argument("--responses", type=Path, help="verified reviewer responses JSON supplied through the facilitator's "
                    "channel; applied only when their binding validates")
    ap.add_argument("--verify", action="store_true", help="inspect the existing bundle read-only and exit")
    args = ap.parse_args()
    root = args.root.resolve()
    if args.verify:
        p = pipeline.Paths(root)
        result = validate.verify_bundle(root, p.deliverables, p.schema)
        print(f"run_id: {result['run_id']}  run status: {result['run_status']}  "
              f"verification: {'OK' if result['ok'] else 'FAILED'} ({len(result['checks'])} checks)")
        for c in result["failed"]:
            print(f"  - {c['id']}: {c['summary']} — {c['detail']}")
        return 0 if result["ok"] else 1
    return pipeline.run(root, reason=args.reason, responses=args.responses)


if __name__ == "__main__":
    sys.exit(main())
