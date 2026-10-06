"""Stages 03-06: authority and timing, evidence reconciliation, impact analysis, actions and approvals.

Nothing here states compliance or non-compliance. Impact states are draft interpretations for
Legal review (decision D-004); approvals are never inferred (decision D-006)."""

from __future__ import annotations

import datetime as dt
import re

from .sources import SourceCapture
from .util import parse_iso_date

BINDING = ("OJ", "AMEND", "CONSOLIDATED")
ADVISORY = ("LAW", "TIME", "FAQ")
COMPANY = ("POLICY", "SYSTEMS", "EVIDENCE", "CALENDAR")
UID_DOMAIN = "regulatory-change-impact-brief.quillhaven"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"▼\w+", " ", s)).strip()


def _rec(id_, summary, evidence_ids, owner=None, rationale=None, **extra):
    r = {"id": id_, "summary": summary, "evidence_ids": sorted(set(evidence_ids)), "owner": owner,
         "rationale": rationale}
    r.update(extra)
    return r


def used_attempt_id(cap: SourceCapture) -> str | None:
    for a in cap.attempts:
        if a["used_as_evidence"]:
            return a["id"]
    return cap.attempts[-1]["id"] if cap.attempts else None


# ============================================================ stage 03

def authority_and_timing(caps: dict[str, SourceCapture], rules: dict, as_of_date: dt.date) -> dict:
    binding_rules, timing_rules, guidance, blockers = [], [], [], []
    failed_legal = [n for n in BINDING + ADVISORY if not caps[n].usable]
    for n in failed_legal:
        c = caps[n]
        blockers.append(_rec(
            f"BLK-{n}", f"Required {'binding' if n in BINDING else 'official advisory'} legal route {n} is "
            f"{c.status}; all formal Article 50 conclusions for this run are withheld (D-002).",
            [a["id"] for a in c.attempts], owner="Operations (re-run when the source is restored); Legal for interpretation",
            rationale="; ".join(c.reasons) or c.status, source=n, retrieval_status=c.status,
            resolution_need=f"Restore a suitable live read of {n} and re-run the documented command."))

    cons, oj, amend = caps["CONSOLIDATED"], caps["OJ"], caps["AMEND"]
    cons_p = cons.parsed.get("article50", {}) if cons.usable else {}
    oj_p = oj.parsed.get("article50", {}) if oj.usable else {}
    replaced = set(amend.parsed.get("art50_paragraphs_replaced", [])) if amend.usable else set()

    # Reconcile the consolidated text against the OJ act and the amendment (interview 2, line 100).
    if cons_p and oj_p:
        for n in range(1, 8):
            same = _norm(cons_p.get(n, "")) == _norm(oj_p.get(n, ""))
            if same:
                continue
            if n in replaced:
                timing_rules.append(_rec(
                    f"REC-ART50-{n}-AMENDED",
                    f"Article 50({n}) differs between OJ and CONSOLIDATED; the difference is explained by AMEND "
                    f"(Regulation (EU) 2026/1744), which replaces paragraph {n}. CONSOLIDATED text is used.",
                    [f"EXT-OJ-ART50-{n}", f"EXT-CONSOLIDATED-ART50-{n}"] +
                    [e for e in amend.extracts if e.startswith("EXT-AMEND-ITEM")],
                    owner="Legal", rationale="Reconciled against the Official Journal acts and applicable amendment."))
            else:
                blockers.append(_rec(
                    f"BLK-ART50-{n}-UNRECONCILED",
                    f"Article 50({n}) differs between OJ and CONSOLIDATED and no AMEND item explains the difference; "
                    "the binding text for the review date cannot be confirmed.",
                    [f"EXT-OJ-ART50-{n}", f"EXT-CONSOLIDATED-ART50-{n}"], owner="Legal",
                    rationale="Unreconciled binding-text discrepancy (D-002 unsuitable).",
                    resolution_need="Legal confirms the binding Article 50 text effective on 26 August 2026."))

    for rule in rules["rules"]:
        if rule["basis"] != "binding-law":
            continue
        ptext = cons_p.get(rule["paragraph"], "")
        located = bool(ptext) and _norm(rule["text_cue"]) in _norm(ptext)
        binding_rules.append(_rec(
            f"RULE-{rule['id']}", f"{rule['rule_ref']}: {rule['summary']}",
            [f"EXT-CONSOLIDATED-ART50-{rule['paragraph']}", f"EXT-CONSOLIDATED-ART50-5"] if located else [],
            owner="Legal (final interpretation)", rationale=(
                "Rule text located in the binding consolidated text (version 2026-07-27, on or before the review date)."
                if located else "Rule text not located in a usable binding source; rows depending on it are unresolved."),
            rule_id=rule["id"], rule_ref=rule["rule_ref"], actor=rule["actor"], located=located,
            paragraph_text=ptext or None, manner_and_timing=cons_p.get(5)))
    for n in (6, 7):
        if cons_p.get(n):
            guidance.append(_rec(f"CTX-ART50-{n}", f"Article 50({n}) recorded as context; it creates no system-level "
                                 f"duty assessed per system in this review.", [f"EXT-CONSOLIDATED-ART50-{n}"],
                                 owner="Legal", rationale="Context only (D-004)."))

    if cons.usable and cons.parsed.get("general_application_date"):
        gad = cons.parsed["general_application_date"]
        timing_rules.append(_rec(
            "TIME-ART113-GENERAL", f"Article 113: the Regulation applies from {gad} (general date; Article 50 is not "
            f"listed among the exceptions). Review date {as_of_date.isoformat()} is "
            f"{'on or after' if parse_iso_date(gad) <= as_of_date else 'before'} that date.",
            ["EXT-CONSOLIDATED-ART113"] + (["EXT-OJ-ART113"] if oj.usable else []), owner="Legal",
            rationale="Binding application date compared with the fixed review date; Legal confirms.",
            effective_date=gad, review_date=as_of_date.isoformat()))
    if cons.usable and cons.parsed.get("art111_4"):
        a = cons.parsed["art111_4"]
        timing_rules.append(_rec(
            "TIME-ART111-4", f"Article 111(4): providers of generative AI systems placed on the market before "
            f"{a['placed_before']} must comply with Article 50(2) by {a['comply_by']}. Applies to providers only.",
            ["EXT-CONSOLIDATED-ART111-4"], owner="Legal", rationale="Transitional provision introduced by AMEND.",
            effective_date=a["comply_by"]))
    if amend.usable and amend.parsed.get("entry_into_force_date"):
        timing_rules.append(_rec(
            "TIME-AMEND-EIF", f"Regulation (EU) 2026/1744 published {amend.parsed['publication_date']}; entry into force "
            f"computed as {amend.parsed['entry_into_force_date']} (third day after publication), on or before the "
            "review date.", ["EXT-AMEND-PUBLICATION", "EXT-AMEND-EIF"], owner="Legal",
            rationale="Computed from the amendment's own publication reference and entry-into-force article.",
            effective_date=amend.parsed["entry_into_force_date"]))

    if caps["TIME"].usable:
        for m in caps["TIME"].parsed.get("milestones", []):
            if "Article 50" in m["text"] or "transparency" in m["text"].lower():
                guidance.append(_rec(f"GUIDE-TIME-{m['date']}", f"TIME milestone {m['date']}: {m['text'][:300]}",
                                     [m["evidence_id"]], owner="European Commission (advisory)",
                                     rationale="Official timeline guidance; not binding."))
    if caps["FAQ"].usable:
        guidance.append(_rec("GUIDE-FAQ", "Commission FAQ on Article 50 transparency obligations (advisory; page "
                             f"last update {caps['FAQ'].version.get('page_last_update')}).",
                             [e for e in caps["FAQ"].extracts], owner="European Commission (advisory)",
                             rationale="Interpretive guidance; not binding."))
    if caps["LAW"].usable:
        guidance.append(_rec("GUIDE-LAW", "AI Act Service Desk Article 50 page; its summaries state they are not "
                             "legally binding. The binding text is taken from CONSOLIDATED.",
                             list(caps["LAW"].extracts), owner="European Commission (advisory)",
                             rationale="Official route; advisory presentation."))

    return {"binding_rules": binding_rules, "timing_rules": timing_rules, "guidance_context": guidance,
            "authority_blockers": blockers}


