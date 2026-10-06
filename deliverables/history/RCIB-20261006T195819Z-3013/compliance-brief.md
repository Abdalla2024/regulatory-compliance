# Article 50 Compliance Impact Brief — DRAFT

- **Run ID:** `RCIB-20261006T195819Z-3013`
- **As-of (business observation) date:** 2026-08-26 (fixed; retrieval times are recorded separately)
- **Run started (UTC):** 2026-10-06T19:58:19Z
- **Recipients:** Legal; Operations (Quillhaven Academy, EU programme team)
- **Draft status:** review-ready DRAFT. Not legal advice, not an approval, not sent to any reviewer.
- **Run status:** **partial** — all ten required sources retrieved and verified; 3 conflicting and 13 unresolved register rows remain.
- **Review-request bindings:** each request below is bound to the exact path and SHA-256 of this brief, the register and the calendar in `deliverables/snapshots/07-publication-validation.json` (`state.review_bindings`). The brief does not contain its own hash.

> **PARTIAL.** Every required source was retrieved and verified, but some records are missing, stale, partial or conflicting. Conclusions below are limited to the stated scope; affected items remain unresolved or conflicting and are listed with owners. This package is not complete (decision D-002).

## 1. Source quality and limitations

| Source | Authority | Status | Retrieved (UTC) | Version / revision | Content hash |
|---|---|---|---|---|---|
| OJ | binding-legal | **retrieved** | 2026-10-06T19:58:19Z | publication=OJ L, 2024/1689, 12.7.2024 | `sha256:50bf43f2466a…` |
| AMEND | binding-legal | **retrieved** | 2026-10-06T19:58:21Z | publication_date=2026-07-24; entry_into_force_date=2026-07-27 | `sha256:f1fa5f0be069…` |
| CONSOLIDATED | binding-legal | **retrieved** | 2026-10-06T19:58:22Z | celex=02024R1689-20260727; consolidated_version_date=2026-07-27 | `sha256:b7a29486ccd7…` |
| LAW | advisory | **retrieved** | 2026-10-06T19:58:23Z | last-modified=Mon, 05 Oct 2026 07:11:36 GMT | `sha256:792b673040b1…` |
| TIME | advisory | **retrieved** | 2026-10-06T19:58:23Z | last-modified=Mon, 05 Oct 2026 07:38:03 GMT | `sha256:0a0f4470e0d6…` |
| FAQ | advisory | **retrieved** | 2026-10-06T19:58:24Z | page_last_update=2026-07-24; last-modified=Tue, 06 Oct 2026 19:01:05 GMT | `sha256:fb94306f8b38…` |
| POLICY | company | **retrieved** | 2026-10-06T19:58:25Z | policy_version=AI-POL-2026-08-15; context_revision=RC-CONTEXT-2026-09-12-R1 | `sha256:39d7d1bcc779…` |
| SYSTEMS | company | **retrieved** | 2026-10-06T19:58:25Z | in-source=register-2026-08-26; tabs=AI System Register | `sha256:5ccd555dac9d…` |
| EVIDENCE | company | **retrieved** | 2026-10-06T19:58:27Z | tabs=Incident Evidence Register | `sha256:3dacdd595cbb…` |
| CALENDAR | company | **retrieved** | 2026-10-06T19:58:28Z | in-source=calendar-2026-08-26; tabs=Compliance Calendar | `sha256:cb3e2ba90e96…` |

Limitations:
- LAW is a live advisory page last modified Mon, 05 Oct 2026 07:11:36 GMT, after the review date 2026-08-26; the retrieved revision may differ from the 26 Aug 2026 version (D-007).
- TIME is a live advisory page last modified Mon, 05 Oct 2026 07:38:03 GMT, after the review date 2026-08-26; the retrieved revision may differ from the 26 Aug 2026 version (D-007).
- FAQ is a live advisory page last modified Tue, 06 Oct 2026 19:01:05 GMT, after the review date 2026-08-26; the retrieved revision may differ from the 26 Aug 2026 version (D-007).
- POLICY context revision RC-CONTEXT-2026-09-12-R1 was authored 2026-09-12, after the review date; it states that it records owner-supplied facts and does not revise the dated registers (D-007).
- CONSOLIDATED (EUR-Lex consolidated version) is used as the working binding text after reconciliation against the OJ act and AMEND; Legal confirms the authoritative version (interview 2, line 100).
- Company sources are read through their existing share-link permission without credentials; they are not treated as public (D-003). The Notion page is read through its page-chunk endpoint, which is undocumented and may change.
- Impact states are derived from declared rules over recorded facts (D-004). A system's worst evidence state applies to all of its applicable rules, because records do not say which rule they evidence.
- No approval outcome exists in any source; every approval is pending (D-006). No review request has been sent.

