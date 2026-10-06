# Project decision records

<!-- Generated from decisions.json by scripts/render_decisions.py; edit the JSON, then re-render. -->

> No stakeholder or facilitator has approved any of these decisions. D-001 to D-003 were made independently by the project developer. D-004 to D-008 are implementation decisions made while building the skill and are awaiting the developer's review.

## D-001 — Keep REC-008 (and REC-003) in the conflicting state, owned by the system owner, instead of reclassifying it as unresolved.

*Decided by:* Project developer (independent decision; no stakeholder or facilitator approval)  

**Concern.** The interviews describe REC-008 two ways. Interview 1 gives it as the example of conflicting evidence; interview 2 says it 'must be recorded in the impact register as unresolved and assigned to the owner'. The schema and register keep conflicting and unresolved as distinct impact states, so the item can only carry one.

**Options considered.**

1. Record REC-008 as unresolved, following interview 2's wording. — *Matches the latest interview phrasing but discards the source's own conflicting state and merges two states the assignment and POLICY keep distinct.*
2. Record REC-008 as conflicting, preserving both contradictory facts, with the owner assigned to resolve it. — *Matches EVIDENCE, SYSTEMS, POLICY's evidence-state list, interview 1 and the schema; still satisfies interview 2's requirement that it stay visible and be assigned to the owner.*
3. Record it as both (two register rows). — *Creates duplicate rows for one system/rule fact and makes counts and cross-file agreement ambiguous.*

**Source basis.**

- `INSPECT-EVIDENCE-REC-008` (EVIDENCE sheet (Incident Evidence Register), row record_id=REC-008, inspected 2026-10-06): REC-008 | AI-007 | incident | 2026-08-21 | Marketing | open | avatar-page-capture | conflicting | Owner says a banner exists but the current capture shows none.
- `INSPECT-SYSTEMS-AI-007` (SYSTEMS sheet (AI System Register), row system_id=AI-007, inspected 2026-10-06): AI-007 Website Guide Avatar, owner Marketing, current_notice=no, evidence_status=conflicting, record_version=register-2026-08-26.
- `INSPECT-POLICY-STATES` (POLICY Notion page, 'Evidence and exceptions' bullet 2, inspected 2026-10-06): missing, stale, conflicting, and not-applicable are different evidence states. Missing evidence must not be converted to compliance or non-compliance.
- `INSPECT-POLICY-AI-007` (POLICY Notion page, 'Actual use and content' > AI-007, inspected 2026-10-06): The owner/banner and current-capture conflict in REC-008 remains unresolved.
- `INT1-L150` (interviews/project-b-regulatory-compliance-20261006-1706.md line 150): Conflicting records occur when owner claims contradict captured evidence, like REC-008. Unresolved means expected facts are missing or stale.
- `INT2-L148` (interviews/project-b-regulatory-compliance-20261006-1750.md line 148): For REC-008 the system owner claims a notice banner exists but the current capture shows none; record it in the impact register as unresolved and assigned to the owner for verification.
- `INT2-L164` (interviews/project-b-regulatory-compliance-20261006-1750.md line 164): System owners resolve factual inconsistencies such as REC-008; Legal owns interpretation and exceptions; Operations manages activation and dates.
- `INT1-L118` (interviews/project-b-regulatory-compliance-20261006-1706.md line 118): Legal obligations from binding text take precedence; for factual conflicts in the records, keep both reports separate and ask the system owner to resolve them.
- `ASSIGN-STATES` (Project B assignment, 'Snapshots and captured sources', paragraph on schema states): Impact states are supported-impact / supported-no-impact / conflicting / unresolved; preserve unresolved or conflicting records with source basis, reason, known owner and resolution need.
- `INSPECT-EVIDENCE-REC-003` (EVIDENCE sheet, row record_id=REC-003, inspected 2026-10-06): REC-003 | AI-003 | incident | 2026-08-24 | Communications | open | social-post-884 | conflicting | Visible label exists but exported platform copy may have lost metadata.

