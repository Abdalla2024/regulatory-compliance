"""Snapshot schema/chain validation, source-evidence integrity, and cross-file agreement checks."""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .outputs import REGISTER_COLUMNS
from .util import parse_iso_date, read_gzip, sha256_bytes, sha256_file

STAGES = ["scope", "source-capture", "authority-and-timing", "evidence-reconciliation", "impact-analysis",
          "actions-and-approvals", "publication-validation"]
SNAPSHOT_FILES = ["01-scope.json", "02-source-capture.json", "03-authority-and-timing.json",
                  "04-evidence-reconciliation.json", "05-impact-analysis.json", "06-actions-and-approvals.json",
                  "07-publication-validation.json"]
FINAL_FILES = {"ART-REGISTER": "impact-register.csv", "ART-BRIEF": "compliance-brief.md",
               "ART-CALENDAR": "action-calendar.ics"}


def schema_validator(schema_path: Path) -> Draft202012Validator:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def schema_errors(validator, snapshot: dict) -> list[str]:
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
            for e in sorted(validator.iter_errors(snapshot), key=lambda e: list(e.absolute_path))]


def record_ids(snapshot: dict) -> set[str]:
    ids: set[str] = set()

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("id"), str):
                ids.add(x["id"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(snapshot.get("state", {}))
    walk(snapshot.get("unresolved", []))
    walk(snapshot.get("decisions", []))
    return ids


def check(cid: str, summary: str, passed: bool, detail: str, evidence_ids=()) -> dict:
    return {"id": cid, "summary": summary, "evidence_ids": sorted(set(evidence_ids)), "passed": bool(passed),
            "detail": detail, "owner": None, "rationale": None}


# ------------------------------------------------------------------ chain

def chain_checks(root: Path, snap_dir: Path, validator, upto: int = 7) -> tuple[list[dict], list[dict]]:
    """Validate snapshots 1..upto. Returns (checks, loaded snapshots)."""
    checks, snaps = [], []
    upstream: set[str] = set()
    run_id = None
    for seq in range(1, upto + 1):
        fname = SNAPSHOT_FILES[seq - 1]
        path = snap_dir / fname
        cid = f"CHK-SNAPSHOT-{seq:02d}"
        if not path.exists():
            checks.append(check(cid, f"Snapshot {fname} present", False, "missing"))
            snaps.append(None)
            continue
        try:
            snap = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as e:
            checks.append(check(cid, f"Snapshot {fname} readable JSON", False, f"damaged: {e}"))
            snaps.append(None)
            continue
        snaps.append(snap)
        errs = schema_errors(validator, snap)
        checks.append(check(f"{cid}-SCHEMA", f"Snapshot {fname} conforms to snapshot.schema.json", not errs,
                            "; ".join(errs[:5]) or "valid", [snap.get("snapshot_id", fname)]))
        ok_stage = snap.get("stage") == STAGES[seq - 1] and snap.get("sequence") == seq
        checks.append(check(f"{cid}-STAGE", f"Snapshot {fname} has stage {STAGES[seq - 1]} / sequence {seq}", ok_stage,
                            f"stage={snap.get('stage')} sequence={snap.get('sequence')}"))
        run_id = run_id or snap.get("run_id")
        checks.append(check(f"{cid}-RUN", f"Snapshot {fname} shares run_id", snap.get("run_id") == run_id,
                            f"{snap.get('run_id')} vs {run_id}"))
        if seq > 1:
            pred, prev_path = snap.get("predecessor") or {}, snap_dir / SNAPSHOT_FILES[seq - 2]
            prev = snaps[seq - 2]
            ok = (prev is not None and prev_path.exists() and pred.get("snapshot_id") == prev.get("snapshot_id")
                  and pred.get("sha256") == sha256_file(prev_path)
                  and pred.get("path") == prev_path.resolve().relative_to(root.resolve()).as_posix())
            checks.append(check(f"{cid}-PREDECESSOR", f"Snapshot {fname} predecessor identifies and hashes "
                                f"{SNAPSHOT_FILES[seq - 2]}", ok, json.dumps(pred)))
            unresolved_refs = [i for i in snap.get("consumed_record_ids", []) if i not in upstream]
            checks.append(check(f"{cid}-CONSUMED", f"Snapshot {fname} consumed_record_ids resolve upstream",
                                not unresolved_refs and bool(snap.get("consumed_record_ids")),
                                f"unresolved: {unresolved_refs[:10]}" if unresolved_refs else
                                f"{len(snap.get('consumed_record_ids', []))} resolved"))
        present = record_ids(snap)
        missing = [i for i in snap.get("produced_record_ids", []) if i not in present]
        checks.append(check(f"{cid}-PRODUCED", f"Snapshot {fname} produced_record_ids present in the stage",
                            not missing, f"missing: {missing[:10]}" if missing else f"{len(present)} records"))
        upstream |= present
    return checks, snaps


def source_evidence_checks(root: Path, stage02: dict) -> list[dict]:
    checks = []
    for a in stage02["state"]["sources"]:
        ref, h = a.get("local_reference"), a.get("content_hash")
        if ref is None and h is None:
            checks.append(check(f"CHK-EVIDENCE-{a['id']}", f"{a['id']} records null content and hash (no content "
                                "obtained)", a["retrieval_status"] != "retrieved" or not a["used_as_evidence"],
                                a["retrieval_status"], [a["id"]]))
            continue
        p = root / ref if ref else None
        ok, detail = False, "missing local evidence"
        if p and p.exists():
            try:
                ok = sha256_bytes(read_gzip(p)) == h
                detail = "hash matches preserved bytes" if ok else "hash mismatch"
            except OSError as e:
                detail = f"damaged: {e}"
        checks.append(check(f"CHK-EVIDENCE-{a['id']}", f"{a['id']} preserved bytes match content_hash", ok, detail,
                            [a["id"]]))
        if a.get("extracts_reference"):
            ep = root / a["extracts_reference"]
            checks.append(check(f"CHK-EXTRACTS-{a['id']}", f"{a['id']} extracts file present", ep.exists(),
                                a["extracts_reference"], [a["id"]]))
    return checks


# ------------------------------------------------------------------ cross-file

def parse_ics(data: bytes) -> tuple[list[str], list[dict]]:
    errors = []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return ["calendar is not UTF-8"], []
    if "\r\n" not in text:
        errors.append("lines are not CRLF-terminated")
    unfolded = re.sub(r"\r\n[ \t]", "", text)
    lines = [ln for ln in unfolded.split("\r\n") if ln]
    if not lines or lines[0] != "BEGIN:VCALENDAR" or lines[-1] != "END:VCALENDAR":
        errors.append("missing BEGIN/END:VCALENDAR")
    if "VERSION:2.0" not in lines:
        errors.append("missing VERSION:2.0")
    if not any(ln.startswith("PRODID:") for ln in lines):
        errors.append("missing PRODID")
    events, cur = [], None
    for ln in lines:
        if ln == "BEGIN:VEVENT":
            cur = {}
        elif ln == "END:VEVENT":
            events.append(cur)
            cur = None
        elif cur is not None:
            k, _, v = ln.partition(":")
            cur[k] = v
    for ev in events:
        for req in ("UID", "DTSTAMP", "DTSTART;VALUE=DATE", "SUMMARY", "DESCRIPTION", "STATUS"):
            if req not in ev:
                errors.append(f"event {ev.get('UID')} missing {req}")
        if ev.get("STATUS") != "TENTATIVE":
            errors.append(f"event {ev.get('UID')} not TENTATIVE")
        s, e = ev.get("DTSTART;VALUE=DATE", ""), ev.get("DTEND;VALUE=DATE")
        if not re.fullmatch(r"\d{8}", s):
            errors.append(f"event {ev.get('UID')} DTSTART not a DATE")
        if e is not None and not (re.fullmatch(r"\d{8}", e) and e > s):
            errors.append(f"event {ev.get('UID')} DTEND not an exclusive later DATE")
        if not re.fullmatch(r"\d{8}T\d{6}Z", ev.get("DTSTAMP", "")):
            errors.append(f"event {ev.get('UID')} DTSTAMP not UTC date-time")
    return errors, events


def cross_file_checks(run_id: str, as_of_date: str, register: bytes, brief: bytes, ics: bytes, stage05: dict,
                      stage06: dict, expected_events: list[dict]) -> list[dict]:
    out = []
    impacts = {i["id"]: i for i in stage05["state"]["impacts"]}
    actions = {a["id"]: a for a in stage06["state"]["proposed_actions"]}
    # Register
    try:
        text = register.decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))
        header = next(csv.reader(io.StringIO(text)))
        enc_ok = True
    except (UnicodeDecodeError, StopIteration):
        rows, header, enc_ok = [], [], False
    out.append(check("CHK-REGISTER-FORMAT", "Register is UTF-8 CSV with the required header",
                     enc_ok and header[:10] == REGISTER_COLUMNS[:10], f"header: {header[:10]}", ["ART-REGISTER"]))
    reg_ids = [r["impact_id"] for r in rows]
    out.append(check("CHK-REGISTER-ROWS", "One register row per stage 05 impact, no duplicates",
                     sorted(reg_ids) == sorted(impacts) and len(set(reg_ids)) == len(reg_ids),
                     f"{len(reg_ids)} rows vs {len(impacts)} impacts", ["ART-REGISTER"]))
    mism = []
    for r in rows:
        i = impacts.get(r["impact_id"])
        if not i:
            continue
        if r["state"] != i["state"] or r["system_id"] != i["system_id"] or r["rule_ref"] != i["rule_ref"]:
            mism.append(f"{r['impact_id']} state/system/rule")
        if r["evidence_ids"].split(";") != i["evidence_ids"]:
            mism.append(f"{r['impact_id']} evidence_ids")
        if r["run_id"] != run_id:
            mism.append(f"{r['impact_id']} run_id")
        a = actions.get(r["linked_action_id"]) if r["linked_action_id"] else None
        expect_a = next((x for x in actions.values() if r["impact_id"] in x["impact_ids"]), None)
        if (a or None) != (expect_a or None):
            mism.append(f"{r['impact_id']} linked action")
        if a:
            if r["proposed_due_date"] != (a["proposed_due_date"] or "") or r["approval_status"] != a["approval_status"]:
                mism.append(f"{r['impact_id']} action date/approval")
        if r["proposed_due_date"] and not parse_iso_date(r["proposed_due_date"]):
            mism.append(f"{r['impact_id']} date format")
        if r["state"] not in ("supported-impact", "supported-no-impact", "conflicting", "unresolved"):
            mism.append(f"{r['impact_id']} invalid state")
    out.append(check("CHK-REGISTER-AGREEMENT", "Register rows agree with stage 05 impacts and stage 06 actions",
                     not mism, "; ".join(mism[:10]) or "all rows agree", ["ART-REGISTER"]))
    # Calendar
    errs, events = parse_ics(ics)
    out.append(check("CHK-CALENDAR-FORMAT", "Calendar is a valid RFC 5545 VCALENDAR draft", not errs,
                     "; ".join(errs[:8]) or "valid", ["ART-CALENDAR"]))
    exp = {a["uid"]: a for a in expected_events}
    got = {e.get("UID"): e for e in events}
    cal_mism = []
    if set(exp) != set(got):
        cal_mism.append(f"UIDs {sorted(got)} vs expected {sorted(exp)}")
    for uid, a in exp.items():
        e = got.get(uid)
        if not e:
            continue
        if e.get("DTSTART;VALUE=DATE") != a["proposed_due_date"].replace("-", ""):
            cal_mism.append(f"{uid} date")
        desc = e.get("DESCRIPTION", "").replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";")
        for needle in (a["id"], a["system_id"], "Responsible role", f"Approval status: {a['approval_status']}", "Basis:"):
            if needle not in desc:
                cal_mism.append(f"{uid} description lacks '{needle}'")
    for a in actions.values():
        if not a["dated"] and a["uid"] in got:
            cal_mism.append(f"undated {a['id']} present in calendar")
    out.append(check("CHK-CALENDAR-AGREEMENT", "Calendar events agree with stage 06 dated actions", not cal_mism,
                     "; ".join(cal_mism[:8]) or f"{len(events)} events agree", ["ART-CALENDAR"]))
    # Brief
    try:
        btext = brief.decode("utf-8")
    except UnicodeDecodeError:
        btext = ""
    need = [run_id, as_of_date] + list(impacts) + list(actions) + \
           [r["request_id"] for r in stage06["state"]["review_requests"]]
    missing = [n for n in need if n and n not in btext]
    for heading in ("Recipients", "Run status", "Source quality and limitations", "Legal-review boundary",
                    "Supported observations",
                    "Conflicts and unresolved scope", "Proposed actions and dates", "Decisions requested"):
        if heading not in btext:
            missing.append(f"section '{heading}'")
    out.append(check("CHK-BRIEF-AGREEMENT", "Brief cites run, impacts, actions and review requests and has required "
                     "sections", not missing, f"missing: {missing[:10]}" if missing else "complete", ["ART-BRIEF"]))
    return out