## 2. Supported observations

Register totals: 3 supported-impact, 53 supported-no-impact, 3 conflicting, 13 unresolved (72 system × rule rows). All states are **draft interpretations pending Legal review**; none is a compliance or non-compliance finding.

### 2.1 Supported impacts

| Impact ID | System | Rule (basis) | Control status | Action | Scope of conclusion |
|---|---|---|---|---|---|
| `IMP-AI-001-POL-T1` | AI-001 | AI-POL Learner and public transparency, bullet 1 (interaction notice) [internal policy] | evidenced: current_notice=yes | — | Draft internal-policy interpretation as of 2026-08-26 for AI-001 only; pending Legal review; not a compliance finding. |
| `IMP-AI-004-POL-T1` | AI-004 | AI-POL Learner and public transparency, bullet 1 (interaction notice) [internal policy] | gap: current_notice=no | ACT-001 | Draft internal-policy interpretation as of 2026-08-26 for AI-004 only; pending Legal review; not a compliance finding. |
| `IMP-AI-006-POL-T3` | AI-006 | AI-POL Learner and public transparency, bullet 3 (staff-only tool output route) [internal policy] | evidenced by complete EVIDENCE record | — | Draft internal-policy interpretation as of 2026-08-26 for AI-006 only; pending Legal review; not a compliance finding. |

- `IMP-AI-001-POL-T1`: SYSTEMS records direct interaction with learners. Control recorded as current_notice=yes, supported by REC-001 (complete): Notice screenshot and release record agree. Evidence: `EXT-EVIDENCE-REC-001`, `FACT-AI-001`, `POLCTL-POL-T1`, `REC-001`.
- `IMP-AI-004-POL-T1`: SYSTEMS records direct interaction with learners. Control gap recorded: current_notice=no (REC-004 (complete): First interaction contains no AI notice). Evidence: `EXT-EVIDENCE-REC-004`, `FACT-AI-004`, `POLCTL-POL-T1`, `REC-004`.
- `IMP-AI-006-POL-T3`: SYSTEMS records a text-generation tool used by staff (exposed group staff). Control evidenced by REC-007: Tool is restricted to staff workspace. Evidence: `EXT-EVIDENCE-REC-007`, `FACT-AI-006`, `POLCTL-POL-T3`, `REC-007`.

### 2.2 Supported no-impact (by system)

