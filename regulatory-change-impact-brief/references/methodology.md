# Methodology and automation choices

This explains how the skill turns the ten live sources into the draft package, and the trade-offs of each choice.
The binding decision records, with their options and source basis, are in [decisions.md](decisions.md).

## Pipeline and snapshot boundaries

| Stage | Snapshot | What happens | Main records |
|---|---|---|---|
| 01 scope | `01-scope.json` | Fixed as-of date (26 Aug 2026), the 8 systems, audiences and approval gates, the disclosed routes, supersession and change reason, and an inspection of the prior run | `SCOPE-*`, `ROUTE-*`, project evidence (`INT*`, `ASSIGN-*`, `INSPECT-*`), decisions |
| 02 source-capture | `02-source-capture.json` | Live read-only attempts for all 10 sources. Each attempt records its locator, actual retrieval time, status, content type, version metadata, hash, preserved bytes and suitability checks. Extracts are kept with locators | `ATT-*`, `SRC-*`, `EXT-*` |
| 03 authority-and-timing | `03-authority-and-timing.json` | Article 50 paragraphs are taken from CONSOLIDATED and reconciled against OJ and AMEND, followed by the application dates, transitions and advisory context. Any blockers are recorded here | `RULE-*`, `TIME-*`, `GUIDE-*`, `CTX-*`, `BLK-*` |
| 04 evidence-reconciliation | `04-evidence-reconciliation.json` | System facts (SYSTEMS plus POLICY statements), policy controls, evidence records, conflicts and gaps | `FACT-*`, `POLCTL-*`, `REC-*`, `CONF-*`, `GAP-*` |
| 05 impact-analysis | `05-impact-analysis.json` | One draft state per system × rule (8 × 9 = 72) | `IMP-*`, `UNAFF-*`, `CONFLICT-*`, `UNRES-*` |
| 06 actions-and-approvals | `06-actions-and-approvals.json` | Actions linked to CALENDAR or newly proposed, pending approvals, escalations and prepared review requests | `ACT-*`/`PA-*`, `APR-*`, `ESC-*`, `RR-*` |
| 07 publication-validation | `07-publication-validation.json` | Written after the three drafts. It records the final file paths and hashes, schema and chain checks, evidence integrity, cross-file agreement and the detached review-request bindings | `ART-*`, `CHK-*`, `BIND-*`, `OPEN-*` |

All seven snapshots share one `run_id`. From stage 02 on, `predecessor` carries the previous snapshot's ID, path and
SHA-256. `consumed_record_ids` always resolve to records in earlier snapshots, and `produced_record_ids` lists every
record present in the stage. After stage 07, the pipeline re-inspects the actual bundle and writes
`deliverables/run-verification.json`.

## Impact states (decision D-004, rule-level evidence)

Each EVIDENCE record is attributed only to the rules whose **evidence subjects** its own `evidence_ref` and `notes`
name. The subjects are interaction-notice, provenance-marking, visible-label-disclosure (including exception
requests), text-output-route, provider-role and emotion-biometric; each rule lists its subjects in
`references/rules.json`. Stage 04 shows each record's attribution. A record that names no subject is unattributed
context and affects no row. The SYSTEMS `evidence_status` summary is not propagated to rows.

- **supported-impact:** recorded facts meet the rule's applicability conditions, and every record attributed to that
  rule is complete. The control is described as evidenced, or as a recorded gap such as `current_notice=no`. It is
  never labelled compliant or non-compliant.
- **supported-no-impact:** recorded facts show the rule's conditions are not met. For example, a provider-side duty
  where SYSTEMS records `provider_role=no` and POLICY records a licensed supplier product. For binding-law rows this is
  a draft reading for Legal; see the brief's Legal-review boundary section.
- **conflicting:** the rule applies, and a record attributed to that rule is `conflicting` (REC-003, REC-008). Both
  facts are preserved and the system owner resolves the conflict (D-001).
- **unresolved:** a needed fact is unknown or its POLICY statement absent; the system's register facts are stale; no
  record addresses the rule's control; an attributed record is missing, stale or partial; or the run is blocked.

The two rule bases stay separately identifiable in `rule_ref`, `rule_id` and `rule_basis`.

*Trade-offs:*
- A record that names two subjects (REC-003, REC-009) applies its single state to both rules, and this is disclosed in
  the reason.
- Stale register facts (AI-005) still affect every row for that system, because the stale facts are the applicability
  inputs.

## Run states and blocking (decision D-002)

