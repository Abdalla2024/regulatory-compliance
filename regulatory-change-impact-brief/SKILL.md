---
name: regulatory-change-impact-brief
description: Prepare Quillhaven Academy's read-only, evidence-backed EU AI Act Article 50 impact review package (impact register CSV, compliance brief, tentative action calendar, seven-stage snapshot chain) for Legal and Operations, as of 26 August 2026. Use when asked to run, re-run, repair or verify the Article 50 regulatory change impact review or brief.
---

# Regulatory change impact brief (EU AI Act Article 50)

Produces a **review-ready draft** for Legal and Operations. It never gives legal advice, approves anything, activates
policy, changes deadlines, closes incidents, sends responses, or writes to any source or production calendar.

## Run it

From the repository root (Python 3.11+; one-time setup in the repository README):

```bash
.venv/bin/python regulatory-change-impact-brief/scripts/run_review.py
```

- Every run reads all ten interview-disclosed sources live (`references/source-routes.json`). No credentials are
  used or accepted, and no local copy is ever substituted for a failed read.
- Exit codes: `0` means a partial or complete draft was validated; `3` means a blocked package was produced with
  conclusions withheld; `1` means failed (see `deliverables/failures/` and `deliverables/run-verification.json`).
- `--verify` inspects the current bundle read-only (seven snapshots, hash chain, source evidence, the three drafts and
  the review bindings), and exits `1` if anything is missing, damaged or stale.
- `--reason "<text>"` records the change or retry reason in stage 01.
- `--responses <file>` applies reviewer responses supplied through the facilitator's verified channel. A response is
  applied only if it binds to an archived draft hash; anything that does not match stays unresolved.

## What to tell the user afterwards

Report the run ID, the run status and what it means, any source that was not `retrieved`, and the counts of
conflicting and unresolved rows with their owners. Point to `deliverables/compliance-brief.md`. Never describe a
`blocked` or `partial` run as complete, and never describe a prepared review request as sent.

## When something fails

- **A source is `unavailable`, `invalid` or `stale`:** the run is blocked by design (decision D-002). Report which
  source and why (stage 02 `suitability_checks`). Do not substitute data. Re-run once the source is restored.
- **Verification failed or outputs are damaged:** run the command again. It archives the damaged bundle to
  `deliverables/history/<run-id>/` with an integrity manifest, then makes fresh source attempts.
- **The Notion adapter stops working** (undocumented endpoint): update `capture_notion` in `scripts/rcib/sources.py`
  only. See decision D-003.

## Files

- `scripts/run_review.py` is the entry point. `scripts/rcib/` holds the stage modules: `sources` (stage 02),
  `analysis` (stages 03–06), `outputs` (the three drafts), `validate` (schema, chain and cross-file checks), and
  `pipeline` (orchestration, history, stage 07).
- `references/source-routes.json` holds the disclosed routes and the identity, version and structure expectations.
- `references/scope.json` holds the as-of date, systems in scope, audiences and approval gates.
- `references/rules.json` holds the Article 50 and POLICY rule catalogue and the fact cues (decision D-004).
- `references/decisions.json` is the canonical decision record. `references/decisions.md` is a view rendered from it
  by `scripts/render_decisions.py`.
- `references/methodology.md` explains how states, actions, blocking and recovery work, and their trade-offs.
- `scripts/redact_history_notion_users.py` was a one-off redaction of the Notion member table from runs archived before the D-008 revision; it is documented in each history manifest.
- `scripts/redact_history_signed_urls.py` was a one-off removal of signed redirect URLs from archived stage 02 snapshots; it is documented in each history manifest.
- `scripts/tests/` holds offline behaviour tests with synthetic fixtures (never used by a real run).