# ------------------------------------------------------------------ decision conformance

REFS = Path(__file__).resolve().parents[2] / "references"


def decision_checks(root: Path, deliverables: Path, snaps: list) -> list[dict]:
    """Check that the generated artifacts actually follow decisions D-004 to D-008."""
    out = []
    if any(s is None for s in snaps):
        return [check("CHK-DECISIONS", "Decision conformance checks", False, "snapshot chain incomplete")]
    s1, s2, s3, s4, s5, s6, s7 = snaps
    rules = {r["id"]: r for r in json.loads((REFS / "rules.json").read_text(encoding="utf-8"))["rules"]}
    blocked = s7["status"] == "blocked"

    # D-004: rows cite only records attributed to that rule; states follow the attributed records.
    recs = {r["id"]: r for r in s4["state"]["incident_evidence"]}
    bad = []
    for i in s5["state"]["impacts"]:
        cited = {e for e in i["evidence_ids"] if e in recs}
        attributed = set(i.get("attributed_record_ids", []))
        if cited - attributed:
            bad.append(f"{i['id']} cites unattributed {sorted(cited - attributed)}")
        for rid in attributed:
            r = recs[rid]
            if r["system_id"] != i["system_id"]:
                bad.append(f"{i['id']} attributed record {rid} belongs to {r['system_id']}")
            stale_sys = "stale" in (i["rationale"] or "") and "register entry" in (i["rationale"] or "")
            if not stale_sys and not set(r["evidence_subjects"]) & set(rules[i["rule_id"]]["evidence_subjects"]):
                bad.append(f"{i['id']} record {rid} names none of the rule's subjects")
        if i["applicability"] == "applies-on-recorded-facts":
            states = {recs[r]["evidence_state"] for r in attributed}
            cf = rules[i["rule_id"]].get("control_field")
            control_unknown = bool(cf) and i["control_status"] in (f"{cf}=None", f"{cf}=unknown")
            if "conflicting" in states:
                expect = "conflicting"
            elif not attributed or states & {"missing", "stale", "partial"} or control_unknown:
                expect = "unresolved"
            else:
                expect = "supported-impact"
            if i["state"] != expect:
                bad.append(f"{i['id']} state {i['state']} but attributed records imply {expect}")
    out.append(check("CHK-D004-RULE-LEVEL", "D-004: each row's state and cited records come only from records "
                     "attributed to that rule", not bad, "; ".join(bad[:8]) or
                     f"{len(s5['state']['impacts'])} rows conform", ["D-004"]))

    # D-005: CALENDAR facts carried unchanged; no invented dates; every CALENDAR action kept; ICS = dated proposals.
    cal = {}
    ext_file = deliverables / "sources" / "CALENDAR.extracts.json"
    cal_ok = any(x["source_name"] == "CALENDAR" and x["retrieval_status"] == "retrieved"
                 for x in s2["state"]["source_summaries"])
    if cal_ok and ext_file.exists():  # an unsuitable CALENDAR read is retained but deliberately not used
        cal = {e["fields"]["action_id"]: e["fields"] for e in json.loads(ext_file.read_text())["extracts"]}
    acts = {a["id"]: a for a in s6["state"]["proposed_actions"]}
    bad = [f"{aid} missing from stage 06" for aid in cal if aid not in acts]
    for a in acts.values():
        if a["origin"].startswith("calendar"):
            c = cal.get(a["id"])
            if not c:
                bad.append(f"{a['id']} not in CALENDAR capture")
            elif (a["proposed_due_date"] or "") != c["due_date"] or (a["owner"] or "") != c["owner"]:
                bad.append(f"{a['id']} date/owner differ from CALENDAR")
        elif a["proposed_due_date"]:
            bad.append(f"{a['id']} new proposal carries an invented date")
    uids = set(s7["state"]["calendar_event_uids"])
    want = set() if blocked else {a["uid"] for a in acts.values() if a["dated"]}
    if uids != want:
        bad.append(f"calendar UIDs {sorted(uids)} vs expected {sorted(want)}")
    out.append(check("CHK-D005-ACTIONS-DATES", "D-005: CALENDAR actions kept with unchanged owners/dates; no invented "
                     "dates; calendar holds exactly the dated proposals", not bad, "; ".join(bad[:8]) or
                     f"{len(acts)} actions conform", ["D-005"]))

    # D-006: approvals pending unless a validated response was applied; requests not sent; no not-required.
    bad = []
    for a in s6["state"]["approval_requirements"]:
        if a["status"] != "pending" and not a.get("response"):
            bad.append(f"{a['id']} is {a['status']} without a validated response")
        if a["status"] == "not-required":
            bad.append(f"{a['id']} uses not-required")
    bad += [f"{r['request_id']} delivery status '{r['delivery_status']}'" for r in s6["state"]["review_requests"]
            if "not sent" not in r["delivery_status"]]
    reg = list(csv.DictReader(io.StringIO((deliverables / FINAL_FILES["ART-REGISTER"]).read_text(encoding="utf-8"))))
    applied = {a["subject_action_id"] for a in s6["state"]["approval_requirements"] if a.get("response")
               and a.get("subject_action_id")}
    bad += [f"{r['impact_id']} approval_status {r['approval_status']}" for r in reg
            if r["approval_status"] != "pending" and r["linked_action_id"] not in applied]
    out.append(check("CHK-D006-APPROVALS", "D-006: approvals pending unless a validated response applies; review "
                     "requests prepared, not sent", not bad, "; ".join(bad[:8]) or "conform", ["D-006"]))

    # D-007: review date fixed and separate from retrieval times; legal versions suitable for the review date.
    scope = json.loads((REFS / "scope.json").read_text(encoding="utf-8"))
    bad = []
    if s1["state"]["as_of"] != scope["as_of"] or s1["state"]["as_of_date"] != scope["as_of_date"]:
        bad.append("stage 01 as_of differs from the assigned review date")
    as_of = parse_iso_date(scope["as_of_date"])
    for a in s2["state"]["sources"]:
        if a["retrieved_at"][:10] == scope["as_of_date"]:
            bad.append(f"{a['id']} retrieval time equals the review date (not separated)")
        vm = a.get("version_metadata") or {}
        if a["used_as_evidence"] and a["retrieval_status"] == "retrieved":
            if vm.get("consolidated_version_date") and parse_iso_date(vm["consolidated_version_date"]) > as_of:
                bad.append(f"{a['id']} consolidated version after review date accepted")
            if vm.get("entry_into_force_date") and parse_iso_date(vm["entry_into_force_date"]) > as_of:
                bad.append(f"{a['id']} amendment not in force by review date accepted")
    brief = (deliverables / FINAL_FILES["ART-BRIEF"]).read_text(encoding="utf-8")
    for a in s2["state"]["sources"]:
        vm = a.get("version_metadata") or {}
        if a["used_as_evidence"] and vm.get("revision_after_review_date") and f"{a['source_name']} " not in brief:
            bad.append(f"{a['source_name']} later revision not disclosed in brief")
    if scope["as_of_date"] not in brief:
        bad.append("brief lacks the as-of date")
    out.append(check("CHK-D007-DATES", "D-007: fixed review date, separate retrieval times, legal versions suitable "
                     "for the review date, later revisions disclosed", not bad, "; ".join(bad[:8]) or "conform", ["D-007"]))

    # D-008: every obtained response preserved as gzip bytes (hash of raw bytes) with extracts; failures null.
    bad = []
    for a in s2["state"]["sources"]:
        if a["content_hash"]:
            ref = a["local_reference"] or ""
            if not (ref.startswith("deliverables/sources/") and ref.endswith(".gz")):
                bad.append(f"{a['id']} local reference {ref!r}")
            if a["used_as_evidence"] and not a.get("extracts_reference"):
                bad.append(f"{a['id']} used as evidence without extracts")
        elif a["local_reference"] is not None:
            bad.append(f"{a['id']} has a local reference but no hash")
    for f in sorted((deliverables / "sources").glob("*.extracts.json")):
        ex = json.loads(f.read_text(encoding="utf-8"))["extracts"]
        if any(not e.get("locator") for e in ex):
            bad.append(f"{f.name} has extracts without locators")
    out.append(check("CHK-D008-PRESERVATION", "D-008: gzip-preserved bytes hashed, extracts with locators, null "
                     "content/hash when nothing obtained", not bad, "; ".join(bad[:8]) or "conform", ["D-008"]))
    out += reproduction_checks(root, deliverables, s2)
    return out


