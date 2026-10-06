"""End-to-end run: inspect and archive the previous run, capture sources, write the seven snapshots
at their boundaries, write the three drafts, bind review requests, then verify the whole bundle."""

from __future__ import annotations

import datetime as dt
import json
import secrets
import shutil
import traceback
from pathlib import Path

from . import SCHEMA_VERSION, analysis, outputs, sources, validate
from .util import read_json, rel, sha256_bytes, sha256_file, utc_now, write_json

SKILL_DIR = Path(__file__).resolve().parents[2]
REFS = SKILL_DIR / "references"


class Paths:
    def __init__(self, root: Path):
        self.root = root
        self.deliverables = root / "deliverables"
        self.snapshots = self.deliverables / "snapshots"
        self.sources = self.deliverables / "sources"
        self.history = self.deliverables / "history"
        self.failures = self.deliverables / "failures"
        self.schema = root / "snapshot.schema.json"

    def final(self, key: str) -> Path:
        return self.deliverables / validate.FINAL_FILES[key]


ARCHIVABLE = ["snapshots", "sources", "impact-register.csv", "compliance-brief.md", "action-calendar.ics",
              "run-verification.json"]


# ------------------------------------------------------------------ history

def archive_previous(p: Paths) -> dict | None:
    present = [n for n in ARCHIVABLE if (p.deliverables / n).exists()]
    if not present:
        return None
    inspection = validate.verify_bundle(p.root, p.deliverables, p.schema)
    old_id = inspection.get("run_id")
    old_status = inspection.get("run_status")
    if not old_id:
        old_id = "unidentified-" + utc_now().replace(":", "").replace("-", "")
    dest = p.history / old_id
    n = 1
    while dest.exists():
        n += 1
        dest = p.history / f"{old_id}-copy{n}"
    dest.mkdir(parents=True)
    for name in present:
        shutil.move(str(p.deliverables / name), str(dest / name))
    missing = [x for x in ARCHIVABLE[:5] if x not in present]
    manifest = {
        "archived_run_id": old_id, "archived_at": utc_now(), "archived_run_status": old_status,
        "files_archived": present, "expected_files_missing_at_archive_time": missing,
        "integrity_at_archive_time": {"ok": inspection["ok"],
                                      "failed_checks": [{"id": c["id"], "summary": c["summary"], "detail": c["detail"]}
                                                        for c in inspection["failed"]]},
        "note": "Retained exactly as found before the superseding run; missing or damaged evidence is recorded, not repaired.",
    }
    write_json(dest / "history-manifest.json", manifest)
    return {"run_id": old_id, "status": old_status, "path": rel(dest, p.root), "inspection_ok": inspection["ok"],
            "failed_checks": manifest["integrity_at_archive_time"]["failed_checks"], "missing": missing}


# ------------------------------------------------------------------ snapshots

def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, set):
        return sorted(obj)
    return obj


class SnapshotWriter:
    def __init__(self, p: Paths, run_id: str):
        self.p, self.run_id = p, run_id
        self.prev: dict | None = None
        self.written: list[dict] = []

    def write(self, seq: int, status: str, state: dict, consumed: list[str], unresolved: list[dict],
              decisions: list[dict]) -> dict:
        stage = validate.STAGES[seq - 1]
        snap = {
            "schema_version": SCHEMA_VERSION,
            "snapshot_id": f"{self.run_id}-S{seq:02d}",
            "run_id": self.run_id,
            "stage": stage,
            "sequence": seq,
            "created_at": utc_now(),
            "status": status,
            "predecessor": None if self.prev is None else {
                "snapshot_id": self.prev["snapshot_id"], "path": self.prev["path"], "sha256": self.prev["sha256"]},
            "consumed_record_ids": sorted(set(consumed)),
            "produced_record_ids": [],
            "state": _clean(state),
            "unresolved": _clean(unresolved),
            "decisions": _clean(decisions),
        }
        snap["produced_record_ids"] = sorted(validate.record_ids(snap))
        path = self.p.snapshots / validate.SNAPSHOT_FILES[seq - 1]
        digest = write_json(path, snap)
        self.prev = {"snapshot_id": snap["snapshot_id"], "path": rel(path, self.p.root), "sha256": digest}
        self.written.append(snap)
        return snap