# ============================================================ stage 04

def _cue_hits(blocks: list[dict], spec: dict) -> list[str] | None:
    if "patterns_all" in spec:
        hits = []
        for p in spec["patterns_all"]:
            found = [b for b in blocks if p in b["text"]]
            if not found:
                return None
            hits += [f"EXT-POLICY-BLK-{b['id'][:8]}" for b in found]
        return hits
    hits = [f"EXT-POLICY-BLK-{b['id'][:8]}" for b in blocks for p in spec["patterns"] if p in b["text"]]
    return hits or None


def evidence_reconciliation(caps: dict[str, SourceCapture], rules: dict, scope: dict, as_of_date: dt.date) -> dict:
    systems_cap, ev_cap, pol_cap = caps["SYSTEMS"], caps["EVIDENCE"], caps["POLICY"]
    in_scope = scope["systems_in_scope"]
    sys_rows = {r["system_id"]: r for r in systems_cap.parsed.get("rows", [])} if systems_cap.usable else {}
    ev_rows = ev_cap.parsed.get("rows", []) if ev_cap.usable else []
    sections = pol_cap.parsed.get("sections", {}) if pol_cap.usable else {}

    system_facts, policy_controls, incident_evidence, conflicts, gaps = [], [], [], [], []

    # Policy controls (rule texts located live in POLICY).
    pol_blocks = pol_cap.parsed.get("blocks", []) if pol_cap.usable else []
    policy_meta = {}
    for rule in rules["rules"]:
        if rule["basis"] != "internal-policy":
            continue
        hits = [b for b in pol_blocks if rule["text_cue"] in b["text"]]
        located = bool(hits)
        policy_meta[rule["id"]] = located
        policy_controls.append(_rec(
            f"POLCTL-{rule['id']}", f"{rule['rule_ref']}: {rule['summary']}",
            [f"EXT-POLICY-BLK-{b['id'][:8]}" for b in hits], owner="Legal (policy interpretation); Operations (activation)",
            rationale=("Located in live POLICY " + str(pol_cap.version.get("policy_version"))) if located else
            "Rule text not located in a usable POLICY read; dependent rows are unresolved.",
            rule_id=rule["id"], located=located, policy_version=pol_cap.version.get("policy_version")))
    for bid_text in ("missing, stale, conflicting, and not-applicable are different evidence states",
                     "An exception requires a named owner, rationale, expiry date, and Legal approval"):
        hits = [b for b in pol_blocks if bid_text in b["text"]]
        if hits:
            policy_controls.append(_rec(
                f"POLCTL-{'EVIDENCE-STATES' if 'evidence states' in bid_text else 'EXCEPTIONS'}", hits[0]["text"],
                [f"EXT-POLICY-BLK-{hits[0]['id'][:8]}"], owner="Legal",
                rationale="Policy constraint applied to state handling and exception requests.", located=True))

    # Licensed supplier products (operating scope).
    licensed, licensed_ev = set(), []
    spec = rules["fact_cues"]["licensed_supplier_product"]
    for b in sections.get("Operating scope", []):
        for p in spec["patterns"]:
            if p in b["text"]:
                licensed |= set(re.findall(r"AI-\d{3}", b["text"][: b["text"].find(p)]))
                licensed_ev.append(f"EXT-POLICY-BLK-{b['id'][:8]}")

    issues_by_id: dict[str, list] = {}
    for cap in (systems_cap, ev_cap, caps["CALENDAR"]):
        for iss in cap.issues:
            issues_by_id.setdefault(iss["record_id"], []).append({**iss, "source": cap.name})

    ev_by_sys: dict[str, list] = {}
    for r in ev_rows:
        ev_by_sys.setdefault(r["system_id"], []).append(r)
        eid = f"EXT-EVIDENCE-{r['record_id']}"
        late = (d := parse_iso_date(r.get("reported_at", ""))) is not None and d > as_of_date
        incident_evidence.append(_rec(
            r["record_id"], f"{r['record_id']} ({r['record_type']}, {r['status']}) for {r['system_id']}: "
            f"evidence_state={r['evidence_state']}; {r['notes']}", [eid], owner=r["owner"],
            rationale="Recorded in EVIDENCE; carried unchanged.", system_id=r["system_id"],
            record_type=r["record_type"], record_status=r["status"], evidence_state=r["evidence_state"],
            evidence_ref=r["evidence_ref"], reported_at=r["reported_at"], notes=r["notes"],
            reported_after_review_date=late))
        if late:
            gaps.append(_rec(f"GAP-{r['record_id']}-LATE", f"{r['record_id']} reported {r['reported_at']}, after the "
                             "review date; retained as later evidence with that uncertainty disclosed.", [eid],
                             owner=r["owner"], rationale="D-007", resolution_need="None; disclosed."))
        if r["evidence_state"] == "conflicting":
            rule_basis = "D-001"
            conflicts.append(_rec(
                f"CONF-{r['record_id']}", f"Conflicting evidence for {r['system_id']}: {r['notes']} "
                f"(evidence reference {r['evidence_ref']}). Both facts are preserved; the automation does not decide "
                "which is true.", [eid, f"EXT-SYSTEMS-{r['system_id']}"], owner=r["owner"], rationale=rule_basis,
                system_id=r["system_id"], record_id=r["record_id"],
                resolution_need=f"System owner ({r['owner']}) verifies the contested fact using {r['evidence_ref']} "
                                "and updates EVIDENCE/SYSTEMS.",
                interview_note=("Interview 2 (line 148) described this item as unresolved pending owner "
                                "verification; it remains unresolved in that sense, with state 'conflicting' (D-001)."
                                if r["record_id"] == "REC-008" else None)))
        elif r["evidence_state"] in ("missing", "stale", "partial"):
            gaps.append(_rec(
                f"GAP-{r['record_id']}", f"{r['record_id']} for {r['system_id']} is {r['evidence_state']}: {r['notes']}",
                [eid], owner=r["owner"], rationale="Missing, stale or partial evidence stays unresolved; it is never "
                "converted to compliance or non-compliance (POLICY).", system_id=r["system_id"],
                record_id=r["record_id"], evidence_state=r["evidence_state"],
                resolution_need=f"{r['owner']} supplies current, complete evidence for {r['evidence_ref']}."
                + (" Legal approval and expiry date are also required for the exception request."
                   if r["record_type"] == "exception_request" else "")))

    attribution = attribute_records(ev_rows, rules["evidence_subjects"])
    for rec in incident_evidence:
        subj = attribution.get(rec["id"], [])
        rec["evidence_subjects"] = subj
        rec["attribution"] = ("attributed to rules naming: " + ", ".join(subj)) if subj else \
            "unattributed: the record names no rule subject, so it affects no register row (context only)"

    for sid in in_scope:
        row = sys_rows.get(sid)
        if row is None:
            gaps.append(_rec(f"GAP-{sid}-ABSENT", f"In-scope system {sid} has no usable SYSTEMS register row.",
                             [used_attempt_id(systems_cap) or "ATT-SYSTEMS-1"], owner="Operations",
                             rationale="Scope system without register facts.", system_id=sid,
                             resolution_need="Operations restores the SYSTEMS register entry."))
            continue
        sec = sections.get(sid, [])
        cues = {}
        for cue_id, spec in rules["fact_cues"].items():
            if spec["scope"] == "system-section":
                cues[cue_id] = _cue_hits(sec, spec)
        invalid_fields = {i["field"] for i in issues_by_id.get(sid, []) if i["source"] == "SYSTEMS"}
        fields = {k: (None if k in invalid_fields else v) for k, v in row.items() if k != "_row"}
        system_facts.append(_rec(
            f"FACT-{sid}", f"{sid} {row['system_name']}: {row['use_case']}; owner {row['owner']}; provider_role="
            f"{row['provider_role']}, deployer_role={row['deployer_role']}, exposed_group={row['exposed_group']}, "
            f"output_type={row['output_type']}, current_notice={row['current_notice']}, evidence_status="
            f"{row['evidence_status']} (updated {row['evidence_updated_at']}).",
            [f"EXT-SYSTEMS-{sid}"] + [f"EXT-POLICY-BLK-{b['id'][:8]}" for b in sec] + (licensed_ev if sid in licensed else []),
            owner=row["owner"], rationale="SYSTEMS register row plus POLICY operating facts for the system.",
            system_id=sid, fields=fields, licensed_supplier_product=sid in licensed,
            policy_section_found=bool(sec), policy_cues={k: v for k, v in cues.items()},
            evidence_record_ids=[r["record_id"] for r in ev_by_sys.get(sid, [])],
            data_quality_issues=issues_by_id.get(sid, [])))
        for f, v in row.items():
            if v == "unknown":
                gaps.append(_rec(f"GAP-{sid}-{f.upper()}", f"{sid} SYSTEMS field {f} is 'unknown'.",
                                 [f"EXT-SYSTEMS-{sid}"], owner=row["owner"], rationale="Expected fact missing.",
                                 system_id=sid, resolution_need=f"{row['owner']} supplies the {f} fact."))
        for iss in issues_by_id.get(sid, []):
            gaps.append(_rec(f"GAP-{sid}-{iss['field'].upper()}-INVALID", f"{iss['source']} row {iss['row']} field "
                             f"{iss['field']}='{iss['value']}': {iss['problem']}. Not guessed.",
                             [f"EXT-{iss['source']}-{sid}"], owner=row["owner"], rationale="ASSIGN changed-inputs rule.",
                             system_id=sid, resolution_need="Source owner corrects the value."))
        if row["evidence_status"] == "stale":
            gaps.append(_rec(f"GAP-{sid}-REGISTER-STALE", f"{sid} register facts are stale (evidence_updated_at "
                             f"{row['evidence_updated_at']}); all rows for this system stay unresolved.",
                             [f"EXT-SYSTEMS-{sid}"], owner=row["owner"], rationale="Stale facts block conclusions "
                             "(interview 1 lines 150, 166).", system_id=sid,
                             resolution_need=f"{row['owner']} refreshes the register entry and supporting evidence."))
    for sid, row in sys_rows.items():
        if sid not in in_scope:
            gaps.append(_rec(f"GAP-{sid}-OUT-OF-SCOPE", f"SYSTEMS lists {sid} which is not in the declared review "
                             "scope; reported and excluded.", [f"EXT-SYSTEMS-{sid}"], owner="Operations",
                             rationale="Scope is the eight registered EU programme systems (interview 1 line 81).",
                             resolution_need="Operations confirms whether the scope should change."))
    for src, iss in [("EVIDENCE", i) for i in ev_cap.issues] + [("CALENDAR", i) for i in caps["CALENDAR"].issues]:
        gaps.append(_rec(f"GAP-{iss['record_id']}-{iss['field'].upper()}-INVALID", f"{src} row {iss['row']} "
                         f"({iss['record_id']}) field {iss['field']}='{iss['value']}': {iss['problem']}. Not guessed.",
                         [f"EXT-{src}-{iss['record_id']}"], owner="Operations", rationale="ASSIGN changed-inputs rule.",
                         resolution_need="Source owner corrects the value."))

    for name in COMPANY:
        if not caps[name].usable:
            gaps.append(_rec(f"GAP-SOURCE-{name}", f"Company source {name} is {caps[name].status}; facts depending "
                             "on it are unresolved and the run is blocked (D-002).", [a["id"] for a in caps[name].attempts],
                             owner="Operations", rationale="; ".join(caps[name].reasons) or caps[name].status,
                             resolution_need=f"Restore a suitable live read of {name} and re-run."))

    return {"system_facts": system_facts, "policy_controls": policy_controls, "incident_evidence": incident_evidence,
            "conflicts": conflicts, "evidence_gaps": gaps, "_licensed": licensed, "_ev_by_sys": ev_by_sys,
            "_policy_located": policy_meta}


