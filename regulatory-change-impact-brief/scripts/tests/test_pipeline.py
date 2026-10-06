"""Offline behaviour tests (synthetic fixtures; no network). Run:
    .venv/bin/python -m unittest discover -s regulatory-change-impact-brief/scripts/tests -v
"""

from __future__ import annotations

import csv
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
REPO = SCRIPTS.parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rcib import pipeline, validate  # noqa: E402
import fake_sources as fx  # noqa: E402


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copy(REPO / "snapshot.schema.json", self.tmp / "snapshot.schema.json")
        self.web = fx.FakeWeb()
        self.patch = mock.patch("rcib.fetch.request", self.web)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        shutil.rmtree(self.tmp)

    # helpers
    def run_pipeline(self, **kw):
        return pipeline.run(self.tmp, **kw)

    def snap(self, n):
        return json.loads((self.tmp / "deliverables" / "snapshots" / validate.SNAPSHOT_FILES[n - 1]).read_text())

    def register(self):
        return list(csv.DictReader(io.StringIO((self.tmp / "deliverables" / "impact-register.csv").read_text())))

    def ics(self):
        return (self.tmp / "deliverables" / "action-calendar.ics").read_text()

    def verify(self):
        return validate.verify_bundle(self.tmp, self.tmp / "deliverables", self.tmp / "snapshot.schema.json")

    # tests
    def test_baseline_partial_run_is_valid_and_traceable(self):
        self.assertEqual(self.run_pipeline(), 0)
        v = self.verify()
        self.assertTrue(v["ok"], v["failed"])
        s7 = self.snap(7)
        self.assertEqual(s7["status"], "partial")
        self.assertEqual(s7["state"]["publication_status"], "validated")
        rows = {r["impact_id"]: r for r in self.register()}
        self.assertEqual(len(rows), 72)
        self.assertEqual(rows["IMP-AI-007-POL-T1"]["state"], "conflicting")       # D-001 (REC-008)
        self.assertEqual(rows["IMP-AI-007-POL-T1"]["owner"], "Owner G")
        self.assertEqual(rows["IMP-AI-003-POL-T2-PROV"]["state"], "conflicting")  # D-001 (REC-003)
        self.assertEqual(rows["IMP-AI-005-L-50-3"]["state"], "unresolved")       # stale register facts
        self.assertEqual(rows["IMP-AI-004-POL-T1"]["state"], "supported-impact")
        self.assertEqual(rows["IMP-AI-004-POL-T1"]["proposed_due_date"], "2026-09-04")
        # Undated CALENDAR action and new proposals stay blank and are absent from the ICS.
        self.assertEqual(rows["IMP-AI-005-L-50-3"]["proposed_due_date"], "")
        self.assertIn("undated", rows["IMP-AI-005-L-50-3"]["reason"])
        self.assertNotIn("ACT-005@", self.ics())
        self.assertIn("UID:ACT-001@", self.ics())
        self.assertTrue(rows["IMP-AI-002-POL-T3"]["proposed_action"].startswith("PA-AI-002-POL-T3"))
        # Never a compliance verdict, never an invented approval.
        self.assertTrue(all(r["approval_status"] == "pending" for r in rows.values()))
        brief = (self.tmp / "deliverables" / "compliance-brief.md").read_text()
        for verdict in ("is non-compliant", "is compliant", "state: compliant", "state: non-compliant"):
            self.assertNotIn(verdict, brief.lower())
        self.assertTrue(all(s["run_id"] == s7["run_id"] for s in (self.snap(i) for i in range(1, 8))))

    def test_binding_source_failure_blocks_and_withholds_conclusions(self):
        self.web.fail.add("OJ%3AL_202601744")  # AMEND outage
        self.assertEqual(self.run_pipeline(), 3)
        v = self.verify()
        self.assertTrue(v["ok"], v["failed"])
        s2, s7 = self.snap(2), self.snap(7)
        amend = [a for a in s2["state"]["sources"] if a["source_name"] == "AMEND"]
        self.assertEqual(amend[0]["retrieval_status"], "unavailable")
        self.assertIsNone(amend[0]["content_hash"])
        self.assertIsNone(amend[0]["local_reference"])
        self.assertEqual(s7["status"], "blocked")
        self.assertEqual(s7["state"]["publication_status"], "blocked")
        legal = [r for r in self.register() if r["rule_basis"] == "binding-law"]
        self.assertTrue(all(r["state"] == "unresolved" and r["applicability"] == "withheld" for r in legal))
        self.assertNotIn("BEGIN:VEVENT", self.ics())
        self.assertIn("VERSION:2.0", self.ics())
        self.assertIn("BLOCKED", (self.tmp / "deliverables" / "compliance-brief.md").read_text())

    def test_advisory_source_failure_also_blocks(self):
        self.web.fail.add("eu-ai-act-implementation-timeline")  # TIME outage (D-002)
        self.assertEqual(self.run_pipeline(), 3)
        self.assertEqual(self.snap(7)["state"]["publication_status"], "blocked")

    def test_login_page_is_not_the_document(self):
        self.web.csv_override["SYSTEMS-login"] = "1"
        self.assertEqual(self.run_pipeline(), 3)
        src = {a["source_name"] + a["attempt_purpose"]: a for a in self.snap(2)["state"]["sources"]}
        self.assertEqual(src["SYSTEMScontent retrieval (CSV export)"]["retrieval_status"], "invalid")

    def test_stale_consolidated_version_is_unsuitable(self):
        url = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727"
        self.web.override[url] = fx.PAGES[url].replace(b"02024R1689-20260727 - EN", b"02024R1689-20260901 - EN")
        self.assertEqual(self.run_pipeline(), 3)
        cons = [a for a in self.snap(2)["state"]["sources"] if a["source_name"] == "CONSOLIDATED"][0]
        self.assertEqual(cons["retrieval_status"], "stale")

    def test_reordered_columns_and_extra_column_are_accepted(self):
        rows = list(csv.reader(io.StringIO(fx.SYSTEMS_CSV)))
        order = list(reversed(range(len(rows[0]))))
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow([rows[0][i] for i in order] + ["unrelated_note"])
        for r in reversed(rows[1:]):
            w.writerow([r[i] for i in order] + ["x"])
        self.web.csv_override["SYSTEMS"] = out.getvalue()
        self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual({r["impact_id"]: r["state"] for r in self.register()}["IMP-AI-004-POL-T1"], "supported-impact")
        s2 = [a for a in self.snap(2)["state"]["sources"] if a["source_name"] == "SYSTEMS" and a["used_as_evidence"]][0]
        self.assertEqual(s2["version_metadata"]["extra_columns"], ["unrelated_note"])

    def test_missing_or_renamed_required_column_is_reported_not_guessed(self):
        self.web.csv_override["SYSTEMS"] = fx.SYSTEMS_CSV.replace("output_type", "output_kind", 1)
        self.assertEqual(self.run_pipeline(), 3)
        s = [a for a in self.snap(2)["state"]["sources"] if a["source_name"] == "SYSTEMS"
             and a["attempt_purpose"].startswith("content retrieval")][0]
        self.assertEqual(s["retrieval_status"], "invalid")
        self.assertFalse(s["used_as_evidence"])  # retained, not used
        self.assertIsNotNone(s["content_hash"])  # unsuitable bytes are still preserved
        self.assertTrue(any("output_type" in c["detail"] for c in s["suitability_checks"] if not c["passed"]))

    def test_duplicate_identity_is_invalid(self):
        self.web.csv_override["EVIDENCE"] = fx.EVIDENCE_CSV + "REC-008,AI-007,incident,2026-08-21,Owner G,open,r,complete,dup\n"
        self.assertEqual(self.run_pipeline(), 3)

    def test_invalid_value_makes_affected_rows_unresolved(self):
        self.web.csv_override["SYSTEMS"] = fx.SYSTEMS_CSV.replace("AI-004,Coach T,test coach,Owner D,no,yes,learners,"
                                                                  "direct_interaction", "AI-004,Coach T,test coach,Owner D,"
                                                                  "no,yes,learners,voice_bot")
        self.assertEqual(self.run_pipeline(), 0)
        rows = {r["impact_id"]: r for r in self.register()}
        self.assertEqual(rows["IMP-AI-004-POL-T1"]["state"], "unresolved")
        self.assertTrue(any(g["id"] == "GAP-AI-004-OUTPUT_TYPE-INVALID" for g in self.snap(4)["state"]["evidence_gaps"]))

    def test_new_tab_is_a_changed_source_condition(self):
        self.web.tabs_override["CALENDAR"] = ["Compliance Calendar", "Archive"]
        self.assertEqual(self.run_pipeline(), 3)

    def test_newer_version_values_are_accepted_and_disclosed(self):
        self.web.csv_override["CALENDAR"] = fx.CALENDAR_CSV.replace("calendar-2026-08-26", "calendar-2026-09-30")
        self.assertEqual(self.run_pipeline(), 0)
        cal = [a for a in self.snap(2)["state"]["sources"] if a["source_name"] == "CALENDAR" and a["used_as_evidence"]][0]
        self.assertEqual(cal["version_metadata"]["versions_after_review_date"], ["calendar-2026-09-30"])
        self.assertEqual(self.snap(1)["state"]["as_of_date"], "2026-08-26")

    def test_evidence_state_is_rule_level_not_system_wide(self):
        # A conflicting record about provenance, and a conflicting record naming no rule subject, must not change
        # the interaction-notice row for the same system (D-004, revised).
        self.web.csv_override["EVIDENCE"] = fx.EVIDENCE_CSV + (
            "REC-098,AI-004,incident,2026-08-20,Owner D,open,ref-98,conflicting,synthetic general review dispute\n"
            "REC-099,AI-001,incident,2026-08-20,Owner A,open,ref-99,conflicting,synthetic provenance metadata disputed\n")
        self.assertEqual(self.run_pipeline(), 0)
        rows = {r["impact_id"]: r for r in self.register()}
        self.assertEqual(rows["IMP-AI-001-POL-T1"]["state"], "supported-impact")
        self.assertNotIn("REC-099", rows["IMP-AI-001-POL-T1"]["evidence_ids"])
        self.assertEqual(rows["IMP-AI-004-POL-T1"]["state"], "supported-impact")
        self.assertNotIn("REC-098", rows["IMP-AI-004-POL-T1"]["evidence_ids"])
        recs = {r["id"]: r for r in self.snap(4)["state"]["incident_evidence"]}
        self.assertTrue(recs["REC-098"]["attribution"].startswith("unattributed"))
        self.assertEqual(recs["REC-099"]["evidence_subjects"], ["provenance-marking"])
        imp = {i["id"]: i for i in self.snap(5)["state"]["impacts"]}
        self.assertEqual(imp["IMP-AI-001-POL-T1"]["attributed_record_ids"], ["REC-001"])

    def test_applicable_rule_without_attributable_evidence_is_unresolved(self):
        self.web.csv_override["EVIDENCE"] = fx.EVIDENCE_CSV.replace("synthetic notice shown", "synthetic screenshot ok")
        self.assertEqual(self.run_pipeline(), 0)
        row = {r["impact_id"]: r for r in self.register()}["IMP-AI-001-POL-T1"]
        self.assertEqual(row["state"], "unresolved")
        self.assertIn("No EVIDENCE record", row["reason"])

    def test_policy_capture_is_redacted_and_still_reproduces_extracts(self):
        import gzip
        self.assertEqual(self.run_pipeline(), 0)
        pol = [a for a in self.snap(2)["state"]["sources"] if a["source_name"] == "POLICY" and a["used_as_evidence"]]
        self.assertTrue(pol)
        raw = gzip.decompress((self.tmp / pol[0]["local_reference"]).read_bytes())
        self.assertNotIn(b"notion_user", raw)
        self.assertNotIn(b"Synthetic Member", raw)
        self.assertNotIn(b"googleusercontent", raw)
        self.assertNotIn(b"example.invalid/synthetic-photo", raw)
        self.assertEqual(pol[0]["redaction"]["removed_tables"], {"notion_user": 1})
        self.assertNotEqual(pol[0]["redaction"]["original_response_sha256"], pol[0]["content_hash"])
        checks = {c["id"]: c for c in self.verify()["checks"]}
        self.assertTrue(checks["CHK-D008-POLICY-REDACTED"]["passed"])
        self.assertTrue(checks["CHK-D008-POLICY-REPRODUCIBLE"]["passed"], checks["CHK-D008-POLICY-REPRODUCIBLE"])
        self.assertTrue(checks["CHK-D008-SYSTEMS-REPRODUCIBLE"]["passed"])

    def test_signed_redirect_urls_are_not_recorded(self):
        self.assertEqual(self.run_pipeline(), 0)
        text = (self.tmp / "deliverables" / "snapshots" / "02-source-capture.json").read_text()
        self.assertNotIn("googleusercontent.com/export", text)
        self.assertNotIn("123456789012345678901", text)
        sheet = [a for a in self.snap(2)["state"]["sources"] if a["source_name"] == "SYSTEMS" and a["used_as_evidence"]][0]
        self.assertEqual(sheet["final_url"], "https://doc-00-sheets.googleusercontent.com/[signed redirect path not recorded]")

    def test_rerun_archives_history_and_links_supersession(self):
        self.assertEqual(self.run_pipeline(), 0)
        first = self.snap(1)["run_id"]
        self.assertEqual(self.run_pipeline(reason="unit-test retry"), 0)
        s1 = self.snap(1)
        self.assertNotEqual(s1["run_id"], first)
        self.assertEqual(s1["state"]["supersedes_run_id"], first)
        self.assertEqual(s1["state"]["change_reason"], "unit-test retry")
        hist = self.tmp / "deliverables" / "history" / first
        self.assertTrue((hist / "snapshots" / "07-publication-validation.json").exists())
        self.assertTrue(json.loads((hist / "history-manifest.json").read_text())["integrity_at_archive_time"]["ok"])
        self.assertEqual(self.snap(2)["state"]["changes_since_superseded_run"]["changed_sources"], [])

    def test_damaged_output_is_detected_then_repaired_by_rerun(self):
        self.assertEqual(self.run_pipeline(), 0)
        first = self.snap(1)["run_id"]
        reg = self.tmp / "deliverables" / "impact-register.csv"
        reg.write_text(reg.read_text().replace("supported-impact", "supported-no-impact", 1))
        (self.tmp / "deliverables" / "snapshots" / "04-evidence-reconciliation.json").unlink()
        v = self.verify()
        self.assertFalse(v["ok"])
        failed = {c["id"] for c in v["failed"]}
        self.assertIn("CHK-ARTIFACT-ART-REGISTER", failed)
        self.assertIn("CHK-SNAPSHOT-04", failed)
        self.assertEqual(self.run_pipeline(), 0)  # fresh attempts, new run id
        self.assertTrue(self.verify()["ok"])
        manifest = json.loads((self.tmp / "deliverables" / "history" / first / "history-manifest.json").read_text())
        self.assertFalse(manifest["integrity_at_archive_time"]["ok"])  # recorded honestly, not repaired
        self.assertTrue(any(u["id"] == "PRIOR-RUN-INTEGRITY" for u in self.snap(1)["unresolved"]))

    def test_unmatched_reviewer_response_stays_unresolved(self):
        self.assertEqual(self.run_pipeline(), 0)
        first = self.snap(1)["run_id"]
        resp = self.tmp / "responses.json"
        resp.write_text(json.dumps({"responses": [{
            "response_id": "R-1", "request_id": "RR-ACT-001", "run_id": first, "reviewer_role": "Operations",
            "reviewer_identity": "ops-reviewer", "responded_at": "2026-10-07T10:00:00Z", "outcome": "approved",
            "artifact_path": "compliance-brief.md", "artifact_sha256": "sha256:" + "0" * 64,
            "channel": "facilitator-verified"}]}))
        self.assertEqual(self.run_pipeline(responses=resp), 0)
        s6 = self.snap(6)
        self.assertEqual(s6["state"]["responses_applied"], [])
        self.assertEqual(len(s6["state"]["responses_unmatched"]), 1)
        apr = {a["id"]: a for a in s6["state"]["approval_requirements"]}
        self.assertEqual(apr["APR-ACT-001"]["status"], "pending")

    def test_validly_bound_reviewer_response_is_applied(self):
        self.assertEqual(self.run_pipeline(), 0)
        s7 = self.snap(7)
        b = next(x for x in s7["state"]["review_bindings"] if x["request_id"] == "RR-ACT-001")
        brief = next(a for a in b["artifacts"] if a["path"].endswith("compliance-brief.md"))
        resp = self.tmp / "responses.json"
        resp.write_text(json.dumps({"responses": [{
            "response_id": "R-2", "request_id": "RR-ACT-001", "run_id": s7["run_id"], "reviewer_role": "Operations",
            "reviewer_identity": "ops-reviewer", "responded_at": "2026-10-07T10:00:00Z", "outcome": "approved",
            "reasons": "date feasible", "artifact_path": "compliance-brief.md", "artifact_sha256": brief["sha256"],
            "channel": "facilitator-verified"}]}))
        self.assertEqual(self.run_pipeline(responses=resp), 0)
        apr = {a["id"]: a for a in self.snap(6)["state"]["approval_requirements"]}
        self.assertEqual(apr["APR-ACT-001"]["status"], "approved")
        self.assertEqual(apr["APR-ACT-001"]["response"]["reviewer_identity"], "ops-reviewer")


if __name__ == "__main__":
    unittest.main()