**Chosen behaviour.** Impact rows whose outcome depends on REC-008 use state 'conflicting'. Owner: Marketing (the AI-007 system owner). Resolution need: the system owner verifies whether the disclosure banner exists, using the identified evidence reference avatar-page-capture. Both facts (the owner's claim that a banner exists; the current capture showing none) are preserved, and the automation does not decide which is true. The item appears in the brief's conflicts/unresolved scope section. The same rule applies to REC-003 (AI-003, owner Communications), which is also conflicting at source level: label reported present, exported platform copy may have lost metadata (evidence reference social-post-884).

**Interview interpretation preserved.** Interview 2's reading — that REC-008 is unresolved until the owner verifies it — is kept in the register 'reason' and the brief: the item is described as not yet resolved and pending owner verification. Only the state value differs: 'conflicting' rather than 'unresolved'.

**Rationale.** The underlying facts directly contradict each other, which is the defining case for 'conflicting' in interview 1, POLICY and the schema. Interview 2's two concerns — visibility, and assignment to the owner — are fully met. Using the source's own state avoids the automation overriding a recorded business fact.

**Trade-offs.**

- Departs from interview 2's literal wording; a reader comparing it with that transcript must see this record to understand why.
- Conflicting and unresolved items are counted separately in the brief, so 'unresolved' totals are lower than a reader of interview 2 might expect.

**Downstream effect.**

- Stage 04 records CONF-REC-008 and CONF-REC-003 as conflicts, citing both facts.
- Stage 05 impact rows for AI-007 and AI-003 that need control evidence carry state 'conflicting'.
- Stage 06 links the rows to the existing CALENDAR actions (ACT-002 for AI-007, ACT-004 for AI-003) with owners Marketing and Communications.
- The register, brief and stage 07 cross-file checks treat conflicting as distinct from unresolved.

*Recorded in snapshot stage(s):* evidence-reconciliation, impact-analysis

## D-002 — Define the run states: blocked if any required source fails, partial if record-level gaps remain, complete if everything is supported, failed on a technical fault. Map them to stage 07 publication status.

*Decided by:* Project developer (independent decision; no stakeholder or facilitator approval)  

**Concern.** The assignment leaves open whether unsupported inputs force whole-run deferral or permit useful unaffected work. The stakeholder said both 'we must pause until all required records are available' and 'I want useful unaffected work', and also defined partial as evaluating unaffected information. A rule is needed that produces consistent run, snapshot, register, brief and calendar states.

**Options considered.**

1. Abort and produce nothing when any source fails. — *Honours 'pause' literally but discards source attempts and evidence; contradicts the assignment's requirement to preserve a blocked/unresolved chain, register and brief.*
2. Treat only binding legal source failures as blocking; continue partially when company or guidance sources fail. — *Produces more output, but contradicts the stakeholder's explicit 'pause' for TIME, FAQ and company sources and risks the misleading completeness they warned about.*
3. Block on any required source failure while still emitting the evidence-preserving withheld-conclusions package; reserve partial for record-level gaps when every source was retrieved and verified. — *Matches the stakeholder's pause rule and concern about misleading completeness, and the assignment's requirement to preserve the blocked chain.*
4. Track which conclusion depends on which source and withhold only those. — *More output in a blocked run, but fragile: the Article 50 text, amendments and dates are spread across OJ, AMEND, CONSOLIDATED and LAW, and the stakeholder said the routes travel together.*

**Source basis.**

- `ASSIGN-BLOCK` (Project B assignment, 'Final drafts', paragraph after the table): When required legal authority is unavailable or unsuitable, withhold dependent formal conclusions and preserve a blocked/unresolved chain, register and brief with an empty or limited calendar. Explain whether other unsupported inputs require whole-run deferral or permit useful unaffected work, and keep that choice consistent across outputs.
- `ASSIGN-PUB` (Project B assignment, 'Final drafts', stage 07 paragraph): Stage 07 publication state describes draft validation, not human approval; do not label an unresolved authority blocker as normal validated publication.
- `INT1-L166` (interviews/project-b-regulatory-compliance-20261006-1706.md line 166): Stale or invalid sources block formal legal conclusions until current and binding evidence is obtained.
- `INT1-L182` (interviews/project-b-regulatory-compliance-20261006-1706.md line 182): The run is blocked when necessary binding evidence is unavailable or unsuitable, e.g. a required source locator fails or returns outdated text.
- `INT2-L52` (interviews/project-b-regulatory-compliance-20261006-1750.md line 52): LAW, OJ, AMEND and CONSOLIDATED are all required; the legislative routes travel together.
- `INT2-L69` (interviews/project-b-regulatory-compliance-20261006-1750.md lines 69 and 76): If TIME or FAQ is unavailable we must pause; the stakeholder wants useful unaffected work but worries a partial package will look complete.
- `INT2-L88` (interviews/project-b-regulatory-compliance-20261006-1750.md lines 88-92): Interviewer proposed marking affected items unresolved or blocked, explaining what is missing and who resolves it, and stating in the brief that the conclusion was withheld; the stakeholder responded that this protects Legal and Operations from assumptions.
- `INT2-L116` (interviews/project-b-regulatory-compliance-20261006-1750.md line 116): If a company source is unavailable, pause until all required records are available; every scoped system needs its actual evidence and owner.
- `INT2-L124` (interviews/project-b-regulatory-compliance-20261006-1750.md line 124): A blocked run pauses the entire review until required sources are restored; a partial run might evaluate available unaffected information while keeping unresolved items marked with missing facts and ownership.
- `INT2-L100` (interviews/project-b-regulatory-compliance-20261006-1750.md line 100): The authoritative version is the binding text effective for 26 August 2026, reconciled against the Official Journal acts and applicable amendments, with Legal confirming.
- `INT1-L276` (interviews/project-b-regulatory-compliance-20261006-1706.md line 276): Retrieval time, source revision and business-effective date are separate.

**Chosen behaviour.** All ten sources are required runtime retrievals, classified by authority: binding legal (OJ, AMEND, CONSOLIDATED); official advisory or interpretive (LAW, TIME, FAQ); company (POLICY, SYSTEMS, EVIDENCE, CALENDAR). Run states: 'blocked' when any required source is unavailable, invalid or unsuitable (this includes TIME or FAQ, because the stakeholder required the set to travel together, even though they are not binding authority). 'partial' when every required source is retrieved and verified but individual records hold missing, stale, partial or conflicting information. 'complete' when every required source is retrieved and verified and every in-scope item reaches a supported state. 'failed' when a technical fault prevents reliable generation or validation of the required outputs. A blocked run does not crash or discard work. It keeps the source attempts, captured evidence, factual reconciliation, unresolved and conflicting items and the blocked/unresolved chain. All formal Article 50 conclusions for the run are withheld (no conclusion-to-source dependency tracking), and factual reconciliation may continue. The final calendar is empty in a blocked run. Stage 07 publication_status: blocked→blocked, partial→validated, complete→validated, failed→failed. 'Unsuitable' is decided by observable checks recorded in stage 02:
- expected identity or title
- expected legal identifier (CELEX or ELI) where relevant
- required Article 50 content or anchor
- a version or date appropriate to the 26 Aug 2026 review: a consolidated version on or before the review date, and an amendment in force by the review date
- not a login or landing page
- the expected record structure for company sources
Identity or structure failures make a source 'invalid'. A source whose only failing checks are version or date checks is 'stale' (for example a consolidated version later than the review date, or an amendment not in force by it). A transport failure is 'unavailable', with null content and a null hash. Retrieval time, source revision or version, effective date and review date are kept as separate facts.

**Rationale.** This follows the stakeholder's pause rule for every source and their concern about misleading completeness, while still meeting the assignment's requirement to preserve the blocked chain, register and brief. Withholding all Article 50 conclusions on any failure avoids brittle dependency tracking across sources the stakeholder treats as one set. Observable suitability checks make 'stale' and 'unsuitable' repeatable instead of judgment calls.

**Trade-offs.**

- A transient outage of a non-binding guidance page (TIME or FAQ) blocks the whole run, even though the binding text may be available.
- Blocked runs give Legal and Operations no draft Article 50 conclusions at all, only the evidence and reconciliation.
- The empty calendar in a blocked run drops dated CALENDAR actions that might be independently supportable; they stay visible in the register and brief.
- With current source data the best achievable state is 'partial', because several records are missing, stale or conflicting; 'complete' needs owners to resolve them.

**Downstream effect.**

- Stage 02 records every attempt with retrieval_status and suitability checks.
- Stage 03 lists authority_blockers.
- Stage 05 marks every legal-rule row 'unresolved' with a withheld reason in a blocked run.
- Every snapshot's status and the brief's run status follow the run state.
- Stage 07 publication_status follows the mapping.
- The calendar is empty in a blocked run.

*Recorded in snapshot stage(s):* scope, authority-and-timing, publication-validation

## D-003 — Read the ten interview-disclosed URLs live and read-only, using existing share-link permissions. No credentials, no local substitutes; Google Sheets via one-tab-verified CSV export, Notion via an isolated page-chunk adapter.

*Decided by:* Project developer (independent decision; no stakeholder or facilitator approval)  

**Concern.** The stakeholder said the company sources require authorized native access and are not public, yet every disclosed URL returned content without credentials. The assignment forbids exposing credentials and substituting local copies, and requires the disclosed routes to be read live each run. The human-facing pages for Sheets and Notion are JavaScript shells that hold no data.

**Options considered.**

1. Add an authentication system (Google service account, Notion integration token). — *No credentials were issued, and the assignment specifies none; inventing one adds secrets to manage and an unapproved access path.*
2. Treat the sources as public and describe them that way. — *Contradicts the stakeholder's statement; unauthenticated readability is not proof of public status.*
3. Read the disclosed URLs through their existing share-link permission with read-only routes (Sheets CSV export after verifying the tab list; Notion page-chunk endpoint behind an adapter), and record that no credentials are used. — *Reads the live source directly with no secrets, keeps the mechanism replaceable and is honest about the access basis.*
4. Render the Notion page in a headless browser. — *Closest to the human route but adds a heavy browser dependency without evidence that the current route is insufficient.*

**Source basis.**

- `INT2-L35` (interviews/project-b-regulatory-compliance-20261006-1750.md line 35): Company sources require authorized native access and are not meant to be publicly readable; access them through their official URLs with approved read-only permissions.
- `ASSIGN-CAPTURE` (Project B assignment, 'Snapshots and captured sources', stage 02 paragraph): Record every source attempt including failed and unused attempts; verify identity, version and suitability for the review date; a login or landing page is not the requested document; accept interview-disclosed routes as runtime inputs; do not replace a failed live read with an undisclosed local copy.
- `ASSIGN-READONLY` (Project B assignment, 'Your task', second paragraph): Keep the work read-only: do not expose credentials, alter sources, give final legal advice, activate policy, change approved deadlines, close incidents, send official responses or write to a production calendar.
- `INSPECT-ACCESS` (Source access probe, 2026-10-06 (session scratchpad)): All ten disclosed URLs returned HTTP 200 without credentials. Google Sheet /edit pages are JavaScript shells; /export?format=csv returns the data; XLSX export shows exactly one tab per sheet. The Notion HTML is a JavaScript shell; content was returned by the page's own loadCachedPageChunkV2 endpoint, and getPublicPageData reports publicAccessRole=reader and requireLogin=false.

**Chosen behaviour.** The official URLs disclosed in the interviews are live runtime inputs (references/source-routes.json), read on every run. Company sources are read using their existing share-link permissions. No credentials are used or stored, and the sources are never described as public just because an unauthenticated GET currently succeeds. Retrieval is read-only: GET requests, plus the read-only POST that Notion's own page client uses to load a page. Source content is never modified. An undisclosed local copy is never substituted when a live read fails; a failed read is recorded as unavailable or invalid. Google Sheets: the tab list is checked on every run through the XLSX export. Exactly one tab is expected. A different tab count is recorded as an invalid or changed source condition and is not ignored. The single tab is then read through the CSV export. Notion POLICY: the page-chunk retrieval sits behind a source adapter. Page identity, title, policy version, context revision and content retrieval are checked on every run. No API credential or browser dependency is added unless implementation evidence shows the current route is insufficient. Every attempt — successful, failed or unused — is recorded in stage 02. When a read is redirected to another host (Google's signed, time-limited export link), stage 02 records only that host as final_url; the signed path (access signature, expiry, owner account ID) is never stored.

