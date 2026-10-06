# Regulatory Change Impact — starter

Build a reusable Skill that connects regulatory changes to company impacts and draft compliance actions.

## Start

1. Read the [formal assignment](https://private-pecorino-70e.notion.site/Project-B-Regulatory-Change-Impact-Compliance-Actions-Learner-assignment-3da0b700541e8152b6d1c638fd1c34fa?source=copy_link) for the work and acceptance requirements.
2. Create your own repository from [this starter](https://github.com/GitRollTraining/regulatory-compliance) using **Fork**, then clone your copy and work there.

## Supplied files

| File | Purpose |
|---|---|
| `README.md` | Starting instructions and links. |
| `snapshot.schema.json` | Public snapshot contract; keep it unchanged. |

Create the Skill, implementation and outputs described in the formal assignment. This starter supplies no business workflow implementation.

## Before you work

**Interview rule.** You conduct the stakeholder interview yourself, and the questions are yours. Do not connect a coding agent or any other AI to the interview to run, script, or automate it. The interview transcript is assessed together with the code; a project whose interview was run by an agent is not scored.

- Export your interview as the original Work Sim Markdown, save one final complete file per session under `interviews/`, and commit and push it with your code. Do not rewrite the export. If the export is unavailable, contact the facilitator.

- Use an Agent Skills-capable coding environment. Choose and document your implementation runtime and dependencies; no runtime or install command is supplied here.
- Follow the [shared course guide for session capture](https://classroom.google.com/c/ODcyMjA4NTkwNDk2/m/ODc0NzI2NzQzMzQ2/details) and verify capture is active before implementation. Keep credentials out of the repository.
- Meet the [stakeholder](https://work-sim.catalyte.ai/s/project-b-regulatory-compliance) to understand the work and relevant business sources. Read those online sources through their intended access route; an unavailable source is not permission to substitute repository data.

## Running the `regulatory-change-impact-brief` skill

**Runtime:** Python 3.11 or newer (developed on 3.13). **Dependencies:** `jsonschema` and `rfc3339-validator`, pinned
in `regulatory-change-impact-brief/scripts/requirements.txt`. Everything else uses the standard library. You need
outbound HTTPS to eur-lex.europa.eu, ai-act-service-desk.ec.europa.eu, digital-strategy.ec.europa.eu,
docs.google.com and private-pecorino-70e.notion.site. **No credentials are needed or accepted.** The company sources
are read through their existing share-link permission, and none are stored.

One-time setup (from the repository root):

```bash
python3 -m venv .venv
.venv/bin/pip install -r regulatory-change-impact-brief/scripts/requirements.txt
```

End-to-end command (takes about 10–30 seconds; reads all ten sources live on every run):

```bash
.venv/bin/python regulatory-change-impact-brief/scripts/run_review.py
```

The command does five things:
1. Archives any previous run to `deliverables/history/<run-id>/`.
2. Captures the sources to `deliverables/sources/`.
3. Writes the seven snapshots to `deliverables/snapshots/`.
4. Writes `impact-register.csv`, `compliance-brief.md` and `action-calendar.ics` to `deliverables/`.
5. Re-verifies the whole bundle and writes the result to `deliverables/run-verification.json`.

Exit codes:
- `0`: a partial or complete draft was validated.
- `3`: a blocked package was produced, with formal conclusions withheld.
- `1`: the run failed. See `deliverables/failures/`.

Other commands:
- `.venv/bin/python regulatory-change-impact-brief/scripts/run_review.py --verify` checks the current bundle read-only.
- `.venv/bin/python -m unittest discover -s regulatory-change-impact-brief/scripts/tests` runs the offline tests,
  which use synthetic fixtures and need no network.

How the skill works and why: `regulatory-change-impact-brief/SKILL.md`,
`regulatory-change-impact-brief/references/methodology.md`, and the decision records in
`regulatory-change-impact-brief/references/decisions.md`.