- **AI-001** — No impact on recorded facts for L-50-1, L-50-2, L-50-3, L-50-4-DF, L-50-4-TXT, POL-T2-PROV, POL-T2-LABEL, POL-T3 (draft; Legal confirms). Rows: `IMP-AI-001-L-50-1`, `IMP-AI-001-L-50-2`, `IMP-AI-001-L-50-3`, `IMP-AI-001-L-50-4-DF`, `IMP-AI-001-L-50-4-TXT`, `IMP-AI-001-POL-T2-PROV`, `IMP-AI-001-POL-T2-LABEL`, `IMP-AI-001-POL-T3`.
- **AI-002** — No impact on recorded facts for L-50-1, L-50-2, L-50-3, L-50-4-DF, L-50-4-TXT, POL-T1, POL-T2-PROV, POL-T2-LABEL (draft; Legal confirms). Rows: `IMP-AI-002-L-50-1`, `IMP-AI-002-L-50-2`, `IMP-AI-002-L-50-3`, `IMP-AI-002-L-50-4-DF`, `IMP-AI-002-L-50-4-TXT`, `IMP-AI-002-POL-T1`, `IMP-AI-002-POL-T2-PROV`, `IMP-AI-002-POL-T2-LABEL`.
- **AI-003** — No impact on recorded facts for L-50-1, L-50-2, L-50-3, L-50-4-DF, L-50-4-TXT, POL-T1, POL-T3 (draft; Legal confirms). Rows: `IMP-AI-003-L-50-1`, `IMP-AI-003-L-50-2`, `IMP-AI-003-L-50-3`, `IMP-AI-003-L-50-4-DF`, `IMP-AI-003-L-50-4-TXT`, `IMP-AI-003-POL-T1`, `IMP-AI-003-POL-T3`.
- **AI-004** — No impact on recorded facts for L-50-1, L-50-2, L-50-3, L-50-4-DF, L-50-4-TXT, POL-T2-PROV, POL-T2-LABEL, POL-T3 (draft; Legal confirms). Rows: `IMP-AI-004-L-50-1`, `IMP-AI-004-L-50-2`, `IMP-AI-004-L-50-3`, `IMP-AI-004-L-50-4-DF`, `IMP-AI-004-L-50-4-TXT`, `IMP-AI-004-POL-T2-PROV`, `IMP-AI-004-POL-T2-LABEL`, `IMP-AI-004-POL-T3`.
- **AI-006** — No impact on recorded facts for L-50-1, L-50-2, L-50-3, L-50-4-DF, L-50-4-TXT, POL-T1, POL-T2-PROV, POL-T2-LABEL (draft; Legal confirms). Rows: `IMP-AI-006-L-50-1`, `IMP-AI-006-L-50-2`, `IMP-AI-006-L-50-3`, `IMP-AI-006-L-50-4-DF`, `IMP-AI-006-L-50-4-TXT`, `IMP-AI-006-POL-T1`, `IMP-AI-006-POL-T2-PROV`, `IMP-AI-006-POL-T2-LABEL`.
- **AI-007** — No impact on recorded facts for L-50-1, L-50-2, L-50-3, L-50-4-DF, L-50-4-TXT, POL-T2-PROV, POL-T2-LABEL, POL-T3 (draft; Legal confirms). Rows: `IMP-AI-007-L-50-1`, `IMP-AI-007-L-50-2`, `IMP-AI-007-L-50-3`, `IMP-AI-007-L-50-4-DF`, `IMP-AI-007-L-50-4-TXT`, `IMP-AI-007-POL-T2-PROV`, `IMP-AI-007-POL-T2-LABEL`, `IMP-AI-007-POL-T3`.
- **AI-008** — No impact on recorded facts for L-50-1, L-50-2, L-50-3, L-50-4-TXT, POL-T1, POL-T3 (draft; Legal confirms). Rows: `IMP-AI-008-L-50-1`, `IMP-AI-008-L-50-2`, `IMP-AI-008-L-50-3`, `IMP-AI-008-L-50-4-TXT`, `IMP-AI-008-POL-T1`, `IMP-AI-008-POL-T3`.

## 3. Conflicts and unresolved scope

### 3.1 Conflicting evidence (both facts preserved; decision D-001)

- `CONF-REC-003` (AI-003, owner **Communications**): Conflicting evidence for AI-003: Visible label exists but exported platform copy may have lost metadata (evidence reference social-post-884). Both facts are preserved; the automation does not decide which is true. Resolution need: System owner (Communications) verifies the contested fact using social-post-884 and updates EVIDENCE/SYSTEMS. Register rows: `IMP-AI-003-POL-T2-PROV`, `IMP-AI-003-POL-T2-LABEL`.
- `CONF-REC-008` (AI-007, owner **Marketing**): Conflicting evidence for AI-007: Owner says a banner exists but the current capture shows none (evidence reference avatar-page-capture). Both facts are preserved; the automation does not decide which is true. Resolution need: System owner (Marketing) verifies the contested fact using avatar-page-capture and updates EVIDENCE/SYSTEMS. Register rows: `IMP-AI-007-POL-T1`. Note: Interview 2 (line 148) described this item as unresolved pending owner verification; it remains unresolved in that sense, with state 'conflicting' (D-001).

### 3.2 Unresolved items