**Rationale.** This respects both the stakeholder's description (no claim of public status, read-only access through the official URLs) and the assignment's rules (no credentials, live reads, no local substitution, every attempt recorded). Isolating the Notion mechanism means it can be replaced if the endpoint changes, without touching the rest of the skill.

**Trade-offs.**

- The Notion page-chunk endpoint is undocumented and may change without notice; a change will block the run until the adapter is updated.
- If the owners revoke link sharing, the run blocks: there is deliberately no credentialed fallback.
- Reading the XLSX export only for the tab list costs one extra request per sheet per run.

**Downstream effect.**

- Stage 02 records the access basis ('share-link permission; no credentials') and the method used for each attempt, including the XLSX tab-check attempts.
- A login page, a changed tab count or a failed Notion identity check makes the source invalid or unavailable, which blocks the run under D-002.
- The README and SKILL.md document that no credentials are needed or accepted.
- Stage 02 final_url is host-only for cross-host redirects; archived snapshots were redacted the same way and documented (CHK-HISTORY-*).

*Recorded in snapshot stage(s):* source-capture

## D-004 — Derive impact states per system and rule from a declared rule catalogue. Each EVIDENCE record is attributed only to the rules whose evidence subjects its own text names, so states are not propagated across a whole system. Never emit compliant or non-compliant findings.