def reproduction_checks(root: Path, deliverables: Path, s2: dict) -> list[dict]:
    """D-008: the preserved captures alone reproduce the extracts used downstream; POLICY is redacted."""
    from .sources import NOTION_REDACTED_TABLES, notion_ordered_blocks
    out = []
    routes = {r["name"]: r for r in json.loads((REFS / "source-routes.json").read_text(encoding="utf-8"))["sources"]}
    used = [a for a in s2["state"]["sources"] if a["used_as_evidence"] and a["content_hash"]]
    # POLICY (Notion): redaction applied, no member data, extracts re-derivable from the saved chunks.
    pol = [a for a in used if a["source_name"] == "POLICY"]
    if pol:
        bad, blocks = [], {}
        for a in pol:
            raw = read_gzip(root / a["local_reference"])
            data = json.loads(raw)
            present = [t for t in NOTION_REDACTED_TABLES if t in data.get("recordMap", {})]
            if present:
                bad.append(f"{a['id']} still contains {present}")
            for needle in ('"profile_photo"', "googleusercontent.com"):
                if needle.encode() in raw:
                    bad.append(f"{a['id']} contains {needle}")
            if not (a.get("redaction") or {}).get("original_response_sha256"):
                bad.append(f"{a['id']} lacks redaction metadata")
            blocks.update(data["recordMap"].get("block", {}))
        out.append(check("CHK-D008-POLICY-REDACTED", "D-008: POLICY capture has no workspace member table or profile "
                         "details, and records its redaction", not bad, "; ".join(bad) or
                         f"{len(pol)} chunk(s) redacted", [a["id"] for a in pol] + ["D-008"]))
        exp = routes["POLICY"]["expect"]
        ordered = notion_ordered_blocks(blocks, exp["page_id"])
        ext = json.loads((deliverables / "sources" / "POLICY.extracts.json").read_text(encoding="utf-8"))["extracts"]
        derived = [(b["id"], b["text"]) for b in ordered]
        saved = [(e["block_id"], e["text"]) for e in ext]
        full = "\n".join(t for _, t in derived)
        bad = []
        if derived != saved:
            bad.append(f"re-derived {len(derived)} blocks differ from {len(saved)} saved extracts")
        for pat in [exp["policy_version_pattern"], exp["context_revision_pattern"]] + exp.get("date_patterns", []):
            if not re.search(pat, full):
                bad.append(f"missing '{pat}'")
        headings = {b["text"] for b in ordered if b["type"] in ("header", "sub_header", "sub_sub_header")}
        bad += [f"missing section '{h}'" for h in exp.get("content_sections", []) if h not in headings]
        out.append(check("CHK-D008-POLICY-REPRODUCIBLE", "D-008: saved POLICY bytes reproduce every extract (block "
                         "IDs, order, text), identity, version, revision dates, rules, approval boundary and evidence "
                         "limits", not bad, "; ".join(bad) or f"{len(derived)} blocks reproduced", ["D-008"]))
    # Sheets: saved CSV bytes reproduce the row extracts.
    for name in ("SYSTEMS", "EVIDENCE", "CALENDAR"):
        att = [a for a in used if a["source_name"] == name]
        if not att:
            continue
        rows = list(csv.DictReader(io.StringIO(read_gzip(root / att[0]["local_reference"]).decode("utf-8-sig"))))
        idcol = routes[name]["expect"]["id_column"]
        derived = {r[idcol].strip(): {k.strip(): (v or "").strip() for k, v in r.items() if k} for r in rows
                   if any((v or "").strip() for v in r.values())}
        ext = json.loads((deliverables / "sources" / f"{name}.extracts.json").read_text(encoding="utf-8"))["extracts"]
        saved = {e["fields"][idcol]: e["fields"] for e in ext}
        ok = derived == saved
        out.append(check(f"CHK-D008-{name}-REPRODUCIBLE", f"D-008: saved {name} bytes reproduce its row extracts", ok,
                         f"{len(derived)} rows reproduced" if ok else "saved bytes and extracts differ", ["D-008"]))
    return out