| Impact ID | System | Rule | Owner | Why unresolved | Resolution need |
|---|---|---|---|---|---|
| `IMP-AI-002-POL-T3` | AI-002 | POL-T3 | Admissions | SYSTEMS records a text-generation tool used by staff (exposed group applicants). Worst evidence state recorded for AI-002 is 'missing' (D-004): REC-002 (missing): No evidence that recipients are told when generated text is used. | Admissions supplies current, complete evidence. |
| `IMP-AI-005-L-50-1` | AI-005 | L-50-1 | Assessment Operations | Register facts for AI-005 are stale (evidence_updated_at 2026-04-15); no conclusion is drawn from stale facts. | Assessment Operations refreshes the register entry and evidence. |
| `IMP-AI-005-L-50-2` | AI-005 | L-50-2 | Assessment Operations | Register facts for AI-005 are stale (evidence_updated_at 2026-04-15); no conclusion is drawn from stale facts. | Assessment Operations refreshes the register entry and evidence. |
| `IMP-AI-005-L-50-3` | AI-005 | L-50-3 | Assessment Operations | Register facts for AI-005 are stale (evidence_updated_at 2026-04-15); no conclusion is drawn from stale facts. | Assessment Operations refreshes the register entry and evidence. |
| `IMP-AI-005-L-50-4-DF` | AI-005 | L-50-4-DF | Assessment Operations | Register facts for AI-005 are stale (evidence_updated_at 2026-04-15); no conclusion is drawn from stale facts. | Assessment Operations refreshes the register entry and evidence. |
| `IMP-AI-005-L-50-4-TXT` | AI-005 | L-50-4-TXT | Assessment Operations | Register facts for AI-005 are stale (evidence_updated_at 2026-04-15); no conclusion is drawn from stale facts. | Assessment Operations refreshes the register entry and evidence. |
| `IMP-AI-005-POL-T1` | AI-005 | POL-T1 | Assessment Operations | Register facts for AI-005 are stale (evidence_updated_at 2026-04-15); no conclusion is drawn from stale facts. | Assessment Operations refreshes the register entry and evidence. |
| `IMP-AI-005-POL-T2-PROV` | AI-005 | POL-T2-PROV | Assessment Operations | Register facts for AI-005 are stale (evidence_updated_at 2026-04-15); no conclusion is drawn from stale facts. | Assessment Operations refreshes the register entry and evidence. |
| `IMP-AI-005-POL-T2-LABEL` | AI-005 | POL-T2-LABEL | Assessment Operations | Register facts for AI-005 are stale (evidence_updated_at 2026-04-15); no conclusion is drawn from stale facts. | Assessment Operations refreshes the register entry and evidence. |
| `IMP-AI-005-POL-T3` | AI-005 | POL-T3 | Assessment Operations | Register facts for AI-005 are stale (evidence_updated_at 2026-04-15); no conclusion is drawn from stale facts. | Assessment Operations refreshes the register entry and evidence. |
| `IMP-AI-008-L-50-4-DF` | AI-008 | L-50-4-DF | Communications | POLICY records that the content shows real people, could be mistaken for an authentic recording and is not an evidently artistic or fictional work. Worst evidence state recorded for AI-008 is 'missing' (D-004): REC-009 (partial): Visible label verified but machine-readable provenance not checked; REC-010 (missing): No Legal approval or expiry date recorded. | Communications supplies current, complete evidence; Legal decides the exception request. |
| `IMP-AI-008-POL-T2-PROV` | AI-008 | POL-T2-PROV | Communications | SYSTEMS records public synthetic media (synthetic_audio_video, exposed_group=public). Worst evidence state recorded for AI-008 is 'missing' (D-004): REC-009 (partial): Visible label verified but machine-readable provenance not checked; REC-010 (missing): No Legal approval or expiry date recorded. | Communications supplies current, complete evidence; Legal decides the exception request. |
| `IMP-AI-008-POL-T2-LABEL` | AI-008 | POL-T2-LABEL | Communications | SYSTEMS records public synthetic media (synthetic_audio_video, exposed_group=public). Worst evidence state recorded for AI-008 is 'missing' (D-004): REC-009 (partial): Visible label verified but machine-readable provenance not checked; REC-010 (missing): No Legal approval or expiry date recorded. | Communications supplies current, complete evidence; Legal decides the exception request. |

