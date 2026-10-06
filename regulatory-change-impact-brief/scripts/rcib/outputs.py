"""Final drafts: impact-register.csv, compliance-brief.md, action-calendar.ics."""

from __future__ import annotations

import csv
import datetime as dt
import io

REGISTER_COLUMNS = ["impact_id", "system_id", "rule_ref", "state", "evidence_ids", "reason", "owner",
                    "proposed_action", "proposed_due_date", "approval_status",
                    # extra columns (allowed by the assignment)
                    "run_id", "rule_id", "rule_basis", "applicability", "control_status", "resolution_need",
                    "linked_action_id", "action_owner", "required_reviewer", "conclusion_scope"]
PRODID = "-//Quillhaven Academy//regulatory-change-impact-brief 1.0//EN"


def action_for(impact_id: str, actions: list[dict]) -> dict | None:
    for a in actions:
        if impact_id in a["impact_ids"]:
            return a
    return None


def register_rows(run_id: str, impacts: list[dict], actions: list[dict]) -> list[dict]:
    rows = []
    for i in impacts:
        a = action_for(i["id"], actions)
        reason = i["rationale"]
        if a and not a["dated"]:
            reason += f" Proposed action {a['id']} is undated: {a['date_basis']}"
        if a and not a.get("owner"):
            reason += " Action owner unknown in CALENDAR; Operations to assign."
        rows.append({
            "impact_id": i["id"], "system_id": i["system_id"], "rule_ref": i["rule_ref"], "state": i["state"],
            "evidence_ids": ";".join(i["evidence_ids"]), "reason": reason, "owner": i["owner"] or "",
            "proposed_action": f"{a['id']}: {a['action']}" if a else "",
            "proposed_due_date": (a["proposed_due_date"] or "") if a else "",
            "approval_status": a["approval_status"] if a else i["approval_status"],
            "run_id": run_id, "rule_id": i["rule_id"], "rule_basis": i["rule_basis"],
            "applicability": i["applicability"], "control_status": i["control_status"] or "",
            "resolution_need": i["resolution_need"], "linked_action_id": a["id"] if a else "",
            "action_owner": (a["owner"] or "") if a else "",
            "required_reviewer": a["required_reviewer"] if a else i["required_reviewer"],
            "conclusion_scope": i["conclusion_scope"],
        })
    return rows