*Decided by:* Implementation decision (Claude), revised at the project developer's request on 2026-10-06 (rule-level evidence states); awaiting developer review  

**Concern.** The register needs a state for each distinct system/rule item. The stakeholder defined supported impact, supported no-impact, conflicting and unresolved in words, and Legal owns final interpretation of applicability. The automation needs a repeatable, inspectable mapping that does not invent facts or make legal findings.

**Options considered.**

1. Free-text interpretation of the policy and legal text on each run. — *Not repeatable or inspectable; risks the automation making unreviewable legal interpretations.*
2. Hard-code per-system outcomes. — *Becomes a local substitute for live sources and breaks when facts change.*
3. Declared rule catalogue with applicability conditions on live structured fields and live POLICY statements located by declared cue phrases, with conservative evidence-state rules and unknowns falling to unresolved. — *Repeatable, traceable to extracts, fails safe when wording changes, and clearly a draft interpretation for Legal.*
4. Apply a system's worst evidence state (SYSTEMS evidence_status plus all its EVIDENCE records) to every applicable rule for that system (the first implementation). — *Simple and conservative, but it propagates one control's gap or conflict to unrelated rules. Rejected on developer review on 2026-10-06.*

**Source basis.**

- `ASSIGN-STATES` (Project B assignment, 'Snapshots and captured sources', paragraph on schema states): Impact states are supported-impact / supported-no-impact / conflicting / unresolved; preserve unresolved or conflicting records with source basis, reason, known owner and resolution need.
- `INT1-L150` (interviews/project-b-regulatory-compliance-20261006-1706.md line 150): Conflicting records occur when owner claims contradict captured evidence, like REC-008. Unresolved means expected facts are missing or stale.
- `INT2-L108` (interviews/project-b-regulatory-compliance-20261006-1750.md line 108): Use the official Article 50 paragraph text; Legal owns the final interpretation of applicability.
- `INT1-L236` (interviews/project-b-regulatory-compliance-20261006-1706.md line 236): The automation cannot decide policy compliance, legal interpretations, exception approvals or operational deadlines.
- `INSPECT-POLICY-STATES` (POLICY Notion page, 'Evidence and exceptions' bullet 2, inspected 2026-10-06): missing, stale, conflicting, and not-applicable are different evidence states. Missing evidence must not be converted to compliance or non-compliance.
- `INSPECT-EVIDENCE-REC-003` (EVIDENCE sheet, row record_id=REC-003, inspected 2026-10-06): REC-003 | AI-003 | incident | 2026-08-24 | Communications | open | social-post-884 | conflicting | Visible label exists but exported platform copy may have lost metadata.