### 3.3 Evidence gaps and authority blockers

- `GAP-REC-002` (owner Admissions): REC-002 for AI-002 is missing: No evidence that recipients are told when generated text is used. Resolution: Admissions supplies current, complete evidence for applicant-email-sample.
- `GAP-REC-005` (owner Assessment Operations): REC-005 for AI-005 is stale: Provider role questionnaire predates the current release. Resolution: Assessment Operations supplies current, complete evidence for provider-role-questionnaire.
- `GAP-REC-009` (owner Communications): REC-009 for AI-008 is partial: Visible label verified but machine-readable provenance not checked. Resolution: Communications supplies current, complete evidence for localisation-export-test.
- `GAP-REC-010` (owner Communications): REC-010 for AI-008 is missing: No Legal approval or expiry date recorded. Resolution: Communications supplies current, complete evidence for exception-draft-008. Legal approval and expiry date are also required for the exception request.
- `GAP-AI-002-CURRENT_NOTICE` (owner Admissions): AI-002 SYSTEMS field current_notice is 'unknown'. Resolution: Admissions supplies the current_notice fact.
- `GAP-AI-005-PROVIDER_ROLE` (owner Assessment Operations): AI-005 SYSTEMS field provider_role is 'unknown'. Resolution: Assessment Operations supplies the provider_role fact.
- `GAP-AI-005-REGISTER-STALE` (owner Assessment Operations): AI-005 register facts are stale (evidence_updated_at 2026-04-15); all rows for this system stay unresolved. Resolution: Assessment Operations refreshes the register entry and supporting evidence.

## 4. Proposed actions and dates

Dates are Operations-proposed dates taken from CALENDAR; the automation does not set or change deadlines (decision D-005). All are proposals with approval **pending**.

| Action ID | System | Action | Owner (responsible role) | Proposed date | Origin | Approval | Linked impacts |
|---|---|---|---|---|---|---|---|
| `ACT-001` | AI-004 | Add and verify first-interaction AI notice | Learning Experience | 2026-09-04 | calendar-linked | pending (Operations) | `IMP-AI-004-POL-T1` |
| `ACT-002` | AI-007 | Resolve disclosure evidence conflict | Marketing | 2026-09-03 | calendar-linked | pending (Operations) | `IMP-AI-007-POL-T1` |
| `ACT-003` | AI-002 | Confirm recipient disclosure practice | Admissions | 2026-09-08 | calendar-linked | pending (Legal) | `IMP-AI-002-POL-T3` |
| `ACT-004` | AI-003 | Verify machine-readable provenance after publishing | Communications | 2026-09-10 | calendar-linked | pending (Operations) | `IMP-AI-003-POL-T2-PROV`, `IMP-AI-003-POL-T2-LABEL` |
| `ACT-005` | AI-005 | Refresh provider-role and release evidence | Assessment Operations | 2026-09-12 | calendar-linked | pending (Legal) | `IMP-AI-005-L-50-1`, `IMP-AI-005-L-50-2`, `IMP-AI-005-L-50-3`, `IMP-AI-005-L-50-4-DF`, `IMP-AI-005-L-50-4-TXT`, `IMP-AI-005-POL-T1`, `IMP-AI-005-POL-T2-PROV`, `IMP-AI-005-POL-T2-LABEL`, `IMP-AI-005-POL-T3` |
| `ACT-006` | AI-008 | Complete provenance test | Communications | 2026-09-09 | calendar-linked | pending (Operations) | `IMP-AI-008-POL-T2-PROV` |
| `ACT-007` | AI-008 | Review exception request | Legal | 2026-09-15 | calendar-linked | pending (Legal) | `IMP-AI-008-L-50-4-DF`, `IMP-AI-008-POL-T2-LABEL` |
| `ACT-008` | ALL | Quarterly AI register evidence review | Operations | 2026-10-02 | calendar-carried-forward | pending (Operations) | — |

Calendar: 8 tentative event(s) in `action-calendar.ics` (ACT-001, ACT-002, ACT-003, ACT-004, ACT-005, ACT-006, ACT-007, ACT-008).

## 5. Decisions requested from Legal and Operations