def _decisions_for(stage: str, decisions: list[dict], emitted: set) -> list[dict]:
    out = []
    for d in decisions:
        if d["id"] not in emitted and d["stages"][0] == stage:
            out.append(d)
            emitted.add(d["id"])
    return out


def _ids(records) -> list[str]:
    return [r["id"] for r in records]


# ------------------------------------------------------------------ responses

def load_responses(path: Path | None, p: Paths, approvals: list[dict], requests: list[dict]) -> tuple[list, list]:
    """Apply verified reviewer responses whose binding validates; leave the rest unresolved (D-006)."""
    if not path:
        return [], []
    applied, unmatched = [], []
    data = read_json(path)
    req_by_id = {r["request_id"]: r for r in requests}
    apr_by_id = {a["id"]: a for a in approvals}
    for resp in data.get("responses", []):
        need = ("response_id", "request_id", "run_id", "reviewer_role", "reviewer_identity", "responded_at",
                "outcome", "artifact_path", "artifact_sha256", "channel")
        problem = None
        if any(k not in resp for k in need):
            problem = f"missing fields {[k for k in need if k not in resp]}"
        elif resp["outcome"] not in ("approved", "rejected"):
            problem = f"outcome '{resp['outcome']}' not approved/rejected"
        else:
            s07 = None
            for cand in [p.history / resp["run_id"] / "snapshots" / "07-publication-validation.json"]:
                if cand.exists():
                    s07 = read_json(cand)
            if s07 is None:
                problem = f"no stage 07 snapshot for run {resp['run_id']} to validate the binding"
            else:
                b = next((x for x in s07["state"].get("review_bindings", []) if x["request_id"] == resp["request_id"]), None)
                if b is None:
                    problem = "request not bound in that run"
                elif not any(x["sha256"] == resp["artifact_sha256"] and x["path"].endswith(resp["artifact_path"])
                             for x in b["artifacts"]):
                    problem = "artifact path/hash does not match the bound draft"
                elif resp["request_id"] not in req_by_id:
                    problem = "request does not exist in the current run"
                elif req_by_id[resp["request_id"]]["required_reviewer"] != resp["reviewer_role"]:
                    problem = "reviewer role does not match the required reviewer"
        if problem:
            unmatched.append({"id": f"RESP-UNMATCHED-{resp.get('response_id', len(unmatched) + 1)}",
                              "summary": f"Reviewer response not applied: {problem}.", "evidence_ids": [],
                              "owner": "Operations", "rationale": "Unmatched responses stay unresolved (assignment).",
                              "response": resp})
            continue
        apr = apr_by_id.get(req_by_id[resp["request_id"]]["approval_record"])
        apr["status"] = resp["outcome"]
        apr["response"] = {k: resp.get(k) for k in need + ("reasons", "conditions")}
        apr["response"]["binding_note"] = f"Response validated against the stage 07 binding of run {resp['run_id']}."
        applied.append(resp["response_id"])
    return applied, unmatched


# ------------------------------------------------------------------ run