**Chosen behaviour.** Rules (references/rules.json):
- binding Article 50 rules L-50-1, L-50-2, L-50-3, L-50-4-DF and L-50-4-TXT (paragraph 5 is the manner-and-timing condition attached to them; paragraphs 6 and 7 are context)
- POLICY rules POL-T1, POL-T2-PROV, POL-T2-LABEL and POL-T3
Every in-scope system is evaluated against every rule.

Applicability comes from SYSTEMS fields (provider_role, deployer_role, exposed_group, output_type) and from POLICY per-system statements located by declared cue phrases. If a needed fact is unknown or its cue is absent, the row is 'unresolved'.

Evidence is attributed at the system and rule level. Each rule declares its evidence subjects:
- interaction-notice
- provenance-marking
- visible-label-disclosure
- text-output-route
- provider-role
- emotion-biometric
Each subject declares the words that identify it in a record's own evidence_ref and notes (exception_request records count as visible-label-disclosure). A record is attributed only to the subjects it names. A record naming none is 'unattributed' context and affects no row. A record naming several subjects keeps its single recorded state for each rule it names; the automation does not split it, and the reason discloses this. The SYSTEMS evidence_status summary is not propagated to rows.

One exception: if the SYSTEMS register entry is 'stale', the applicability facts for every rule of that system are stale, so all its rows are 'unresolved'. These rows link to the system's CALENDAR action under D-005.

For each row:
- an attributed applicability record (provider-role or emotion-biometric) that is not complete → 'unresolved' ('conflicting' if that record conflicts)
- rule not applicable on recorded facts → 'supported-no-impact'
- rule applies:
  - no attributed control record → 'unresolved'
  - any attributed record conflicting → 'conflicting'
  - any attributed record stale, missing or partial → 'unresolved'
  - otherwise → 'supported-impact', with the control described as evidenced or as a recorded gap (for example current_notice=no)

Binding-law rows are draft readings for Legal. Actor role, applicability and interpretation are Legal's (see the brief's Legal-review boundary section).

**Rationale.** Each conclusion stays traceable to the specific records that bear on that rule, so an unrelated gap or conflict on the same system does not change it. This keeps the stakeholder's definitions (missing or stale facts give unresolved; contradictory claims give conflicting) at the level where they apply, and keeps the law and policy bases separately identifiable.

**Trade-offs.**