These review requests are **prepared, not sent**. No reply has been received or simulated.

| Request ID | Required reviewer | Subject | Question | Evidence |
|---|---|---|---|---|
| `RR-A50` | Legal | 40 register rows | Do you confirm, correct or reject each draft Article 50 state and its reason, including the unresolved and withheld items? | `IMP-AI-001-L-50-1`, `IMP-AI-001-L-50-2`, `IMP-AI-001-L-50-3`, `IMP-AI-001-L-50-4-DF`, `IMP-AI-001-L-50-4-TXT`, `IMP-AI-002-L-50-1` … |
| `RR-POLICY` | Legal | 32 register rows | Do you confirm the draft policy-rule states, conflicts and resolution owners? | `IMP-AI-001-POL-T1`, `IMP-AI-001-POL-T2-LABEL`, `IMP-AI-001-POL-T2-PROV`, `IMP-AI-001-POL-T3`, `IMP-AI-002-POL-T1`, `IMP-AI-002-POL-T2-LABEL` … |
| `RR-ACT-001` | Operations | ACT-001 | Approve, reject or amend action 'Add and verify first-interaction AI notice' with owner Learning Experience and proposed date 2026-09-04? | `ACT-001`, `IMP-AI-004-POL-T1` |
| `RR-ACT-002` | Operations | ACT-002 | Approve, reject or amend action 'Resolve disclosure evidence conflict' with owner Marketing and proposed date 2026-09-03? | `ACT-002`, `IMP-AI-007-POL-T1` |
| `RR-ACT-003` | Legal | ACT-003 | Approve, reject or amend action 'Confirm recipient disclosure practice' with owner Admissions and proposed date 2026-09-08? | `ACT-003`, `IMP-AI-002-POL-T3` |
| `RR-ACT-004` | Operations | ACT-004 | Approve, reject or amend action 'Verify machine-readable provenance after publishing' with owner Communications and proposed date 2026-09-10? | `ACT-004`, `IMP-AI-003-POL-T2-LABEL`, `IMP-AI-003-POL-T2-PROV` |
| `RR-ACT-005` | Legal | ACT-005 | Approve, reject or amend action 'Refresh provider-role and release evidence' with owner Assessment Operations and proposed date 2026-09-12? | `ACT-005`, `IMP-AI-005-L-50-1`, `IMP-AI-005-L-50-2`, `IMP-AI-005-L-50-3`, `IMP-AI-005-L-50-4-DF`, `IMP-AI-005-L-50-4-TXT` … |
| `RR-ACT-006` | Operations | ACT-006 | Approve, reject or amend action 'Complete provenance test' with owner Communications and proposed date 2026-09-09? | `ACT-006`, `IMP-AI-008-POL-T2-PROV` |
| `RR-ACT-007` | Legal | ACT-007 | Approve, reject or amend action 'Review exception request' with owner Legal and proposed date 2026-09-15? | `ACT-007`, `IMP-AI-008-L-50-4-DF`, `IMP-AI-008-POL-T2-LABEL` |
| `RR-ACT-008` | Operations | ACT-008 | Approve, reject or amend action 'Quarterly AI register evidence review' with owner Operations and proposed date 2026-10-02? | `ACT-008` |

Run `RCIB-20261006T195819Z-3013`; source versions for each request are recorded in `deliverables/snapshots/06-actions-and-approvals.json` (`state.review_requests[].source_versions`).

Escalations to resolution owners (system owners resolve factual behaviour; Legal owns interpretation and exceptions; Operations owns activation and dates):

- **Admissions**: `IMP-AI-002-POL-T3`
- **Assessment Operations**: `IMP-AI-005-L-50-1`, `IMP-AI-005-L-50-2`, `IMP-AI-005-L-50-3`, `IMP-AI-005-L-50-4-DF`, `IMP-AI-005-L-50-4-TXT`, `IMP-AI-005-POL-T1`, `IMP-AI-005-POL-T2-PROV`, `IMP-AI-005-POL-T2-LABEL`, `IMP-AI-005-POL-T3`
- **Communications**: `IMP-AI-003-POL-T2-PROV`, `IMP-AI-003-POL-T2-LABEL`, `IMP-AI-008-L-50-4-DF`, `IMP-AI-008-POL-T2-PROV`, `IMP-AI-008-POL-T2-LABEL`
- **Marketing**: `IMP-AI-007-POL-T1`