def run(root: Path, reason: str | None = None, responses: Path | None = None) -> int:
    p = Paths(root)
    scope = read_json(REFS / "scope.json")
    routes = read_json(REFS / "source-routes.json")["sources"]
    rules = read_json(REFS / "rules.json")
    dec_doc = read_json(REFS / "decisions.json")
    decisions = dec_doc["decisions"]
    as_of_date = dt.date.fromisoformat(scope["as_of_date"])
    run_id = "RCIB-" + utc_now().replace("-", "").replace(":", "") + "-" + secrets.token_hex(2)
    started = utc_now()
    stage_reached = "pre-run"
    try:
        prior = archive_previous(p)
        prior_s02 = None
        if prior:
            cand = p.root / prior["path"] / "snapshots" / "02-source-capture.json"
            try:
                prior_s02 = read_json(cand) if cand.exists() else None
            except ValueError:
                prior_s02 = None
        change_reason = reason or ("initial run" if not prior else
                                   f"re-run superseding {prior['run_id']} (prior status {prior['status']}; prior bundle "
                                   f"integrity {'ok' if prior['inspection_ok'] else 'FAILED: ' + '; '.join(c['id'] for c in prior['failed_checks'][:5])})")
        p.snapshots.mkdir(parents=True, exist_ok=True)
        p.sources.mkdir(parents=True, exist_ok=True)
        sw = SnapshotWriter(p, run_id)
        emitted: set = set()

        # ---------------- stage 01
        stage_reached = "scope"
        evidence_records = [{"id": k, "summary": v["statement"], "evidence_ids": [], "locator": v["locator"],
                             "owner": None, "rationale": None} for k, v in dec_doc["evidence_index"].items()]
        scope_records = [{"id": "SCOPE-REVIEW", "summary": scope["review_type"], "evidence_ids": ["ASSIGN-BLOCK"]},
                         {"id": "SCOPE-AS-OF", "summary": f"As-of {scope['as_of']} ({scope['as_of_note']})",
                          "evidence_ids": ["INT1-L276"]}]
        scope_records += [{"id": f"SCOPE-SYS-{s}", "summary": f"{s} in scope (eight registered EU programme systems)",
                           "evidence_ids": []} for s in scope["systems_in_scope"]]
        route_records = [{"id": f"ROUTE-{r['name']}", "summary": f"{r['name']}: {r['summary']}", "evidence_ids": [],
                          "locator": r["url"], "authority_class": r["authority_class"], "required": True,
                          "adapter": r["adapter"]} for r in routes]
        s01_state = {
            "as_of": scope["as_of"], "as_of_date": scope["as_of_date"], "review_type": scope["review_type"],
            "organisation": scope["organisation"], "systems_in_scope": scope["systems_in_scope"],
            "audiences": scope["audiences"], "approval_gates": scope["approval_gates"],
            "resolution_owners": scope["resolution_owners"],
            "supersedes_run_id": prior["run_id"] if prior else None, "change_reason": change_reason,
            "prior_run_inspection": prior, "run_started_at": started,
            "scope_records": scope_records, "source_routes": route_records, "project_evidence": evidence_records,
            "decision_approval_note": dec_doc["approval_note"],
        }
        prior_unres = []
        if prior and not prior["inspection_ok"]:
            prior_unres.append({"id": "PRIOR-RUN-INTEGRITY", "summary": f"Superseded run {prior['run_id']} failed "
                                "integrity checks when archived; retained as found.", "evidence_ids": [],
                                "owner": "Operations", "rationale": "Pre-existing missing/corrupt evidence recorded honestly.",
                                "failed_checks": prior["failed_checks"]})
        sw.write(1, "complete", s01_state, [], prior_unres, _decisions_for("scope", decisions, emitted))

        # ---------------- stage 02
        stage_reached = "source-capture"
        ctx = sources.Ctx(p.root, p.sources, as_of_date)
        caps = sources.capture_all(routes, ctx)
        attempts = [a for c in caps.values() for a in c.attempts]
        for a in attempts:
            a["evidence_ids"] = [f"ROUTE-{a['source_name']}"]
        extract_records = []
        for c in caps.values():
            used = analysis.used_attempt_id(c)
            for e in c.extracts.values():
                extract_records.append({"id": e["id"], "summary": e["text"][:240] or "(empty block)",
                                        "evidence_ids": [used] if used else [], "source_name": c.name,
                                        "locator": e["locator"], "text": e["text"],
                                        "extracts_file": f"deliverables/sources/{c.name}.extracts.json"})
        summary_records = []
        source_versions = {}
        for name, c in caps.items():
            used = next((a for a in c.attempts if a["used_as_evidence"]), c.attempts[-1] if c.attempts else None)
            ext_path = p.sources / f"{name}.extracts.json"
            source_versions[name] = {"status": c.status, "content_hash": used["content_hash"] if used else None,
                                     "extracts_sha256": sha256_file(ext_path) if ext_path.exists() else None,
                                     "version": {k: v for k, v in c.version.items() if k not in ("columns",)},
                                     "retrieved_at": used["retrieved_at"] if used else None}
            summary_records.append({"id": f"SRC-{name}", "summary": f"{name} overall: {c.status}"
                                    + (f" — {'; '.join(c.reasons)}" if c.reasons else ""),
                                    "evidence_ids": [a["id"] for a in c.attempts], "source_name": name,
                                    "authority_class": c.route["authority_class"], "retrieval_status": c.status,
                                    "required": True, "data_quality_issues": c.issues,
                                    "owner": "Operations" if c.route["authority_class"] == "company" else "European Commission",
                                    "rationale": "Overall status is the status of the attempt used as evidence."})
        changes = None
        if prior_s02:
            old = prior_s02["state"].get("source_versions", {})
            # Claim-bearing extracts are compared; raw bytes of EUR-Lex/Notion responses embed per-request tokens.
            changed = sorted(n for n, v in source_versions.items()
                             if (old.get(n) or {}).get("extracts_sha256") != v["extracts_sha256"])
            raw_changed = sorted(n for n, v in source_versions.items()
                                 if (old.get(n) or {}).get("content_hash") != v["content_hash"])
            changes = {"superseded_run_id": prior["run_id"], "changed_sources": changed,
                       "comparison_basis": "sha256 of claim-bearing extracts (content_hash of raw bytes also differs "
                                           f"for: {raw_changed or 'none'}, e.g. per-request page tokens)",
                       "unchanged_sources": sorted(set(source_versions) - set(changed)),
                       "earliest_changed_basis": "source-capture" if changed else "none (inputs unchanged)",
                       "recomputation": "All stages 03-07 and all three drafts are recomputed from the fresh captures."}
        failed_sources = [n for n, c in caps.items() if not c.usable]
        run_blocked = bool(failed_sources)
        src_unres = [{"id": f"SRCISSUE-{n}", "summary": f"Required source {n} is {caps[n].status}: "
                      + ("; ".join(caps[n].reasons) or "no detail"), "evidence_ids": [a["id"] for a in caps[n].attempts],
                      "owner": "Operations", "rationale": "Blocks the run (D-002).",
                      "resolution_need": f"Restore a suitable live read of {n}; re-run the documented command."}
                     for n in failed_sources]
        for n, c in caps.items():
            for iss in c.issues:
                src_unres.append({"id": f"SRCISSUE-{n}-{iss['record_id']}-{iss['field']}",
                                  "summary": f"{n} row {iss['row']} {iss['field']}='{iss['value']}': {iss['problem']}",
                                  "evidence_ids": [f"EXT-{n}-{iss['record_id']}"], "owner": "Operations",
                                  "rationale": "Reported, not guessed (assignment: changed inputs)."})
        s02 = sw.write(2, "blocked" if run_blocked else "complete",
                       {"sources": attempts, "source_summaries": summary_records, "extracts": extract_records,
                        "source_versions": source_versions, "changes_since_superseded_run": changes,
                        "as_of_date": scope["as_of_date"],
                        "time_separation_note": "retrieved_at is the actual retrieval time; in-source revisions and "
                                                "effective dates are in version_metadata; the review date is fixed."},
                       _ids(route_records) + ["SCOPE-AS-OF"] + _ids(scope_records[2:]), src_unres,
                       _decisions_for("source-capture", decisions, emitted))

        # ---------------- stage 03
        stage_reached = "authority-and-timing"
        s03_state = analysis.authority_and_timing(caps, rules, as_of_date)
        s03_consumed = [a["id"] for n in analysis.BINDING + analysis.ADVISORY for a in caps[n].attempts]
        s03_consumed += [e for r in s03_state["binding_rules"] + s03_state["timing_rules"] + s03_state["guidance_context"]
                         for e in r["evidence_ids"] if e.startswith("EXT-")]
        s03_consumed += ["D-002", "SCOPE-AS-OF"]
        s03_status = "blocked" if run_blocked or s03_state["authority_blockers"] else "complete"
        if s03_state["authority_blockers"] and not run_blocked:
            run_blocked = True  # unreconciled binding text is unsuitable authority (D-002)
        sw.write(3, s03_status, s03_state, s03_consumed, s03_state["authority_blockers"],
                 _decisions_for("authority-and-timing", decisions, emitted))

        # ---------------- stage 04
        stage_reached = "evidence-reconciliation"
        s04 = analysis.evidence_reconciliation(caps, rules, scope, as_of_date)
        s04_consumed = [e for c in ("SYSTEMS", "EVIDENCE", "POLICY", "CALENDAR") for e in caps[c].extracts]
        s04_consumed += [a["id"] for c in ("SYSTEMS", "EVIDENCE", "POLICY") for a in caps[c].attempts]
        s04_consumed += _ids(scope_records[2:])
        s04_unres = s04["conflicts"] + s04["evidence_gaps"]
        s04_status = "blocked" if run_blocked else ("partial" if s04_unres else "complete")
        sw.write(4, s04_status, s04, s04_consumed, s04_unres, _decisions_for("evidence-reconciliation", decisions, emitted))

        # ---------------- stage 05
        stage_reached = "impact-analysis"
        s05 = analysis.impact_analysis(caps, rules, scope, s03_state, s04, run_blocked)
        valid_up = set(validate.record_ids(sw.written[2])) | set(validate.record_ids(sw.written[3])) | \
            set(validate.record_ids(sw.written[1]))
        for i in s05["impacts"]:
            i["evidence_ids"] = sorted(e for e in i["evidence_ids"] if e in valid_up)
        s05_consumed = sorted({e for i in s05["impacts"] for e in i["evidence_ids"]} | {"D-002"})
        s05_unres = s05["conflicts"] + s05["unresolved_items"]
        s05_status = "blocked" if run_blocked else ("partial" if s05_unres else "complete")
        sw.write(5, s05_status, s05, s05_consumed, s05_unres, _decisions_for("impact-analysis", decisions, emitted))

        # ---------------- stage 06
        stage_reached = "actions-and-approvals"
        s06 = analysis.actions_and_approvals(caps, rules, scope, s05, run_id, source_versions)
        applied, unmatched = load_responses(responses, p, s06["approval_requirements"], s06["review_requests"])
        s06["responses_applied"] = applied
        s06["responses_unmatched"] = unmatched
        s06_consumed = sorted({i["id"] for i in s05["impacts"]} |
                              {e for a in s06["proposed_actions"] for e in a["evidence_ids"] if e.startswith("EXT-CALENDAR")}
                              | {"SCOPE-REVIEW"})
        s06_unres = s06["escalations"] + unmatched
        s06_status = "blocked" if run_blocked else ("partial" if s06_unres else "complete")
        s06_snap = sw.write(6, s06_status, s06, s06_consumed, s06_unres,
                            _decisions_for("actions-and-approvals", decisions, emitted))

        # ---------------- final drafts
        stage_reached = "publication-validation (drafts)"
        actions = s06_snap["state"]["proposed_actions"]
        events = outputs.calendar_events(actions, run_blocked)
        if run_blocked:
            run_status = "blocked"
            status_reason = ("required source(s) not suitably retrieved or binding text unreconciled: "
                             + ", ".join(failed_sources or [b["id"] for b in s03_state["authority_blockers"]])
                             + "; formal Article 50 conclusions withheld.")
        elif s05_unres or unmatched:
            run_status = "partial"
            status_reason = (f"all ten required sources retrieved and verified; {len(s05['conflicts'])} conflicting and "
                             f"{len(s05['unresolved_items'])} unresolved register rows remain.")
        else:
            run_status = "complete"
            status_reason = "all ten required sources retrieved and verified; every in-scope item reached a supported state."
        limitations = _limitations(caps, scope, run_blocked)
        source_summary = [{"name": n, "authority_class": caps[n].route["authority_class"], "status": caps[n].status,
                           "retrieved_at": source_versions[n]["retrieved_at"],
                           "version": _version_text(n, caps[n]), "content_hash": source_versions[n]["content_hash"]}
                          for n in caps]
        reg_rows = outputs.register_rows(run_id, sw.written[4]["state"]["impacts"], actions)
        register = outputs.render_register(reg_rows)
        ics = outputs.render_ics(run_id, sw.written[0]["created_at"], events)
        brief = outputs.render_brief({
            "run_id": run_id, "run_status": run_status, "run_status_reason": status_reason,
            "as_of_date": scope["as_of_date"], "created_at": started,
            "supersedes_run_id": prior["run_id"] if prior else None, "change_reason": change_reason,
            "stage03": sw.written[2]["state"], "stage04": sw.written[3]["state"], "stage05": sw.written[4]["state"],
            "stage06": s06_snap["state"], "source_summary": source_summary, "limitations": limitations,
            "calendar_event_ids": [a["id"] for a in events], "decisions": decisions,
            "responses_note": (f"Reviewer responses applied: {applied or 'none'}; unmatched (unresolved): "
                               f"{[u['id'] for u in unmatched] or 'none'}.") if responses else None})
        p.final("ART-REGISTER").write_bytes(register)
        p.final("ART-BRIEF").write_bytes(brief)
        p.final("ART-CALENDAR").write_bytes(ics)

        # ---------------- stage 07 (after writing)
        stage_reached = "publication-validation"
        validator = validate.schema_validator(p.schema)
        chain, _ = validate.chain_checks(p.root, p.snapshots, validator, upto=6)
        ev_checks = validate.source_evidence_checks(p.root, s02)
        xfile = validate.cross_file_checks(run_id, scope["as_of_date"], p.final("ART-REGISTER").read_bytes(),
                                           p.final("ART-BRIEF").read_bytes(), p.final("ART-CALENDAR").read_bytes(),
                                           sw.written[4], s06_snap, events)
        checks = chain + ev_checks + xfile
        art_checks = {"ART-REGISTER": ["CHK-REGISTER-FORMAT", "CHK-REGISTER-ROWS", "CHK-REGISTER-AGREEMENT"],
                      "ART-BRIEF": ["CHK-BRIEF-AGREEMENT"],
                      "ART-CALENDAR": ["CHK-CALENDAR-FORMAT", "CHK-CALENDAR-AGREEMENT"]}
        artifacts = []
        for key, cids in art_checks.items():
            ok = all(c["passed"] for c in checks if c["id"] in cids)
            artifacts.append({"id": key, "path": rel(p.final(key), p.root), "sha256": sha256_file(p.final(key)),
                              "validation_status": "valid" if ok else "invalid",
                              "summary": f"Final draft {validate.FINAL_FILES[key]}", "evidence_ids": cids})
        technical_fail = any(not c["passed"] for c in checks)
        if technical_fail:
            run_status = "failed"
        publication = {"blocked": "blocked", "partial": "validated", "complete": "validated",
                       "failed": "failed"}[run_status]
        bindings = [{"id": f"BIND-{r['request_id']}", "summary": f"{r['request_id']} bound to the final drafts "
                     "reviewed under this run (detached binding; the brief does not contain its own hash).",
                     "evidence_ids": [r["request_id"]], "request_id": r["request_id"],
                     "required_reviewer": r["required_reviewer"], "run_id": run_id,
                     "artifacts": [{"path": a["path"], "sha256": a["sha256"]} for a in artifacts],
                     "delivery_status": "prepared; not sent"} for r in s06_snap["state"]["review_requests"]]
        open_items = [{"id": f"OPEN-{i['id']}", "summary": f"{i['state']}: {i['rationale']}", "evidence_ids": [i["id"]],
                       "owner": i["owner"], "rationale": "Remains open in the published draft.",
                       "resolution_need": i["resolution_need"]}
                      for i in sw.written[4]["state"]["impacts"] if i["state"] in ("conflicting", "unresolved")]
        s07_state = {"artifacts": artifacts, "validation_checks": checks, "publication_status": publication,
                     "run_status": run_status, "run_status_reason": status_reason,
                     "publication_meaning": "Draft validation only; not human approval and not external publication.",
                     "calendar_event_uids": [a["uid"] for a in events], "review_bindings": bindings,
                     "post_write_verification": "deliverables/run-verification.json (written after this snapshot)"}
        s07_consumed = sorted({a["id"] for a in actions} | {r["id"] for r in s06_snap["state"]["review_requests"]}
                              | {a["id"] for a in s06_snap["state"]["approval_requirements"]} | {"D-002"})
        sw.write(7, run_status, s07_state, s07_consumed, open_items,
                 _decisions_for("publication-validation", decisions, emitted))

        # ---------------- post-write verification of the actual bundle
        result = validate.verify_bundle(p.root, p.deliverables, p.schema)
        write_json(p.deliverables / "run-verification.json", {
            "run_id": run_id, "verified_at": utc_now(), "ok": result["ok"], "run_status": run_status,
            "publication_status": publication, "checks_run": len(result["checks"]),
            "failed_checks": result["failed"]})
        _print_summary(run_id, run_status, publication, caps, sw.written[4]["state"]["impacts"], actions, events, result)
        if not result["ok"] or run_status == "failed":
            _record_failure(p, run_id, "post-write verification", "; ".join(c["id"] for c in result["failed"][:10]),
                            "Inspect run-verification.json, repair the cause, and re-run the documented command "
                            "(fresh source attempts; this run is archived to history).")
            return 1
        return 3 if run_status == "blocked" else 0
    except Exception as e:
        _record_failure(p, run_id, stage_reached, f"{type(e).__name__}: {e}", "Fix the cause and re-run the documented "
                        "command; prior evidence is retained under deliverables/history/.", traceback.format_exc())
        print(f"FAILED at stage {stage_reached}: {type(e).__name__}: {e}")
        return 1