- Subject words are matched in free-text notes. A record worded without any subject word is unattributed, so a rule that depends on it shows 'unresolved' (no attributable evidence). This is a safe failure, but it needs the catalogue updated if record wording changes.
- A record naming two subjects (REC-003 and REC-009 name both a label and provenance) applies its single state to both rules. With current data, AI-003's label row stays 'conflicting' because REC-003 is one conflicting record; the owner or Legal must split it.
- Stale register facts still affect every row for that system (AI-005), because the stale facts are the applicability inputs, not a single control's evidence.
- A full system × rule matrix (72 rows) is long; the brief summarizes it.

**Downstream effect.**

- Stage 04 tags each incident_evidence record with evidence_subjects and an attribution note.
- Stage 05 impact records carry attributed_record_ids and cite only attributed records.
- The register 'reason' names the attributed records and discloses multi-subject records.
- The post-run verifier checks that every cited record is attributed to that rule (CHK-D004-*).

*Recorded in snapshot stage(s):* authority-and-timing, impact-analysis

## D-005 — Propose actions from findings, linking them to existing CALENDAR actions to avoid duplication. Take dates only from CALENDAR (Operations' proposals); new actions stay undated, are omitted from the ICS and are explained.

*Decided by:* Implementation decision (Claude), awaiting project developer review  

**Concern.** The automation proposes actions from findings and must account for existing CALENDAR actions, but it cannot set operational deadlines; Operations proposes owners and dates.

**Options considered.**