# ============================================================ stage 05

def _applicability(rule: dict, f: dict, cues: dict, licensed: bool, otypes: dict):
    """Return (applies: True/False/None, reason, extra evidence ids) from recorded facts only."""
    rid = rule["id"]
    otype, kind = f.get("output_type"), otypes.get(f.get("output_type") or "", None)
    prov, depl = f.get("provider_role"), f.get("deployer_role")
    if otype is None or kind is None:
        return None, "output_type is missing or outside its disclosed meanings", []

    if rid in ("L-50-1", "L-50-2"):
        relevant = (kind == "interaction") if rid == "L-50-1" else kind in ("interaction", "generated-text", "generated-media")
        if not relevant:
            return False, (f"Recorded output_type '{otype}' is not "
                           f"{'direct interaction' if rid == 'L-50-1' else 'synthetic content generation'}."), []
        if prov == "no":
            return False, (f"Draft reading for Legal review: Art. 50({rid[-1]}) places this duty on providers "
                           "(\"Providers shall ensure ...\"). SYSTEMS records provider_role=no"
                           + (" and POLICY records a licensed third-party supplier product that Quillhaven did not "
                              "develop, commission or place on the market under its own name or trademark" if licensed else "")
                           + ". The automation does not determine provider status; Legal confirms whether Quillhaven is "
                           "the provider of this system. This row is not a finding that no transparency duty applies: "
                           "the internal-policy rows for the same system are assessed separately."), []
        if prov == "yes":
            return True, "SYSTEMS records provider_role=yes for a system within the paragraph's subject matter.", []
        return None, f"provider_role is '{prov}'; the provider-side duty cannot be assessed.", []

    if rid == "L-50-3":
        if depl != "yes":
            return None if depl in (None, "unknown") else False, f"deployer_role={depl}.", []
        if cues.get("emotion_or_biometric_unestablished"):
            return None, ("POLICY states that emotion-recognition / biometric-categorisation use is not yet "
                          "established for the current release."), cues["emotion_or_biometric_unestablished"]
        if cues.get("no_emotion_or_biometric"):
            return False, "POLICY states that the system does not perform emotion recognition or biometric categorisation.", \
                cues["no_emotion_or_biometric"]
        if kind == "classification":
            return None, "Classification system with no recorded statement on emotion recognition or biometric categorisation.", []
        return False, (f"Recorded function is '{otype}'; no source records emotion recognition or biometric "
                       "categorisation."), []

    if rid == "L-50-4-DF":
        if kind != "generated-media":
            return False, f"Recorded output_type '{otype}' is not generated image, audio or video.", []
        if depl != "yes":
            return None, f"deployer_role={depl}.", []
        if cues.get("deep_fake_indicators"):
            return True, ("POLICY records that the content shows real people, could be mistaken for an authentic "
                          "recording and is not an evidently artistic or fictional work."), cues["deep_fake_indicators"]
        if cues.get("not_existing_person_depiction"):
            return False, ("POLICY records that the generated media does not depict existing persons, places, objects or "
                           "events presented as authentic."), cues["not_existing_person_depiction"]
        return None, "No recorded facts on whether the generated media resembles existing persons or events.", []

    if rid == "L-50-4-TXT":
        if kind != "generated-text":
            return False, f"Recorded output_type '{otype}' is not text published by the deployer.", []
        if cues.get("not_public_interest_text"):
            return False, "POLICY records that the generated text is not published to inform the public on matters of public interest.", \
                cues["not_public_interest_text"]
        return None, "No recorded facts on whether generated text is published on matters of public interest.", []

    if rid == "POL-T1":
        if cues.get("no_direct_conversation"):
            return False, "POLICY records that the people concerned do not interact directly with the AI product.", \
                cues["no_direct_conversation"]
        if kind == "interaction":
            return True, f"SYSTEMS records direct interaction with {f.get('exposed_group')}.", []
        return False, f"Recorded output_type '{otype}' is not direct interaction.", []

    if rid in ("POL-T2-PROV", "POL-T2-LABEL"):
        if kind == "generated-media" and f.get("exposed_group") == "public":
            return True, f"SYSTEMS records public synthetic media ({otype}, exposed_group=public).", []
        return False, f"Not public synthetic media (output_type={otype}, exposed_group={f.get('exposed_group')}).", []

    if rid == "POL-T3":
        if kind == "generated-text":
            return True, f"SYSTEMS records a text-generation tool used by staff (exposed group {f.get('exposed_group')}).", []
        return False, f"Recorded output_type '{otype}' is not a staff text-drafting tool.", []
    return None, "No applicability rule defined.", []