def _record_failure(p: Paths, run_id: str, stage: str, error: str, recovery: str, tb: str | None = None) -> None:
    write_json(p.failures / f"{run_id}.json", {
        "run_id": run_id, "failed_at": utc_now(), "affected_stage": stage, "error": error,
        "recovery_action": recovery, "next_owner": "Project developer / Operations", "traceback": tb,
        "outputs_state": "Partial snapshots or drafts from this run, if any, remain in deliverables/ and will be "
                         "archived to deliverables/history/<run-id>/ by the next run."})


def _version_text(name: str, cap) -> str:
    v = cap.version
    parts = []
    for k in ("publication", "celex", "consolidated_version_date", "publication_date", "entry_into_force_date", "policy_version",
              "context_revision", "page_last_update", "last-modified"):
        if v.get(k):
            parts.append(f"{k}={v[k]}")
    if v.get("in_source_versions"):
        parts.append("in-source=" + ",".join(v["in_source_versions"]))
    if v.get("tabs"):
        parts.append("tabs=" + ",".join(v["tabs"]))
    return "; ".join(parts) or "no version label in source"


def _limitations(caps, scope, run_blocked) -> list[str]:
    lim = []
    for n, c in caps.items():
        if not c.usable:
            lim.append(f"{n} was {c.status}: {'; '.join(c.reasons)}. Formal Article 50 conclusions are withheld.")
    for n in ("LAW", "TIME", "FAQ"):
        if caps[n].usable and caps[n].version.get("revision_after_review_date"):
            lim.append(f"{n} is a live advisory page last modified {caps[n].version.get('last-modified')}, after the "
                       f"review date {scope['as_of_date']}; the retrieved revision may differ from the 26 Aug 2026 version (D-007).")
    if caps["POLICY"].usable and caps["POLICY"].version.get("revision_after_review_date"):
        lim.append(f"POLICY context revision {caps['POLICY'].version.get('context_revision')} was authored "
                   f"{caps['POLICY'].version.get('authoring_clarification_date')}, after the review date; it states that it "
                   "records owner-supplied facts and does not revise the dated registers (D-007).")
    lim.append("CONSOLIDATED (EUR-Lex consolidated version) is used as the working binding text after reconciliation "
               "against the OJ act and AMEND; Legal confirms the authoritative version (interview 2, line 100).")
    lim.append("Company sources are read through their existing share-link permission without credentials; they are "
               "not treated as public (D-003). The Notion page is read through its page-chunk endpoint, which is "
               "undocumented and may change.")
    lim.append("Impact states are derived per system and rule (D-004): each EVIDENCE record counts only for the rules "
               "whose evidence subjects its own text names. Records naming no subject are context only. A record naming "
               "two subjects (for example label and provenance) applies its single state to both, as disclosed in the "
               "register reason. Stale register facts (AI-005) affect every row for that system.")
    lim.append("No approval outcome exists in any source; every approval is pending (D-006). No review request has been "
               "sent.")
    return lim


def _print_summary(run_id, run_status, publication, caps, impacts, actions, events, result) -> None:
    print(f"run_id:             {run_id}")
    print(f"run status:         {run_status}   (stage 07 publication_status: {publication})")
    print("sources:            " + ", ".join(f"{n}={c.status}" for n, c in caps.items()))
    counts = {}
    for i in impacts:
        counts[i["state"]] = counts.get(i["state"], 0) + 1
    print(f"register rows:      {len(impacts)} {counts}")
    print(f"actions:            {len(actions)} ({sum(1 for a in actions if not a['dated'])} undated); "
          f"calendar events: {len(events)}")
    print(f"bundle verification: {'OK' if result['ok'] else 'FAILED'} ({len(result['checks'])} checks, "
          f"{len(result['failed'])} failed)")
    for c in result["failed"][:10]:
        print(f"  - {c['id']}: {c['summary']} — {c['detail']}")
