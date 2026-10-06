#!/usr/bin/env python3
"""One-off, post-run redaction of signed redirect URLs in archived stage 02 snapshots (developer instruction,
2026-10-06).

Runs archived before the adapter fix recorded Google's signed, time-limited export redirect
(https://doc-…-sheets.googleusercontent.com/export/<signature>/<token>/<expiry>/<owner account id>/…) as an
attempt's final_url. This replaces only those final_url values with the host-only form the live adapter now
records (rcib.sources.safe_final_url), and documents the change in history-manifest.json. Nothing else in the
snapshot changes. The run's stage 03 predecessor hash still records the original stage 02 bytes; the manifest states
this explicitly. Idempotent.

    python3 regulatory-change-impact-brief/scripts/redact_history_signed_urls.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rcib.sources import safe_final_url  # noqa: E402
from rcib.util import read_json, sha256_file, utc_now, write_json  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HISTORY = ROOT / "deliverables" / "history"
REASON = ("Removal of signed, time-limited Google export redirect URLs (access signature, expiry and the sheet owner's "
          "account ID) from recorded final_url values before repository publication. The requested locator, "
          "retrieval status, content hash and preserved bytes are unchanged.")


def main() -> int:
    for run_dir in sorted(p for p in HISTORY.iterdir() if p.is_dir()):
        snap_path = run_dir / "snapshots" / "02-source-capture.json"
        snap = read_json(snap_path)
        changed = []
        for a in snap["state"]["sources"]:
            new = safe_final_url(a.get("final_url"), a["locator"])
            if new != a.get("final_url"):
                changed.append(a["id"])
                a["final_url"] = new
        if not changed:
            print(f"skip (no signed URLs): {snap_path.relative_to(ROOT)}")
            continue
        s03 = read_json(run_dir / "snapshots" / "03-authority-and-timing.json")
        original = sha256_file(snap_path)
        write_json(snap_path, snap)
        manifest_path = run_dir / "history-manifest.json"
        manifest = read_json(manifest_path)
        manifest.setdefault("post_run_redactions", []).append({
            "file": snap_path.relative_to(ROOT).as_posix(),
            "redacted_at": utc_now(),
            "reason": REASON,
            "removed": {"final_url signed redirect paths": changed},
            "original_file_sha256": original,
            "original_file_sha256_matches_stage03_predecessor": original == s03["predecessor"]["sha256"],
            "redacted_file_sha256": sha256_file(snap_path),
            "notice": ("This historical snapshot was redacted after the original run. Its current hash intentionally "
                       "differs from the sha256 recorded as the predecessor in this run's 03-authority-and-timing.json, "
                       "which still identifies the original stage 02 bytes. Only the listed final_url values changed; "
                       "run ID, snapshot ID, records, statuses, content hashes and all other snapshots are unchanged."),
        })
        write_json(manifest_path, manifest)
        print(f"redacted: {snap_path.relative_to(ROOT)} ({len(changed)} final_url values)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