def attribute_records(records: list[dict], subjects: dict) -> dict[str, list[str]]:
    """Map each EVIDENCE record to the evidence subjects its own text names (D-004, revised).
    A record naming no subject is unattributed context and affects no register row."""
    out = {}
    for r in records:
        text = f"{r.get('evidence_ref', '')} {r.get('notes', '')}".lower()
        out[r["record_id"]] = sorted(
            name for name, spec in subjects.items()
            if any(p in text for p in spec["patterns"]) or r.get("record_type") in spec.get("record_types", []))
    return out


def impact_analysis(caps, rules, scope, stage03, stage04, run_blocked: bool) -> dict:
    otypes = rules["output_types"]
    effect = rules["evidence_state_effect"]
    subjects = rules["evidence_subjects"]
    facts = {r["system_id"]: r for r in stage04["system_facts"]}
    rule_located = {r["rule_id"]: r["located"] for r in stage03["binding_rules"]}
    rule_located.update(stage04["_policy_located"])
    failed = [n for n, c in caps.items() if not c.usable]
    policy_inputs_ok = all(caps[n].usable for n in ("POLICY", "SYSTEMS", "EVIDENCE"))
    ev_by_sys = stage04["_ev_by_sys"]
    attribution = attribute_records([r for rs in ev_by_sys.values() for r in rs], subjects)
    impacts = []

    def recs_for(sid: str, rule: dict, affects: str) -> list[dict]:
        wanted = {sname for sname in rule["evidence_subjects"] if subjects[sname]["affects"] == affects}
        return [r for r in ev_by_sys.get(sid, []) if wanted & set(attribution.get(r["record_id"], []))]

    def describe(recs: list[dict], rule: dict) -> str:
        parts = []
        for r in recs:
            others = [x for x in attribution[r["record_id"]] if x not in rule["evidence_subjects"]]
            parts.append(f"{r['record_id']} ({r['evidence_state']}): {r['notes']}" +
                         (f" [record also names {', '.join(others)}; its single recorded state is applied to each "
                          "rule it names and is not split by the automation]" if others else ""))
        return "; ".join(parts)

    def rec_ev(recs):
        return [f"EXT-EVIDENCE-{r['record_id']}" for r in recs] + [r["record_id"] for r in recs]

    for sid in scope["systems_in_scope"]:
        fr = facts.get(sid)
        for rule in rules["rules"]:
            iid = f"IMP-{sid}-{rule['id']}"
            basis = rule["basis"]
            ev_ids = [f"RULE-{rule['id']}" if basis == "binding-law" else f"POLCTL-{rule['id']}"]
            owner = fr["owner"] if fr else "Operations"
            scope_text = (f"Draft reading of the binding Article 50 text as of {scope['as_of_date']} for {sid} only. "
                          "Actor role (provider/deployer), applicability and interpretation are for Legal to decide; "
                          "not legal advice and not a compliance finding." if basis == "binding-law" else
                          f"Draft internal-policy reading as of {scope['as_of_date']} for {sid} only; Legal owns policy "
                          "interpretation boundaries; not a compliance finding.")
            common = dict(system_id=sid, rule_id=rule["id"], rule_ref=rule["rule_ref"], rule_basis=basis,
                          required_reviewer="Legal", approval_status="pending", conclusion_scope=scope_text)

            def emit(state, applicability, reason, need, extra_ev=(), control=None, needs_action=False,
                     attributed=()):
                impacts.append(_rec(iid, f"{sid} × {rule['rule_ref']}: {state}", ev_ids + list(extra_ev), owner=owner,
                                    rationale=reason, state=state, applicability=applicability,
                                    control_status=control, resolution_need=need, needs_action=needs_action,
                                    attributed_record_ids=sorted({r["record_id"] for r in attributed}),
                                    evidence_subjects=rule["evidence_subjects"], **common))

            if run_blocked and basis == "binding-law":
                emit("unresolved", "withheld", "Formal Article 50 conclusion withheld: required source(s) "
                     f"{', '.join(failed)} not suitably retrieved (D-002).",
                     "Restore every required source and re-run; Legal then reviews the draft interpretation.",
                     [f"BLK-{n}" for n in failed if n in BINDING + ADVISORY])
                continue
            if basis == "internal-policy" and not policy_inputs_ok:
                emit("unresolved", "withheld", "Internal-policy evaluation not possible: required company input(s) "
                     f"{', '.join(n for n in ('POLICY', 'SYSTEMS', 'EVIDENCE') if not caps[n].usable)} unavailable.",
                     "Restore the company sources and re-run.", [f"GAP-SOURCE-{n}" for n in COMPANY if not caps[n].usable])
                continue
            if fr is None:
                emit("unresolved", "unknown", f"No usable SYSTEMS register facts for {sid}.",
                     "Operations restores the register entry.", [f"GAP-{sid}-ABSENT"])
                continue
            ev_ids.append(fr["id"])
            if not rule_located.get(rule["id"]):
                emit("unresolved", "unknown", "Rule text not located in a usable live source.",
                     "Source owner restores the rule text; re-run.")
                continue
            f = fr["fields"]
            # Stale register facts: the applicability inputs themselves (output_type, roles, exposure) are stale.
            if f.get("evidence_status") == "stale":
                stale_recs = [r for r in ev_by_sys.get(sid, []) if r["evidence_state"] == "stale"]
                emit("unresolved", "unknown", f"The SYSTEMS register entry for {sid} is stale (evidence_updated_at "
                     f"{f.get('evidence_updated_at')}), so the applicability facts used for every rule are stale; no "
                     "conclusion is drawn from stale facts." +
                     (f" Stale record(s): {describe(stale_recs, rule)}." if stale_recs else ""),
                     f"{owner} refreshes the register entry and evidence.", [f"GAP-{sid}-REGISTER-STALE"] +
                     [f"GAP-{r['record_id']}" for r in stale_recs], needs_action=True, attributed=stale_recs)
                continue
            # Records that bear on applicability (provider role, emotion/biometric use) for this rule.
            app_recs = recs_for(sid, rule, "applicability")
            bad_app = [r for r in app_recs if effect.get(r["evidence_state"], "unresolved") != "supports"]
            if bad_app:
                st = "conflicting" if any(r["evidence_state"] == "conflicting" for r in bad_app) else "unresolved"
                emit(st, "unknown", f"Applicability evidence for this rule is not settled: {describe(bad_app, rule)}.",
                     f"{owner} supplies current applicability facts; Legal then reviews.", rec_ev(bad_app) +
                     [f"GAP-{r['record_id']}" for r in bad_app if r["evidence_state"] != "conflicting"],
                     needs_action=True, attributed=bad_app)
                continue
            applies, why, cue_ev = _applicability(rule, f, fr["policy_cues"], fr["licensed_supplier_product"], otypes)
            if applies is False:
                emit("supported-no-impact", "not-applicable-on-recorded-facts", why,
                     "None for the system owner; Legal confirms or corrects the draft reading.", cue_ev + rec_ev(app_recs),
                     attributed=app_recs)
                continue
            if applies is None:
                emit("unresolved", "unknown", why, f"{owner} supplies the missing fact; Legal then reviews.", cue_ev)
                continue
            # Rule applies: the state comes only from records attributed to this rule's control subjects (D-004).
            recs = recs_for(sid, rule, "control")
            if not recs:
                emit("unresolved", "applies-on-recorded-facts", f"{why} No EVIDENCE record for {sid} addresses this "
                     f"rule's control ({', '.join(rule['evidence_subjects'])}); "
                     f"{rule.get('control_note', 'control evidence is missing')}.",
                     f"{owner} supplies evidence for the control.", cue_ev, needs_action=True)
                continue
            effects = {effect.get(r["evidence_state"], "unresolved") for r in recs}
            notes = describe(recs, rule)
            if "conflicting" in effects:
                conf = [r for r in recs if r["evidence_state"] == "conflicting"]
                emit("conflicting", "applies-on-recorded-facts", f"{why} Evidence for this rule conflicts (D-001): "
                     f"{notes}. Both facts are preserved; the item remains unresolved pending system-owner "
                     "verification and is not decided by the automation.",
                     "; ".join(c["resolution_need"] for c in stage04["conflicts"]
                               if c.get("record_id") in {r["record_id"] for r in conf}),
                     cue_ev + rec_ev(recs) + [f"CONF-{r['record_id']}" for r in conf],
                     control="contested", needs_action=True, attributed=recs)
                continue
            if "unresolved" in effects:
                weak = [r for r in recs if effect.get(r["evidence_state"], "unresolved") == "unresolved"]
                emit("unresolved", "applies-on-recorded-facts", f"{why} Evidence for this rule is incomplete: {notes}.",
                     f"{owner} supplies current, complete evidence" +
                     ("; Legal decides the exception request" if any(r["record_type"] == "exception_request" for r in weak)
                      else "") + ".", cue_ev + rec_ev(recs) + [f"GAP-{r['record_id']}" for r in weak],
                     control="evidence " + ", ".join(sorted({r["evidence_state"] for r in weak})),
                     needs_action=True, attributed=recs)
                continue
            cf = rule.get("control_field")
            val = f.get(cf) if cf else None
            if cf and val in (None, "unknown"):
                emit("unresolved", "applies-on-recorded-facts", f"{why} Control field {cf} is {val or 'invalid'}; "
                     f"attributed evidence: {notes}.", f"{owner} records the control state.", cue_ev + rec_ev(recs),
                     control=f"{cf}={val}", needs_action=True, attributed=recs)
            elif cf and val not in rule.get("control_ok_values", []):
                emit("supported-impact", "applies-on-recorded-facts", f"{why} Control gap recorded: {cf}={val}, "
                     f"consistent with {notes}.", f"{owner} closes the recorded control gap; Operations approves "
                     "activation and dates.", cue_ev + rec_ev(recs), control=f"gap: {cf}={val}", needs_action=True,
                     attributed=recs)
            else:
                emit("supported-impact", "applies-on-recorded-facts", f"{why} Control evidenced"
                     + (f" ({cf}={val})" if cf else "") + f" by {notes}.",
                     "None for the control; Legal confirms the draft reading.", cue_ev + rec_ev(recs),
                     control=f"evidenced{': ' + cf + '=' + val if cf else ''}", attributed=recs)

    unaffected, conflicts, unresolved = [], [], []
    for sid in scope["systems_in_scope"]:
        rows = [i for i in impacts if i["system_id"] == sid and i["state"] == "supported-no-impact"]
        if rows:
            unaffected.append(_rec(f"UNAFF-{sid}", "No impact on recorded facts for "
                                   + ", ".join(r["rule_id"] for r in rows) + " (draft; Legal confirms).",
                                   [e for r in rows for e in r["evidence_ids"]], owner=rows[0]["owner"],
                                   rationale="Supported no-impact rows grouped per system.",
                                   impact_ids=[r["id"] for r in rows]))
    for i in impacts:
        if i["state"] == "conflicting":
            conflicts.append(_rec(f"CONFLICT-{i['id']}", i["rationale"], i["evidence_ids"], owner=i["owner"],
                                  rationale="D-001", impact_id=i["id"], resolution_need=i["resolution_need"]))
        elif i["state"] == "unresolved":
            unresolved.append(_rec(f"UNRES-{i['id']}", i["rationale"], i["evidence_ids"], owner=i["owner"],
                                   rationale="Missing, stale, withheld or unknown facts.", impact_id=i["id"],
                                   resolution_need=i["resolution_need"]))
    return {"impacts": impacts, "unaffected_items": unaffected, "conflicts": conflicts, "unresolved_items": unresolved}