| Condition | Run status | Stage 07 `publication_status` | Calendar |
|---|---|---|---|
| Any of the 10 required sources is unavailable, invalid or stale, or the binding text is unreconciled | blocked | blocked | empty |
| All sources retrieved and verified; some rows conflicting or unresolved | partial | validated (draft validation only) | dated proposals |
| All sources retrieved and verified; every row supported | complete | validated | dated proposals |
| A technical or validation failure | failed | failed | as written; recorded in failures |

In a blocked run, every binding-law row is `unresolved` with applicability `withheld`. Internal-policy rows are still
evaluated when POLICY, SYSTEMS and EVIDENCE are usable. This is factual reconciliation, clearly labelled under the
BLOCKED banner.

Suitability is decided by observable checks recorded in stage 02:
- final host and content type
- title or identifier
- Article 50 anchor and text
- tab list and required columns
- unique IDs
- Notion page identity, policy version and context revision
- the consolidated version date on or before the review date, and matching the requested CELEX version
- the amendment in force by the review date

A failed identity check makes a source `invalid`. Failed version checks alone make it `stale`.

## Actions, dates and calendar (decision D-005)

A finding that needs action is linked to a CALENDAR action for the same system: first by the rule's declared action
cues, otherwise when it is that system's only action. A linked action keeps its CALENDAR owner, Operations-proposed
date, status and required approver. A finding with no linkable action gets an undated `PA-<system>-<rule>` proposal
owned by the system owner. Unlinked CALENDAR actions are carried forward so that no work is lost.

The ICS holds only dated actions. Each is an all-day `VALUE=DATE` event with an exclusive `DTEND`, marked
`STATUS:TENTATIVE`, with a stable UID `<action-id>@regulatory-change-impact-brief.quillhaven`. Undated actions are
listed in the register (`reason`) and the brief.

## Approvals and reviews (decision D-006)

Every approval is `pending`, because no source records an approval outcome. Review requests (`RR-A50`, `RR-POLICY`,
one per action) are prepared but never sent. Stage 07 binds each request to the exact paths and hashes of the three
final drafts. A reviewer response is applied only when its request ID, reviewer role, run ID and artifact hash match an
archived binding. Unmatched responses stay unresolved in stage 06.

## Changed inputs

- Sheets are parsed by header name, so reordered rows and columns work, and extra columns are recorded and ignored.
- Missing or renamed required columns, duplicate column headers and duplicate or blank IDs make the source `invalid`,
  which blocks the run. Renamed fields are never guessed.
- Values outside the disclosed meanings, or malformed dates, are reported as `GAP-…-INVALID`. The affected rows become
  `unresolved`.
- Newer in-source version labels are accepted and listed under `versions_after_review_date`. The review date never
  changes.

## History and recovery

Before a run writes anything, any existing bundle is inspected with the full verifier and moved to
`deliverables/history/<old-run-id>/`. A `history-manifest.json` there records what was found, including missing or
damaged files; nothing is repaired. Each run gets a new run ID and new snapshot IDs.

Stage 01 records `supersedes_run_id` and the reason. Stage 02 compares claim-bearing extracts with the superseded run.
Raw EUR-Lex and Notion bytes embed per-request tokens, so they differ on every fetch. Every stage and draft is
recomputed from the fresh captures.

**Redaction (D-008).** Saved POLICY page chunks omit Notion's workspace member table (third-party names, user IDs and profile-photo links). The attempt records the removed table, its record count and the original response hash. The verifier proves that the saved bytes still reproduce every POLICY extract and its identity, version and dates.

Runs archived before that change were redacted after the fact with `scripts/redact_history_notion_users.py`. It removes the same table only and documents each change in that run's `history-manifest.json` (`post_run_redactions`): the reason, the original and redacted hashes, and a notice that the current file intentionally differs from the run's stage 02 hash. The verifier requires every such difference to be documented (`CHK-HISTORY-*`).

**Redirect URLs.** When a request is redirected to another host (Google Sheets exports go to a signed, time-limited `*.googleusercontent.com` link that embeds an access signature, expiry and the owner's account ID), stage 02 records only that host in `final_url`. The requested locator, content hash and preserved bytes are unaffected. Archived stage 02 snapshots were redacted the same way with `scripts/redact_history_signed_urls.py` and documented in their manifests. Each run's stage 03 `predecessor` hash still identifies the original stage 02 bytes, and the verifier requires that difference to be documented.

Technical failures are written to `deliverables/failures/<run-id>.json` with the affected stage and the recovery
action. Re-running the documented command is the repair path.