## 6. Project decisions applied

- **D-001** — Keep REC-008 (and REC-003) in the conflicting state, owned by the system owner, instead of reclassifying it as unresolved. (Project developer (independent decision; no stakeholder or facilitator approval))
- **D-002** — Define the run states: blocked if any required source fails, partial if record-level gaps remain, complete if everything is supported, failed on a technical fault. Map them to stage 07 publication status. (Project developer (independent decision; no stakeholder or facilitator approval))
- **D-003** — Read the ten interview-disclosed URLs live and read-only, using existing share-link permissions. No credentials, no local substitutes; Google Sheets via one-tab-verified CSV export, Notion via an isolated page-chunk adapter. (Project developer (independent decision; no stakeholder or facilitator approval))
- **D-004** — Derive impact states from a declared rule catalogue (Article 50 paragraphs and POLICY transparency rules), applied to live structured SYSTEMS fields, POLICY per-system statements and EVIDENCE record states, and never emit compliant or non-compliant findings. (Implementation decision (Claude), awaiting project developer review)
- **D-005** — Propose actions from findings, linking them to existing CALENDAR actions to avoid duplication. Take dates only from CALENDAR (Operations' proposals); new actions stay undated, are omitted from the ICS and are explained. (Implementation decision (Claude), awaiting project developer review)
- **D-006** — Every approval is 'pending', because no source records an approval outcome. The required approver comes from CALENDAR approval_required (actions) or Legal (applicability interpretation). Reviewer responses are applied only from a supplied verified file whose binding validates. (Implementation decision (Claude), awaiting project developer review)
- **D-007** — Represent the as-of date as end of the Dublin business day on 26 Aug 2026. Accept legitimately newer source revisions while recording them separately, and judge legal versions against the review date. (Implementation decision (Claude), awaiting project developer review)
- **D-008** — Keep every retrieved response's exact bytes (gzip-compressed) plus claim-bearing extracts with locators. Hash the original uncompressed bytes. (Implementation decision (Claude), awaiting project developer review)

Full decision records: `regulatory-change-impact-brief/references/decisions.md` and each snapshot's `decisions`.

## Appendix A. Full impact index

| Impact ID | State | Basis | Applicability | Owner |
|---|---|---|---|---|
| `IMP-AI-001-L-50-1` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learner Operations |
| `IMP-AI-001-L-50-2` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learner Operations |
| `IMP-AI-001-L-50-3` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learner Operations |
| `IMP-AI-001-L-50-4-DF` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learner Operations |
| `IMP-AI-001-L-50-4-TXT` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learner Operations |
| `IMP-AI-001-POL-T1` | supported-impact | internal-policy | applies-on-recorded-facts | Learner Operations |
| `IMP-AI-001-POL-T2-PROV` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Learner Operations |
| `IMP-AI-001-POL-T2-LABEL` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Learner Operations |
| `IMP-AI-001-POL-T3` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Learner Operations |
| `IMP-AI-002-L-50-1` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Admissions |
| `IMP-AI-002-L-50-2` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Admissions |
| `IMP-AI-002-L-50-3` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Admissions |
| `IMP-AI-002-L-50-4-DF` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Admissions |
| `IMP-AI-002-L-50-4-TXT` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Admissions |
| `IMP-AI-002-POL-T1` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Admissions |
| `IMP-AI-002-POL-T2-PROV` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Admissions |
| `IMP-AI-002-POL-T2-LABEL` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Admissions |
| `IMP-AI-002-POL-T3` | unresolved | internal-policy | applies-on-recorded-facts | Admissions |
| `IMP-AI-003-L-50-1` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-003-L-50-2` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-003-L-50-3` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-003-L-50-4-DF` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-003-L-50-4-TXT` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-003-POL-T1` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-003-POL-T2-PROV` | conflicting | internal-policy | applies-on-recorded-facts | Communications |
| `IMP-AI-003-POL-T2-LABEL` | conflicting | internal-policy | applies-on-recorded-facts | Communications |
| `IMP-AI-003-POL-T3` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-004-L-50-1` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learning Experience |
| `IMP-AI-004-L-50-2` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learning Experience |
| `IMP-AI-004-L-50-3` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learning Experience |
| `IMP-AI-004-L-50-4-DF` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learning Experience |
| `IMP-AI-004-L-50-4-TXT` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Learning Experience |
| `IMP-AI-004-POL-T1` | supported-impact | internal-policy | applies-on-recorded-facts | Learning Experience |
| `IMP-AI-004-POL-T2-PROV` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Learning Experience |
| `IMP-AI-004-POL-T2-LABEL` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Learning Experience |
| `IMP-AI-004-POL-T3` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Learning Experience |
| `IMP-AI-005-L-50-1` | unresolved | binding-law | unknown | Assessment Operations |
| `IMP-AI-005-L-50-2` | unresolved | binding-law | unknown | Assessment Operations |
| `IMP-AI-005-L-50-3` | unresolved | binding-law | unknown | Assessment Operations |
| `IMP-AI-005-L-50-4-DF` | unresolved | binding-law | unknown | Assessment Operations |
| `IMP-AI-005-L-50-4-TXT` | unresolved | binding-law | unknown | Assessment Operations |
| `IMP-AI-005-POL-T1` | unresolved | internal-policy | unknown | Assessment Operations |
| `IMP-AI-005-POL-T2-PROV` | unresolved | internal-policy | unknown | Assessment Operations |
| `IMP-AI-005-POL-T2-LABEL` | unresolved | internal-policy | unknown | Assessment Operations |
| `IMP-AI-005-POL-T3` | unresolved | internal-policy | unknown | Assessment Operations |
| `IMP-AI-006-L-50-1` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | People Operations |
| `IMP-AI-006-L-50-2` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | People Operations |
| `IMP-AI-006-L-50-3` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | People Operations |
| `IMP-AI-006-L-50-4-DF` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | People Operations |
| `IMP-AI-006-L-50-4-TXT` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | People Operations |
| `IMP-AI-006-POL-T1` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | People Operations |
| `IMP-AI-006-POL-T2-PROV` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | People Operations |
| `IMP-AI-006-POL-T2-LABEL` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | People Operations |
| `IMP-AI-006-POL-T3` | supported-impact | internal-policy | applies-on-recorded-facts | People Operations |
| `IMP-AI-007-L-50-1` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Marketing |
| `IMP-AI-007-L-50-2` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Marketing |
| `IMP-AI-007-L-50-3` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Marketing |
| `IMP-AI-007-L-50-4-DF` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Marketing |
| `IMP-AI-007-L-50-4-TXT` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Marketing |
| `IMP-AI-007-POL-T1` | conflicting | internal-policy | applies-on-recorded-facts | Marketing |
| `IMP-AI-007-POL-T2-PROV` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Marketing |
| `IMP-AI-007-POL-T2-LABEL` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Marketing |
| `IMP-AI-007-POL-T3` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Marketing |
| `IMP-AI-008-L-50-1` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-008-L-50-2` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-008-L-50-3` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-008-L-50-4-DF` | unresolved | binding-law | applies-on-recorded-facts | Communications |
| `IMP-AI-008-L-50-4-TXT` | supported-no-impact | binding-law | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-008-POL-T1` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Communications |
| `IMP-AI-008-POL-T2-PROV` | unresolved | internal-policy | applies-on-recorded-facts | Communications |
| `IMP-AI-008-POL-T2-LABEL` | unresolved | internal-policy | applies-on-recorded-facts | Communications |
| `IMP-AI-008-POL-T3` | supported-no-impact | internal-policy | not-applicable-on-recorded-facts | Communications |

## Appendix B. Evidence references

Evidence IDs (`EXT-…`) resolve to `deliverables/sources/<SOURCE>.extracts.json`; attempt IDs (`ATT-…`) to `deliverables/snapshots/02-source-capture.json`; `REC-…`, `FACT-…`, `CONF-…`, `GAP-…`, `POLCTL-…` to `04-evidence-reconciliation.json`; `RULE-…`, `TIME-…`, `BLK-…` to `03-authority-and-timing.json`.