def render_register(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=REGISTER_COLUMNS, lineterminator="\r\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue().encode("utf-8")


# ------------------------------------------------------------------ ICS

def _ics_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n")


def _fold(line: str) -> str:
    out, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > (75 if not out else 74):
            out.append(cur.decode("utf-8"))
            cur = b""
        cur += b
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def calendar_events(actions: list[dict], run_blocked: bool) -> list[dict]:
    if run_blocked:
        return []  # D-002: the final calendar is empty in a blocked run
    return [a for a in actions if a["dated"]]


def render_ics(run_id: str, dtstamp_utc: str, events: list[dict]) -> bytes:
    stamp = dtstamp_utc.replace("-", "").replace(":", "")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{PRODID}", "CALSCALE:GREGORIAN",
             f"X-WR-CALNAME:Article 50 review draft actions ({run_id})"]
    for a in events:
        start = a["proposed_due_date"].replace("-", "")
        end = (dt.date.fromisoformat(a["proposed_due_date"]) + dt.timedelta(days=1)).strftime("%Y%m%d")
        desc = (f"Action: {a['id']}\nSystem: {a['system_id']}\nResponsible role: {a['responsible_role'] or 'unassigned'}\n"
                f"Basis: {a['date_basis']}; origin {a['origin']}; linked findings: "
                f"{', '.join(a['impact_ids']) or 'none (carried forward from CALENDAR)'}\n"
                f"Approval status: {a['approval_status']} ({a['required_reviewer']} approval required)\n"
                f"Run: {run_id}\nDraft proposal for review; not an approved deadline.")
        lines += ["BEGIN:VEVENT", f"UID:{a['uid']}", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{start}",
                  f"DTEND;VALUE=DATE:{end}", _fold(f"SUMMARY:{_ics_escape(f'[Proposed] {a['id']} {a['system_id']}: {a['action']}')}"),
                  _fold(f"DESCRIPTION:{_ics_escape(desc)}"), "STATUS:TENTATIVE", "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


# ------------------------------------------------------------------ brief

def _md_cell(s) -> str:
    return str(s if s is not None else "").replace("|", "\\|").replace("\n", " ")


def _first_sentence(text: str | None, limit: int = 260) -> str:
    if not text:
        return "(paragraph text not available in this run)"
    cut = text.find(". ")
    t = text[: cut + 1] if 0 < cut < limit else text[:limit] + "…"
    return t.replace('"', "'")


def legal_boundary_section(ctx: dict) -> list[str]:
    """Section 2: what the automation decided, what it did not, and what Legal must decide (Art. 50(1)/(2) focus)."""
    s03, impacts = ctx["stage03"], ctx["stage05"]["impacts"]
    rules = {r["rule_id"]: r for r in s03["binding_rules"]}
    blocked = ctx["run_status"] == "blocked"
    rows = {i["id"]: i for i in impacts}
    prov_rows = [i for i in impacts if i["rule_id"] in ("L-50-1", "L-50-2") and i["state"] == "supported-no-impact"
                 and "places this duty on providers" in (i["rationale"] or "")]
    prov_systems = sorted({i["system_id"] for i in prov_rows})
    other_12 = [i for i in impacts if i["rule_id"] in ("L-50-1", "L-50-2") and i not in prov_rows]
    L = ["## 2. Legal-review boundary", ""]
    L.append("**This draft does not interpret the EU AI Act, decide actor roles (provider or deployer), decide "
             "applicability, or assess compliance.** It sets out the binding text, the recorded company facts and a draft "
             "reading of how they fit, so Legal can confirm, correct or reject it (request `RR-A50`). Every "
             "binding-law register row carries this scope in its `conclusion_scope` column.")
    L.append("")
    if blocked:
        L.append("Because this run is **blocked**, no Article 50 reading is offered: every binding-law row is "
                 "`unresolved` with applicability `withheld` (decision D-002).")
        L.append("")
        return L
    L.append("### 2.1 Article 50(1) and 50(2): provider-side duties")
    L.append("")
    for rid, para in (("L-50-1", 1), ("L-50-2", 2)):
        r = rules.get(rid)
        L.append(f"- **Art. 50({para})** (binding text, `EXT-CONSOLIDATED-ART50-{para}`): "
                 f"\"{_first_sentence(r['paragraph_text'] if r else None)}\"")
    L.append("")
    L.append("**Draft reading used, for Legal to confirm.** Both paragraphs are addressed to *providers*. Where SYSTEMS "
             "records `provider_role=no` and POLICY records that Quillhaven licenses a third-party supplier's existing "
             "product (it did not develop or commission it, or place it on the market under its own name or trademark), "
             "the 50(1) and 50(2) rows are drafted as `supported-no-impact`"
             + (f" for {', '.join(prov_systems)}" if prov_systems else "") + ".")
    L.append("")
    L.append("**What this reading depends on, and what the automation did not decide:**")
    L.append("")
    L.append("1. *Provider status.* The reading rests on the recorded `provider_role` value and the POLICY licensing "
             "statement. Whether Quillhaven is, or has become, the provider of any system is a legal determination. The "
             "automation has not made it, and it has not assessed any circumstance that could change the role. The "
             "Commission FAQ (advisory, `EXT-FAQ-INTRO`) cites the Article 3(3) definition of provider; it is context, "
             "not a determination.")
    L.append("2. *Not a finding that no transparency duty applies.* Deployer-side duties (Art. 50(3), 50(4)) are "
             "assessed in their own rows. The internal-policy interaction-notice rule (POL-T1) applies independently "
             "and is where the interaction-notice control is assessed (evidenced, a recorded gap, or conflicting): "
             + ", ".join(f"`{i}` ({rows[i]['state']})" for i in ("IMP-AI-001-POL-T1", "IMP-AI-004-POL-T1",
                                                                "IMP-AI-007-POL-T1") if i in rows) + ".")
    L.append("3. *Transition.* The Art. 50(2) transitional deadline (`TIME-ART111-4`) applies to providers only. It is "
             "recorded as context and not applied to any system.")
    if other_12:
        L.append("4. *Rows not resting on the provider reading:* "
                 + ", ".join(f"`{i['id']}` ({i['state']})" for i in other_12)
                 + ". These are no-impact on output type, or unresolved because of stale or unknown facts.")
    L.append("")
    L.append("### 2.2 Questions for Legal (part of `RR-A50`)")
    L.append("")
    for q in ctx["stage06"]["review_requests"][0].get("questions", []):
        L.append(f"- {q}")
    L.append("")
    return L


def render_brief(ctx: dict) -> bytes:
    run_id, run_status = ctx["run_id"], ctx["run_status"]
    s05, s06, s04, s03 = ctx["stage05"], ctx["stage06"], ctx["stage04"], ctx["stage03"]
    impacts, actions = s05["impacts"], s06["proposed_actions"]
    counts = {k: sum(1 for i in impacts if i["state"] == k) for k in
              ("supported-impact", "supported-no-impact", "conflicting", "unresolved")}
    L = []
    w = L.append
    w("# Article 50 Compliance Impact Brief — DRAFT")
    w("")
    w(f"- **Run ID:** `{run_id}`")
    w(f"- **As-of (business observation) date:** {ctx['as_of_date']} (fixed; retrieval times are recorded separately)")
    w(f"- **Run started (UTC):** {ctx['created_at']}")
    w(f"- **Recipients:** Legal; Operations (Quillhaven Academy, EU programme team)")
    w(f"- **Draft status:** review-ready DRAFT. Not legal advice, not an approval, not sent to any reviewer.")
    w(f"- **Run status:** **{run_status}** — {ctx['run_status_reason']}")
    if ctx.get("supersedes_run_id"):
        w(f"- **Supersedes run:** `{ctx['supersedes_run_id']}` ({ctx['change_reason']}); prior outputs retained under "
          f"`deliverables/history/{ctx['supersedes_run_id']}/`.")
    w(f"- **Review-request bindings:** each request below is bound to the exact path and SHA-256 of this brief, the "
      f"register and the calendar in `deliverables/snapshots/07-publication-validation.json` (`state.review_bindings`). "
      f"The brief does not contain its own hash.")
    w("")
    if run_status == "blocked":
        w("> **BLOCKED.** One or more required sources were not suitably retrieved. All formal Article 50 conclusions "
          "for this run are **withheld**. Factual reconciliation is shown for information only. The action calendar is "
          "intentionally empty. Do not treat this package as complete (decision D-002).")
        w("")
    elif run_status == "partial":
        w("> **PARTIAL.** Every required source was retrieved and verified, but some records are missing, stale, "
          "partial or conflicting. Conclusions below are limited to the stated scope; affected items remain unresolved or "
          "conflicting and are listed with owners. This package is not complete (decision D-002).")
        w("")

    w("## 1. Source quality and limitations")
    w("")
    w("| Source | Authority | Status | Retrieved (UTC) | Version / revision | Content hash |")
    w("|---|---|---|---|---|---|")
    for s in ctx["source_summary"]:
        w(f"| {s['name']} | {s['authority_class']} | **{s['status']}** | {s['retrieved_at']} | {_md_cell(s['version'])} | "
          f"`{(s['content_hash'] or 'null')[:19]}…` |")
    w("")
    w("Limitations:")
    for lim in ctx["limitations"]:
        w(f"- {lim}")
    w("")

    L.extend(legal_boundary_section(ctx))
    w("## 3. Supported observations")
    w("")
    w(f"Register totals: {counts['supported-impact']} supported-impact, {counts['supported-no-impact']} "
      f"supported-no-impact, {counts['conflicting']} conflicting, {counts['unresolved']} unresolved "
      f"({len(impacts)} system × rule rows). All states are **draft interpretations pending Legal review**; none is a "
      "compliance or non-compliance finding.")
    w("")
    w("### 3.1 Supported impacts")
    w("")
    sup = [i for i in impacts if i["state"] == "supported-impact"]
    if not sup:
        w("None supportable in this run.")
    else:
        w("| Impact ID | System | Rule (basis) | Control status | Action | Scope of conclusion |")
        w("|---|---|---|---|---|---|")
        for i in sup:
            a = action_for(i["id"], actions)
            w(f"| `{i['id']}` | {i['system_id']} | {_md_cell(i['rule_ref'])} | {_md_cell(i['control_status'])} | "
              f"{a['id'] if a else '—'} | {_md_cell(i['conclusion_scope'])} |")
        w("")
        for i in sup:
            w(f"- `{i['id']}`: {i['rationale']} Evidence: {', '.join('`' + e + '`' for e in i['evidence_ids'])}.")
    w("")
    w("### 3.2 Supported no-impact (by system)")
    w("")
    w("Binding-law no-impact rows are draft readings of the Article 50 text for Legal to confirm or correct "
      "(section 2); they are not findings that no transparency duty applies.")
    w("")
    if not s05["unaffected_items"]:
        w("None supportable in this run.")
    for u in s05["unaffected_items"]:
        w(f"- **{u['id'].removeprefix('UNAFF-')}** — {u['summary']} Rows: {', '.join('`' + x + '`' for x in u['impact_ids'])}.")
    w("")

    w("## 4. Conflicts and unresolved scope")
    w("")
    w("### 4.1 Conflicting evidence (both facts preserved; decision D-001)")
    w("")
    if not s04["conflicts"]:
        w("No source-level conflicts recorded.")
    for c in s04["conflicts"]:
        rows = [i["id"] for i in impacts if i["state"] == "conflicting" and i["system_id"] == c["system_id"]]
        w(f"- `{c['id']}` ({c['system_id']}, owner **{c['owner']}**): {c['summary']} Resolution need: "
          f"{c['resolution_need']} Register rows: {', '.join('`' + r + '`' for r in rows) or 'none'}."
          + (f" Note: {c['interview_note']}" if c.get("interview_note") else ""))
    w("")
    w("### 4.2 Unresolved items")
    w("")
    unres = [i for i in impacts if i["state"] == "unresolved"]
    if not unres:
        w("None.")
    else:
        w("| Impact ID | System | Rule | Owner | Why unresolved | Resolution need |")
        w("|---|---|---|---|---|---|")
        for i in unres:
            w(f"| `{i['id']}` | {i['system_id']} | {i['rule_id']} | {_md_cell(i['owner'])} | {_md_cell(i['rationale'])} | "
              f"{_md_cell(i['resolution_need'])} |")
    w("")
    w("### 4.3 Evidence gaps and authority blockers")
    w("")
    for b in s03["authority_blockers"]:
        w(f"- `{b['id']}` (authority blocker): {b['summary']} {b['rationale']}")
    for g in s04["evidence_gaps"]:
        w(f"- `{g['id']}` (owner {g['owner']}): {g['summary'].rstrip('.')}. Resolution: {g.get('resolution_need', '')}")
    if not s03["authority_blockers"] and not s04["evidence_gaps"]:
        w("None.")
    w("")

    w("## 5. Proposed actions and dates")
    w("")
    w("Dates are Operations-proposed dates taken from CALENDAR; the automation does not set or change deadlines "
      "(decision D-005). All are proposals with approval **pending**.")
    w("")
    if actions:
        w("| Action ID | System | Action | Owner (responsible role) | Proposed date | Origin | Approval | Linked impacts |")
        w("|---|---|---|---|---|---|---|---|")
        for a in actions:
            w(f"| `{a['id']}` | {a['system_id']} | {_md_cell(a['action'])} | {_md_cell(a['owner'] or '(unassigned)')} | "
              f"{a['proposed_due_date'] or '**undated**'} | {a['origin']} | {a['approval_status']} ({a['required_reviewer']}) | "
              f"{', '.join('`' + x + '`' for x in a['impact_ids']) or '—'} |")
    else:
        w("No actions proposed.")
    w("")
    undated = [a for a in actions if not a["dated"]]
    in_cal = ctx["calendar_event_ids"]
    w(f"Calendar: {len(in_cal)} tentative event(s) in `action-calendar.ics` ({', '.join(in_cal) or 'none'}).")
    if undated:
        w("Undated actions (omitted from the ICS, kept visible here and in the register):")
        for a in undated:
            w(f"- `{a['id']}` ({a['system_id']}, owner {a['owner'] or 'unassigned'}): {a['date_basis']}")
    if ctx["run_status"] == "blocked":
        w("The calendar is intentionally empty because the run is blocked (decision D-002).")
    w("")

    w("## 6. Decisions requested from Legal and Operations")
    w("")
    w("These review requests are **prepared, not sent**. No reply has been received or simulated.")
    w("")
    w("| Request ID | Required reviewer | Subject | Question | Evidence |")
    w("|---|---|---|---|---|")
    for r in s06["review_requests"]:
        subj = r["subject"].get("action_id") or f"{len(r['subject'].get('impact_ids', []))} register rows"
        ev = r["evidence_ids"][:6]
        w(f"| `{r['request_id']}` | {r['required_reviewer']} | {_md_cell(subj)} | {_md_cell(r['question'])} | "
          f"{', '.join('`' + e + '`' for e in ev)}{' …' if len(r['evidence_ids']) > 6 else ''} |")
    w("")
    w(f"Run `{run_id}`; source versions for each request are recorded in "
      "`deliverables/snapshots/06-actions-and-approvals.json` (`state.review_requests[].source_versions`).")
    if ctx.get("responses_note"):
        w("")
        w(ctx["responses_note"])
    w("")
    w("Escalations to resolution owners (system owners resolve factual behaviour; Legal owns interpretation and "
      "exceptions; Operations owns activation and dates):")
    w("")
    owners = {}
    for e in s06["escalations"]:
        owners.setdefault(e["resolution_owner"], []).append(e["impact_id"])
    for o, ids in sorted(owners.items()):
        w(f"- **{o}**: {', '.join('`' + x + '`' for x in ids)}")
    w("")

    w("## 7. Project decisions applied")
    w("")
    for d in ctx["decisions"]:
        w(f"- **{d['id']}** — {d['summary']} ({d['decided_by']})")
    w("")
    w("Full decision records: `regulatory-change-impact-brief/references/decisions.md` and each snapshot's `decisions`.")
    w("")

    w("## Appendix A. Full impact index")
    w("")
    w("| Impact ID | State | Basis | Applicability | Owner |")
    w("|---|---|---|---|---|")
    for i in impacts:
        w(f"| `{i['id']}` | {i['state']} | {i['rule_basis']} | {i['applicability']} | {_md_cell(i['owner'])} |")
    w("")
    w("## Appendix B. Evidence references")
    w("")
    w("Evidence IDs (`EXT-…`) resolve to `deliverables/sources/<SOURCE>.extracts.json`; attempt IDs (`ATT-…`) to "
      "`deliverables/snapshots/02-source-capture.json`; `REC-…`, `FACT-…`, `CONF-…`, `GAP-…`, `POLCTL-…` to "
      "`04-evidence-reconciliation.json`; `RULE-…`, `TIME-…`, `BLK-…` to `03-authority-and-timing.json`.")
    w("")
    return ("\n".join(L) + "\n").encode("utf-8")