# ============================================================ stage 06

def actions_and_approvals(caps, rules, scope, stage05, run_id: str, source_versions: dict) -> dict:
    cal_rows = caps["CALENDAR"].parsed.get("rows", []) if caps["CALENDAR"].usable else []
    rules_by_id = {r["id"]: r for r in rules["rules"]}
    actions: dict[str, dict] = {}
    for imp in stage05["impacts"]:
        if not imp.get("needs_action"):
            continue
        sid, rule = imp["system_id"], rules_by_id[imp["rule_id"]]
        cands = [r for r in cal_rows if r["system_id"] == sid]
        match = [r for r in cands if any(c in r["action"].lower() for c in rule["action_cues"])]
        chosen = match[0] if match else (cands[0] if len(cands) == 1 else None)
        if chosen:
            aid = chosen["action_id"]
            a = actions.setdefault(aid, _rec(
                aid, chosen["action"], [f"EXT-CALENDAR-{aid}"], owner=chosen["owner"] or None,
                rationale="Existing CALENDAR action linked to review findings to avoid duplication (D-005).",
                origin="calendar-linked", system_id=sid, action=chosen["action"],
                proposed_due_date=chosen["due_date"] or None,
                date_basis=("Operations-proposed date from CALENDAR " + chosen.get("source_version", "")).strip()
                if chosen["due_date"] else "No date in CALENDAR; left blank (Operations to propose).",
                calendar_status=chosen["status"], approval_required=chosen["approval_required"],
                responsible_role=chosen["owner"] or None, impact_ids=[],
                link_basis="action cue match" if match else "sole CALENDAR action for the system",
                uid=f"{aid}@{UID_DOMAIN}"))
        else:
            aid = f"PA-{sid}-{rule['id']}"
            a = actions.setdefault(aid, _rec(
                aid, rule["new_action_text"], [], owner=imp["owner"],
                rationale="New proposal from review findings; no linkable CALENDAR action (D-005).",
                origin="proposed-new", system_id=sid, action=rule["new_action_text"], proposed_due_date=None,
                date_basis="Undated: no Operations-proposed date exists; omitted from the ICS (interview 2 line 140).",
                calendar_status=None, approval_required="legal" if imp["rule_basis"] == "binding-law" else "operations",
                responsible_role=imp["owner"], impact_ids=[], link_basis=None,
                candidate_calendar_actions=[r["action_id"] for r in cands], uid=f"{aid}@{UID_DOMAIN}"))
        a["impact_ids"].append(imp["id"])
        a["evidence_ids"] = sorted(set(a["evidence_ids"]) | {imp["id"]})
    linked = set(actions)
    for r in cal_rows:
        if r["action_id"] in linked:
            continue
        aid = r["action_id"]
        actions[aid] = _rec(aid, r["action"], [f"EXT-CALENDAR-{aid}"], owner=r["owner"] or None,
                            rationale="Existing CALENDAR action carried forward; not derived from this review's "
                            "findings (kept to avoid loss of work, D-005).", origin="calendar-carried-forward",
                            system_id=r["system_id"], action=r["action"], proposed_due_date=r["due_date"] or None,
                            date_basis=("Operations-proposed date from CALENDAR " + r.get("source_version", "")).strip()
                            if r["due_date"] else "No date in CALENDAR.", calendar_status=r["status"],
                            approval_required=r["approval_required"], responsible_role=r["owner"] or None,
                            impact_ids=[], link_basis=None, uid=f"{aid}@{UID_DOMAIN}")
    for a in actions.values():
        reviewer = {"legal": "Legal", "operations": "Operations"}.get(a["approval_required"], "Operations")
        a["required_reviewer"] = reviewer
        a["approval_status"] = "pending"
        date = a["proposed_due_date"]
        a["dated"] = bool(date and parse_iso_date(date))
        if date and not parse_iso_date(date):
            a["proposed_due_date"] = None
            a["dated"] = False
            a["date_basis"] = f"CALENDAR value '{date}' is not a YYYY-MM-DD date; left blank and reported."
    ordered = [actions[k] for k in sorted(actions)]

    approvals = []
    for a in ordered:
        approvals.append(_rec(f"APR-{a['id']}", f"{a['required_reviewer']} approval of proposed action {a['id']} "
                              f"({a['action']}) for {a['system_id']}, including owner and date.", [a["id"]],
                              owner=a["required_reviewer"], rationale="No approval outcome is recorded in any source (D-006).",
                              status="pending", subject_action_id=a["id"], approver_role=a["required_reviewer"]))
    approvals.append(_rec("APR-LEGAL-A50-INTERPRETATION", "Legal review of the draft Article 50 applicability "
                          "interpretation for all binding-law register rows.",
                          [i["id"] for i in stage05["impacts"] if i["rule_basis"] == "binding-law"], owner="Legal",
                          rationale="Legal owns final interpretation (interview 2 line 108).", status="pending",
                          approver_role="Legal"))
    approvals.append(_rec("APR-LEGAL-POLICY-INTERPRETATION", "Legal review of the draft internal-policy interpretation "
                          "boundaries for all internal-policy register rows.",
                          [i["id"] for i in stage05["impacts"] if i["rule_basis"] == "internal-policy"], owner="Legal",
                          rationale="Legal approves policy interpretation boundaries (interview 1 line 220).",
                          status="pending", approver_role="Legal"))

    escalations = []
    for i in stage05["impacts"]:
        if i["state"] in ("conflicting", "unresolved"):
            linked_actions = [a["id"] for a in ordered if i["id"] in a["impact_ids"]]
            escalations.append(_rec(f"ESC-{i['id']}", f"{i['state']}: {i['rationale']}", [i["id"]] + linked_actions,
                                    owner=i["owner"], rationale="Kept visible until evidence or an actual decision changes it.",
                                    impact_id=i["id"], resolution_owner=i["owner"], resolution_need=i["resolution_need"],
                                    linked_action_ids=linked_actions))

    def versions(names):
        return {n: source_versions[n] for n in names if n in source_versions}

    review_requests = [
        _rec("RR-A50", "Review of the draft Article 50 applicability interpretation (binding-law rows).",
             [i["id"] for i in stage05["impacts"] if i["rule_basis"] == "binding-law"], owner="Legal",
             rationale="Legal owns final interpretation.", request_id="RR-A50", run_id=run_id,
             subject={"impact_ids": [i["id"] for i in stage05["impacts"] if i["rule_basis"] == "binding-law"]},
             source_versions=versions(BINDING + ADVISORY + ("SYSTEMS", "POLICY", "EVIDENCE")),
             question="Do you confirm, correct or reject each draft Article 50 state and its reason, including the "
                      "unresolved and withheld items? See the specific questions listed.",
             questions=[
                 "Q1 (Art. 50(1)/(2)): Is Quillhaven the provider of any in-scope system? The draft treats it as not "
                 "the provider wherever SYSTEMS records provider_role=no and POLICY records a licensed supplier product.",
                 "Q2 (Art. 50(4) deep fake): Do you confirm the draft readings that AI-008 (dubbed presenter videos) "
                 "falls within the deep-fake disclosure duty and AI-003 (illustrated fictional scenes) does not?",
                 "Q3 (Art. 50(3)): Once Assessment Operations refreshes AI-005's release facts, does AI-005 perform "
                 "emotion recognition or biometric categorisation?",
                 "Q4 (Art. 50(4) text): Do you confirm that AI-002 and AI-006 outputs are not text published to inform "
                 "the public on matters of public interest?",
                 "Q5 (version): Do you confirm CONSOLIDATED 02024R1689-20260727, reconciled with OJ 2024/1689 and "
                 "AMEND 2026/1744, as the binding text effective on 26 August 2026?"],
             required_reviewer="Legal", approval_record="APR-LEGAL-A50-INTERPRETATION",
             delivery_status="prepared; not sent by the automation"),
        _rec("RR-POLICY", "Review of the draft internal-policy interpretation boundaries (internal-policy rows).",
             [i["id"] for i in stage05["impacts"] if i["rule_basis"] == "internal-policy"], owner="Legal",
             rationale="Legal approves policy interpretation boundaries.", request_id="RR-POLICY", run_id=run_id,
             subject={"impact_ids": [i["id"] for i in stage05["impacts"] if i["rule_basis"] == "internal-policy"]},
             source_versions=versions(("POLICY", "SYSTEMS", "EVIDENCE")),
             question="Do you confirm the draft policy-rule states, conflicts and resolution owners?",
             required_reviewer="Legal", approval_record="APR-LEGAL-POLICY-INTERPRETATION",
             delivery_status="prepared; not sent by the automation"),
    ]
    for a in ordered:
        review_requests.append(_rec(
            f"RR-{a['id']}", f"{a['required_reviewer']} decision on proposed action {a['id']} for {a['system_id']}.",
            [a["id"]] + a["impact_ids"], owner=a["required_reviewer"], rationale="Action approval stays with the "
            "responsible role.", request_id=f"RR-{a['id']}", run_id=run_id,
            subject={"system_id": a["system_id"], "action_id": a["id"], "impact_ids": a["impact_ids"]},
            source_versions=versions(("CALENDAR", "SYSTEMS", "EVIDENCE", "POLICY")),
            question=(f"Approve, reject or amend action '{a['action']}' with owner {a['owner'] or '(blank)'} and "
                      f"proposed date {a['proposed_due_date'] or '(undated)'}?"),
            required_reviewer=a["required_reviewer"], approval_record=f"APR-{a['id']}",
            delivery_status="prepared; not sent by the automation"))

    return {"proposed_actions": ordered, "approval_requirements": approvals, "escalations": escalations,
            "review_requests": review_requests}