1. Generate actions and compute due dates from the findings. — *Sets operational deadlines, which the stakeholder and POLICY reserve to Operations.*
2. Report only CALENDAR actions. — *Misses findings that have no action and does not propose anything.*
3. Link each finding that needs action to an existing CALENDAR action for the same system (by declared cue match, or the system's sole action); otherwise propose a new undated action owned by the system owner; carry forward unlinked CALENDAR actions. — *Avoids duplication and loss of work, never invents dates, and keeps undated items visible.*

**Source basis.**

- `INT2-L132` (interviews/project-b-regulatory-compliance-20261006-1750.md line 132): The automation proposes actions from findings and must account for existing CALENDAR actions to prevent duplication or loss of work.
- `INT1-L212` (interviews/project-b-regulatory-compliance-20261006-1706.md line 212): Operations determines proposed dates; if an owner cannot be identified or a dependency timeline is unknown, the date remains blank and visible.
- `INT2-L140` (interviews/project-b-regulatory-compliance-20261006-1750.md line 140): Undated actions remain visible in the draft calendar and brief; they are omitted from the final ICS export.
- `INT1-L236` (interviews/project-b-regulatory-compliance-20261006-1706.md line 236): The automation cannot decide policy compliance, legal interpretations, exception approvals or operational deadlines.
- `ASSIGN-CAL` (Project B assignment, 'Final drafts' table, action-calendar.ics row): Proposed events use STATUS:TENTATIVE; omit undated events and explain them in the register/brief; an empty valid calendar is required when no dated proposal is supportable.
- `INSPECT-CALENDAR` (CALENDAR sheet (Compliance Calendar), inspected 2026-10-06): Columns action_id, system_id, action, owner, due_date, status, approval_required, source_version; ACT-001..ACT-008 all dated; approval_required is operations or legal; no approval outcome column exists.

**Chosen behaviour.** Findings that need action are supported-impact rows with a control gap, plus conflicting and unresolved rows. Each is linked to a CALENDAR action for the same system: first by matching the rule's declared action cues, otherwise when the system has exactly one CALENDAR action. A linked action keeps its CALENDAR id, owner, due date (as the Operations-proposed date), status and required approver. A finding with no linkable action gets a new proposed action (PA-nnn) owned by the system owner, with a blank date and the reason disclosed. CALENDAR actions that are not linked to any finding are carried forward and marked as not derived from this review. The ICS contains only dated proposals, all STATUS:TENTATIVE. Undated actions are omitted from it and explained in the register and brief.

**Rationale.** Meets both interview requirements (findings-driven proposals; no duplication or loss of CALENDAR work) and the rule that the automation does not set deadlines.

**Trade-offs.**

- Cue and system matching may link a finding to an action Operations considers unrelated; the link is shown for Operations to confirm.
- Proposals without a CALENDAR action stay undated until Operations supplies a date.

**Downstream effect.**

- Stage 06 proposed_actions and approval_requirements.
- The register's proposed_action and proposed_due_date columns.
- The ICS events and the brief's actions section.

*Recorded in snapshot stage(s):* actions-and-approvals

## D-006 — Every approval is 'pending', because no source records an approval outcome. The required approver comes from CALENDAR approval_required (actions) or Legal (applicability interpretation). Reviewer responses are applied only from a supplied verified file whose binding validates.

*Decided by:* Implementation decision (Claude), awaiting project developer review  

**Concern.** The schema needs approval statuses, but no source contains approval outcomes. POLICY states that no Legal approval is supplied, and the assignment forbids simulated replies.

**Options considered.**

1. Mark actions approved when CALENDAR shows planned or scheduled. — *Invents approval from a scheduling status.*
2. Mark everything pending with the required approver role, and accept only verified responses bound to the reviewed draft hash. — *Honest; uses only recorded facts.*

**Source basis.**

- `ASSIGN-REVIEW` (Project B assignment, 'Review evidence'): Do not simulate replies or claim an unsent request reached a reviewer; validate response bindings before applying them; leave unmatched responses unresolved.
- `INSPECT-CALENDAR` (CALENDAR sheet (Compliance Calendar), inspected 2026-10-06): Columns action_id, system_id, action, owner, due_date, status, approval_required, source_version; ACT-001..ACT-008 all dated; approval_required is operations or legal; no approval outcome column exists.
- `INT1-L236` (interviews/project-b-regulatory-compliance-20261006-1706.md line 236): The automation cannot decide policy compliance, legal interpretations, exception approvals or operational deadlines.

**Chosen behaviour.** Approval records have status 'pending'. Action approvals use CALENDAR approval_required (legal or operations); impact interpretation approvals use Legal. 'not-required' is not used in this design, because every register row needs either a Legal interpretation review (binding-law and internal-policy rows) or an action approval. Review requests are prepared but not sent. Responses are applied only when supplied with --responses and when their request id, reviewer role, run id and artifact hash match the bound draft. Unmatched responses are recorded as unresolved.

**Rationale.** Uses only recorded facts and keeps decisions with Legal and Operations.

**Trade-offs.**

- The package shows nearly everything as pending, which is accurate but less informative.
- Responses need a strict file format.

**Downstream effect.**

- Stage 06 approval_requirements and review_requests.
- Stage 07 review_bindings.
- The register's approval_status column.

*Recorded in snapshot stage(s):* actions-and-approvals, publication-validation

## D-007 — Represent the as-of date as end of the Dublin business day on 26 Aug 2026. Accept legitimately newer source revisions while recording them separately, and judge legal versions against the review date.

*Decided by:* Implementation decision (Claude), awaiting project developer review  

**Concern.** The review is fixed at 26 Aug 2026, but sources are retrieved later. Some revisions postdate the review date (the POLICY context revision of 12 Sep 2026; guidance pages modified in October 2026).

**Options considered.**

1. Reject any source revised after the as-of date. — *Would block every run, since live pages are always current; contradicts the assignment's acceptance of legitimate newer versions.*
2. Accept newer revisions, record them separately, and require binding legal versions to be in force on the review date. — *Keeps the review date fixed and the version facts visible.*

**Source basis.**

- `INT1-L276` (interviews/project-b-regulatory-compliance-20261006-1706.md line 276): Retrieval time, source revision and business-effective date are separate.
- `INT2-L100` (interviews/project-b-regulatory-compliance-20261006-1750.md line 100): The authoritative version is the binding text effective for 26 August 2026, reconciled against the Official Journal acts and applicable amendments, with Legal confirming.
- `ASSIGN-CHANGED` (Project B assignment, 'Changed inputs and recovery'): Report missing/ambiguous required fields, conflicting identities, invalid values or unsuitable responses; do not guess renamed fields or changed business meanings.
- `INSPECT-LEGAL-VERSIONS` (Legal source inspection, 2026-10-06): OJ 2024/1689 Art 113 applies from 2 Aug 2026; AMEND 2026/1744 published OJ L 24.7.2026, enters into force on the third day after publication, replaces Art 50(7); CONSOLIDATED 02024R1689-20260727 marks the amendments ▼M1, adds Art 111(4) (Art 50(2) transition to 2 Dec 2026).

**Chosen behaviour.** as_of = 2026-08-26T23:59:59+01:00, with as_of_date 2026-08-26, which is never changed. Each source records retrieved_at, its in-source revision, its effective date and its HTTP Last-Modified header separately. CONSOLIDATED is suitable only if its version date is on or before the as-of date. AMEND is suitable only if its entry-into-force date (computed from the stated publication date plus the stated third day) is on or before the as-of date. The OJ is suitable if it identifies Regulation (EU) 2024/1689. Advisory and company sources revised after the as-of date are accepted as the current retrieved revision, with the later revision disclosed as a limitation. Company records reported after the as-of date are flagged.

**Rationale.** Keeps the review date fixed while preserving later evidence and its uncertainty, as the stakeholder described.

**Trade-offs.**

- Accepted guidance revisions dated after the as-of date may not match what was published on 26 Aug; this is disclosed but not corrected.
- The entry-into-force computation depends on the publication-date text pattern.

**Downstream effect.**

- Stage 01 as_of.
- Stage 02 version_metadata.
- Stage 03 timing rules.
- The brief's source quality and limitations section.

*Recorded in snapshot stage(s):* scope, source-capture, authority-and-timing

## D-008 — Preserve every retrieved response gzip-compressed, plus claim-bearing extracts with locators. The one exception is the documented removal of Notion's workspace member table from the POLICY capture. content_hash is the sha256 of the preserved bytes, and the original response hash is recorded for the redacted capture.

*Decided by:* Implementation decision (Claude), revised at the project developer's instruction on 2026-10-06 (Notion member-table redaction)  

**Concern.** The assignment requires the actual bytes or permitted extracts, with locators. The legal pages are 0.6–1.5 MB each, and every run is retained in history. The Notion page-chunk response also carries a workspace member table with third-party names, user IDs and profile-photo links, which committing would publish.

**Options considered.**

1. Store raw bytes uncompressed. — *Simple but grows the repository by about 4 MB per run.*
2. Store only extracts. — *Smaller, but identity checks cannot be re-run on the full document.*
3. Store raw bytes gzip-compressed plus a JSON file of extracts with locators. — *Keeps full fidelity at a fraction of the size.*
4. Redact only recordMap.notion_user from the saved POLICY chunks, record what was removed and the original response hash, and prove that the saved bytes still reproduce every extract. — *Removes third-party personal data while keeping all policy content, identity, version, dates and locators verifiable.*

**Source basis.**

- `ASSIGN-CAPTURE` (Project B assignment, 'Snapshots and captured sources', stage 02 paragraph): Record every source attempt including failed and unused attempts; verify identity, version and suitability for the review date; a login or landing page is not the requested document; accept interview-disclosed routes as runtime inputs; do not replace a failed live read with an undisclosed local copy.
- `DEV-REDACTION-2026-10-06` (Project developer instruction, 2026-10-06 (pre-commit hygiene review)): Redact the Notion workspace member/user table (third-party names, user IDs, profile-photo links) from the saved POLICY capture before committing, preserving all policy/content-bearing data, locators and metadata.
- `INSPECT-NOTION-USERS` (POLICY capture inspection, 2026-10-06): The page-chunk response includes recordMap.notion_user with 5 workspace members (name, user ID, profile-photo link; email blank). Member IDs and names occur nowhere else in the response; blocks carry no creator/editor IDs; other non-block tables are access-role stubs.

**Chosen behaviour.** deliverables/sources/<SOURCE>.<ext>.gz holds the response bytes, and deliverables/sources/<SOURCE>.extracts.json holds claim-bearing extracts with section, paragraph, row or block locators. content_hash is the sha256 of the preserved (uncompressed) bytes. Failed attempts have null content, a null hash and a null local reference.

The POLICY page-chunk responses are the one exception to keeping exact bytes. Before saving, recordMap.notion_user (workspace member names, user IDs and profile-photo links) is removed; everything else is kept, including all blocks, page identity, policy version, context revision and the observation and clarification dates. Each such attempt records redaction.removed_tables and redaction.original_response_sha256 (the hash of the unredacted response). The verifier proves that the saved POLICY bytes contain no member table or profile details, and that they reproduce every POLICY extract (block IDs, order, text), the identity and version patterns, the revision dates and the declared content sections. It applies the same reproduction test to the sheet captures.

**Rationale.** Full fidelity and verifiable hashes at modest size, without publishing third-party personal data that is irrelevant to the review.

**Trade-offs.**

- Readers must decompress the raw file to inspect it; the extracts are plain JSON.
- The saved POLICY chunk is not byte-identical to Notion's response. Its integrity is shown through the recorded original hash and the reproduction check, not by re-hashing Notion's exact bytes.
- Earlier runs archived before this change still hold unredacted POLICY captures in deliverables/history/; they are retained as found unless the developer decides otherwise.

**Downstream effect.**

- Stage 02 local_reference, content_hash and (for POLICY chunks) the redaction metadata.
- The verifier re-hashes the preserved bytes and runs CHK-D008-POLICY-REDACTED, CHK-D008-POLICY-REPRODUCIBLE and CHK-D008-<SHEET>-REPRODUCIBLE.

*Recorded in snapshot stage(s):* source-capture