# ------------------------------------------------------------------ history

def history_checks(deliverables: Path) -> list[dict]:
    """Archived runs: any preserved POLICY chunk that no longer matches its run's stage 02 hash must be explained by a
    documented post-run redaction, and no archived chunk may still hold the Notion member table."""
    from .sources import NOTION_REDACTED_TABLES
    out = []
    hist = deliverables / "history"
    if not hist.exists():
        return out
    for run_dir in sorted(p for p in hist.iterdir() if p.is_dir()):
        bad = []
        try:
            manifest = json.loads((run_dir / "history-manifest.json").read_text(encoding="utf-8"))
            s02 = json.loads((run_dir / "snapshots" / "02-source-capture.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            out.append(check(f"CHK-HISTORY-{run_dir.name}", f"History {run_dir.name} readable", False, str(e)))
            continue
        recorded = {a["local_reference"].split("/")[-1]: a.get("content_hash") for a in s02["state"]["sources"]
                    if a.get("local_reference")}
        redactions = {Path(e["file"]).name: e for e in manifest.get("post_run_redactions", [])}
        for chunk in sorted((run_dir / "sources").glob("POLICY-chunk-*.json.gz")):
            raw = read_gzip(chunk)
            if any(f'"{t}"'.encode() in raw for t in NOTION_REDACTED_TABLES):
                bad.append(f"{chunk.name} still contains the member table")
            current = sha256_bytes(raw)
            if current != recorded.get(chunk.name):
                e = redactions.get(chunk.name)
                if not e or e["redacted_content_sha256"] != current or e["original_content_sha256"] != recorded.get(chunk.name):
                    bad.append(f"{chunk.name} differs from its stage 02 hash without a matching documented redaction")
        # Stage 02 snapshot: a hash that no longer matches stage 03's predecessor must be a documented redaction.
        s02_path = run_dir / "snapshots" / "02-source-capture.json"
        try:
            pred = json.loads((run_dir / "snapshots" / "03-authority-and-timing.json").read_text())["predecessor"]["sha256"]
        except (OSError, ValueError, KeyError, TypeError):
            pred = None
        cur = sha256_file(s02_path)
        if pred and cur != pred:
            e = redactions.get(s02_path.name)
            if not e or e.get("redacted_file_sha256") != cur or e.get("original_file_sha256") != pred:
                bad.append("02-source-capture.json differs from stage 03 predecessor without a documented redaction")
        if "googleusercontent.com/export" in s02_path.read_text(encoding="utf-8"):
            bad.append("02-source-capture.json still records a signed redirect URL")
        out.append(check(f"CHK-HISTORY-{run_dir.name}", f"History {run_dir.name}: POLICY captures and signed URLs "
                         "redacted, and every hash difference documented as a post-run redaction", not bad,
                         "; ".join(bad) or f"{len(redactions)} documented redaction(s)"))
    return out


# ------------------------------------------------------------------ whole bundle

def verify_bundle(root: Path, deliverables: Path, schema_path: Path) -> dict:
    """Read-only inspection of the current seven snapshots, evidence and final drafts."""
    validator = schema_validator(schema_path)
    snap_dir = deliverables / "snapshots"
    checks, snaps = chain_checks(root, snap_dir, validator)
    if snaps[1]:
        checks += source_evidence_checks(root, snaps[1])
    s07 = snaps[6]
    if s07:
        for art in s07["state"].get("artifacts", []):
            p = root / art["path"]
            ok = p.exists() and sha256_file(p) == art["sha256"]
            checks.append(check(f"CHK-ARTIFACT-{art['id']}", f"{art['path']} matches stage 07 hash", ok,
                                "match" if ok else ("missing" if not p.exists() else "hash mismatch (stale or damaged)")))
        if snaps[4] and snaps[5] and all((deliverables / f).exists() for f in FINAL_FILES.values()):
            expected = [a for a in snaps[5]["state"]["proposed_actions"] if a["uid"] in
                        s07["state"].get("calendar_event_uids", [])]
            checks += cross_file_checks(s07["run_id"], snaps[0]["state"]["as_of_date"] if snaps[0] else "",
                                        (deliverables / FINAL_FILES["ART-REGISTER"]).read_bytes(),
                                        (deliverables / FINAL_FILES["ART-BRIEF"]).read_bytes(),
                                        (deliverables / FINAL_FILES["ART-CALENDAR"]).read_bytes(),
                                        snaps[4], snaps[5], expected)
        bound = {b["request_id"] for b in s07["state"].get("review_bindings", [])}
        reqs = {r["request_id"] for r in (snaps[5] or {}).get("state", {}).get("review_requests", [])}
        checks.append(check("CHK-BINDINGS", "Every review request is bound to final draft hashes", reqs == bound,
                            f"requests {len(reqs)}, bound {len(bound)}"))
        for b in s07["state"].get("review_bindings", []):
            bad = [x["path"] for x in b["artifacts"] if not (root / x["path"]).exists()
                   or sha256_file(root / x["path"]) != x["sha256"]]
            checks.append(check(f"CHK-BIND-{b['request_id']}", f"Binding for {b['request_id']} matches the files",
                                not bad, f"mismatch: {bad}" if bad else "match"))
    else:
        for f in FINAL_FILES.values():
            checks.append(check(f"CHK-FINAL-{f}", f"{f} verifiable", False, "no stage 07 snapshot to verify against"))
    if all(snaps) and all((deliverables / f).exists() for f in FINAL_FILES.values()):
        checks += decision_checks(root, deliverables, snaps)
    checks += history_checks(deliverables)
    failed = [c for c in checks if not c["passed"]]
    return {"ok": not failed, "run_id": next((s["run_id"] for s in snaps if s), None),
            "run_status": s07["status"] if s07 else None, "checks": checks, "failed": failed}
