#!/usr/bin/env python3
"""One-off, post-run redaction of archived POLICY captures (developer instruction, 2026-10-06).

Runs archived before the D-008 revision saved Notion's page-chunk response including the workspace member table
(recordMap.notion_user: third-party names, user IDs, profile-photo links). This removes only that table, using the
same function as the live adapter, and records the change in each run's history-manifest.json. It does not touch
run IDs, snapshots, decisions or drafts. The redacted file is documented as redacted; it is never presented as the
originally captured bytes. Idempotent: already-redacted files are skipped.

    python3 regulatory-change-impact-brief/scripts/redact_history_notion_users.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rcib.sources import NOTION_REDACTED_TABLES, notion_ordered_blocks, redact_notion_chunk  # noqa: E402
from rcib.util import read_gzip, read_json, sha256_bytes, sha256_file, utc_now, write_gzip, write_json  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HISTORY = ROOT / "deliverables" / "history"
REASON = ("Removal of incidental third-party Notion workspace-member metadata (names, user IDs, profile-photo links) "
          "before repository publication. The table carries no policy content, identity, version or date information.")


def main() -> int:
    page_id = next(r for r in read_json(ROOT / "regulatory-change-impact-brief" / "references" / "source-routes.json")
                   ["sources"] if r["name"] == "POLICY")["expect"]["page_id"]
    for run_dir in sorted(p for p in HISTORY.iterdir() if p.is_dir()):
        manifest_path = run_dir / "history-manifest.json"
        manifest = read_json(manifest_path)
        s02 = read_json(run_dir / "snapshots" / "02-source-capture.json")
        attempts = {a["local_reference"].split("/")[-1]: a for a in s02["state"]["sources"] if a.get("local_reference")}
        entries = manifest.get("post_run_redactions", [])
        for chunk in sorted((run_dir / "sources").glob("POLICY-chunk-*.json.gz")):
            raw = read_gzip(chunk)
            data = json.loads(raw)
            if not any(t in data.get("recordMap", {}) for t in NOTION_REDACTED_TABLES):
                print(f"skip (already redacted): {chunk.relative_to(ROOT)}")
                continue
            redacted, removed = redact_notion_chunk(data)
            new_raw = json.dumps(redacted, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            # Prove the redaction keeps every policy extract this historical run relied on.
            ext = read_json(run_dir / "sources" / "POLICY.extracts.json")["extracts"]
            derived = [(b["id"], b["text"]) for b in notion_ordered_blocks(redacted["recordMap"]["block"], page_id)]
            if derived != [(e["block_id"], e["text"]) for e in ext]:
                print(f"ABORT: redaction would change extracts for {chunk}")
                return 1
            original_file_hash = sha256_file(chunk)
            att = attempts.get(chunk.name, {})
            write_gzip(chunk, new_raw)
            entries.append({
                "file": chunk.relative_to(ROOT).as_posix(),
                "stage02_attempt_id": att.get("id"),
                "redacted_at": utc_now(),
                "reason": REASON,
                "removed": {"recordMap tables": removed},
                "original_content_sha256": sha256_bytes(raw),
                "original_content_sha256_matches_stage02_content_hash": sha256_bytes(raw) == att.get("content_hash"),
                "original_gzip_file_sha256": original_file_hash,
                "redacted_content_sha256": sha256_bytes(new_raw),
                "redacted_gzip_file_sha256": sha256_file(chunk),
                "extracts_reproduced_after_redaction": True,
                "notice": ("This historical artifact was redacted after the original run. Its current hash intentionally "
                           "differs from the content_hash recorded in this run's stage 02 snapshot, which still records "
                           "the original captured bytes. The redacted file is not the original capture; run ID, "
                           "snapshot IDs, snapshots, decisions, register, brief and calendar are unchanged."),
            })
            print(f"redacted: {chunk.relative_to(ROOT)} removed {removed}")
        if entries:
            manifest["post_run_redactions"] = entries
            write_json(manifest_path, manifest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
