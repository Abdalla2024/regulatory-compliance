"""SYNTHETIC test fixtures. These are NOT copies of the live sources and are never used by a real run;
they only exercise the pipeline's blocking, changed-input and recovery logic offline."""

from __future__ import annotations

import io
import json
import zipfile

from rcib import fetch
from rcib.util import utc_now

ART50 = (
    "Article 50 Transparency obligations for providers and deployers of certain AI systems "
    "1. Providers shall ensure that AI systems intended to interact directly with natural persons are designed so "
    "persons are informed (synthetic test text). "
    "2. Providers of AI systems, including general-purpose AI systems, generating synthetic audio, image, video or text "
    "content, shall ensure that the outputs of the AI system are marked in a machine-readable format (synthetic). "
    "3. Deployers of an emotion recognition system or a biometric categorisation system shall inform the natural "
    "persons exposed thereto (synthetic). "
    "4. Deployers of an AI system that generates or manipulates image, audio or video content constituting a deep fake, "
    "shall disclose (synthetic). Deployers of an AI system that generates or manipulates text which is published with "
    "the purpose of informing the public on matters of public interest shall disclose (synthetic). "
    "5. The information referred to in paragraphs 1 to 4 shall be provided clearly (synthetic). "
    "6. Paragraphs 1 to 4 shall not affect Chapter III (synthetic). "
    "7. {p7} CHAPTER V GENERAL-PURPOSE AI MODELS ")
A113 = ("Article 113 Entry into force and application This Regulation shall enter into force on the twentieth day. "
        "It shall apply from 2 August 2026. However: (a) synthetic. ANNEX I")


def _html(title: str, body: str) -> bytes:
    return f"<html><head><title>{title}</title></head><body>{body}</body></html>".encode()


PAGES = {
    "https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng": _html(
        "Regulation - EU - 2024/1689 - EN - EUR-Lex",
        "<p>OJ L, 2024/1689, 12.7.2024, </p><div id=\"art_50\">" + ART50.format(p7="The AI Office shall encourage codes (old).")
        + "</div>" + A113),
    "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727": _html(
        "EUR-Lex - 02024R1689-20260727 - EN - EUR-Lex",
        "<div id=\"art_50\">" + ART50.format(p7="The Commission shall encourage codes (new).") + "</div>"
        "4. Providers of AI systems, including general-purpose AI systems, generating synthetic audio, image, video or "
        "text content, that have been placed on the market before 2 August 2026 shall take the necessary steps in order "
        "to comply with Article 50(2) by 2 December 2026. " + A113),
    "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ%3AL_202601744": _html(
        "Regulation - EU - 2026/1744 - EN - EUR-Lex",
        "OJ L, 2026/1744, 24.7.2026, Article 1 Amendments to Regulation (EU) 2024/1689 Regulation (EU) 2024/1689 is "
        "amended as follows: (20) in Article 50, paragraph 7 is replaced by the following: ‘7. new’ "
        "Article 2 Amendments to Regulation (EU) 2018/1139 (6) in Article 50, the following paragraph is added: ‘3. x’ "
        "Article 4 Entry into force and application This Regulation shall enter into force on the third day following "
        "that of its publication."),
    "https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50": _html(
        "Article 50: Transparency obligations | AI Act Service Desk",
        "Providers shall ensure that AI systems intended to interact directly with natural persons (synthetic)."),
    "https://ai-act-service-desk.ec.europa.eu/en/ai-act/eu-ai-act-implementation-timeline": _html(
        "Timeline for the Implementation of the EU AI Act | AI Act Service Desk",
        "Timeline for the Implementation of the EU AI Act The EU synthetic. 02 Aug 2026 Transparency rules (Article 50) "
        "start to apply. 02 Dec 2026 Article 50(2) transition for systems placed before 02 Aug 2026. "
        "AI Act Service Desk Contact us"),
    "https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act": _html(
        "Transparency obligations under Article 50 of the AI Act | Shaping Europe",
        "Last update 24 July 2026 This page provides answers about Article 50 (synthetic)."),
}

SHEET_IDS = {"10ky745H_1h9XbGCXPJsiRp5yfdeU08TZtmrsCMinGgU": "SYSTEMS",
             "19BYZ68OSbsa1i9OfF6MzthrdC6q6mt6IWk6ucI8u7Rk": "EVIDENCE",
             "1xtXl_P7Yb9LaECZjjgtlyI-idoAJTAhH-1gQ4vQaCGA": "CALENDAR"}
TABS = {"SYSTEMS": ["AI System Register"], "EVIDENCE": ["Incident Evidence Register"],
        "CALENDAR": ["Compliance Calendar"]}

SYSTEMS_CSV = """system_id,system_name,use_case,owner,provider_role,deployer_role,exposed_group,output_type,current_notice,human_review,evidence_status,evidence_updated_at,record_version
AI-001,Chat T,test chat,Owner A,no,yes,learners,direct_interaction,yes,esc,complete,2026-08-20,register-2026-08-26
AI-002,Draft T,test drafting,Owner B,no,yes,applicants,text,unknown,review,partial,2026-07-01,register-2026-08-26
AI-003,Image T,test images,Owner C,no,yes,public,synthetic_image,visible_label,approval,complete,2026-08-22,register-2026-08-26
AI-004,Coach T,test coach,Owner D,no,yes,learners,direct_interaction,no,esc,complete,2026-08-18,register-2026-08-26
AI-005,Flag T,test flags,Owner E,unknown,yes,learners,classification,yes,human,stale,2026-04-15,register-2026-08-26
AI-006,Summary T,test summaries,Owner F,no,yes,staff,text,not_applicable,author,complete,2026-08-14,register-2026-08-26
AI-007,Guide T,test guide,Owner G,no,yes,public,direct_interaction,no,esc,conflicting,2026-08-21,register-2026-08-26
AI-008,Video T,test video,Owner C,no,yes,public,synthetic_audio_video,visible_label,approval,partial,2026-08-19,register-2026-08-26
"""
EVIDENCE_CSV = """record_id,system_id,record_type,reported_at,owner,status,evidence_ref,evidence_state,notes
REC-001,AI-001,evidence,2026-08-20,Owner A,closed,ref-1,complete,synthetic notice shown
REC-002,AI-002,evidence_gap,2026-08-23,Owner B,open,ref-2,missing,synthetic recipients not told
REC-003,AI-003,incident,2026-08-24,Owner C,open,ref-3,conflicting,synthetic label present but metadata may be lost
REC-004,AI-004,incident,2026-08-18,Owner D,open,ref-4,complete,synthetic first interaction has no notice
REC-005,AI-005,evidence_gap,2026-08-25,Owner E,open,ref-5,stale,synthetic provider role facts outdated
REC-007,AI-006,evidence,2026-08-14,Owner F,closed,ref-7,complete,synthetic restricted to staff workspace
REC-008,AI-007,incident,2026-08-21,Owner G,open,ref-8,conflicting,synthetic owner says banner exists but capture shows none
REC-009,AI-008,evidence,2026-08-19,Owner C,open,ref-9,partial,synthetic label checked but provenance unchecked
"""
CALENDAR_CSV = """action_id,system_id,action,owner,due_date,status,approval_required,source_version
ACT-001,AI-004,Add and verify first-interaction AI notice,Owner D,2026-09-04,planned,operations,calendar-2026-08-26
ACT-002,AI-007,Resolve disclosure evidence conflict,Owner G,2026-09-03,open,operations,calendar-2026-08-26
ACT-005,AI-005,Refresh provider-role and release evidence,Owner E,,open,legal,calendar-2026-08-26
"""
CSVS = {"SYSTEMS": SYSTEMS_CSV, "EVIDENCE": EVIDENCE_CSV, "CALENDAR": CALENDAR_CSV}

PAGE_ID = "3ba0b700-541e-81f0-9998-d48f3b1c2856"
POLICY_BLOCKS = [
    ("page", "Project 2 Regulatory Compliance — Current Internal Policies"),
    ("header", "Internal AI-use policy"), ("text", "Policy version: AI-POL-2026-08-15"),
    ("sub_header", "Learner and public transparency"),
    ("bulleted_list", "A person must receive a clear notice before or at the first interaction (synthetic)."),
    ("bulleted_list", "Media must retain machine-readable provenance when the tool supports it. The owner also requires "
                      "a visible label unless Legal approves a documented exception."),
    ("bulleted_list", "Staff tools are not public. The owner must still record how generated material reaches learners or the public."),
    ("sub_header", "Evidence and exceptions"),
    ("bulleted_list", "missing, stale, conflicting, and not-applicable are different evidence states. Synthetic."),
    ("sub_header", "Approval boundary"),
    ("text", "Legal owns interpretation; Operations owns activation and deadlines (synthetic)."),
    ("header", "Article 50 review — company operating facts"), ("text", "Context revision: RC-CONTEXT-2026-09-12-R1"),
    ("text", "Business observation date: 26 August 2026. Authoring clarification date: 12 September 2026."),
    ("sub_header", "Operating scope"),
    ("text", "For AI-001, AI-002, AI-003, AI-004, AI-006, AI-007 and AI-008, Quillhaven licenses and operates a "
             "third-party supplier's existing AI product."),
    ("sub_header", "Actual use and content"),
    ("sub_sub_header", "AI-001"), ("text", "Synthetic: it does not classify biometric data or infer emotions."),
    ("sub_sub_header", "AI-002"), ("text", "Synthetic: applicants do not converse with the AI product; not material "
                                           "published to inform the public about matters of public interest."),
    ("sub_sub_header", "AI-003"), ("text", "Synthetic: scenes are not depictions of an existing person."),
    ("sub_sub_header", "AI-004"), ("text", "Synthetic: not used to identify or infer emotions or intentions or to assign "
                                           "people to categories from biometric data."),
    ("sub_sub_header", "AI-005"), ("text", "Synthetic: documentation has not yet established whether the flagging uses biometric data."),
    ("sub_sub_header", "AI-006"), ("text", "Synthetic: not published or sent to applicants, learners or the general public."),
    ("sub_sub_header", "AI-007"), ("text", "Synthetic: stylised guide."),
    ("sub_sub_header", "AI-008"), ("text", "Synthetic: presenters are real people; a viewer could mistake it for an "
                                           "authentic recording; not an evidently artistic performance."),
    ("sub_header", "Product timing and evidence limits"),
    ("text", "Synthetic: this context does not replace missing evidence."),
]


def notion_chunk(blocks=POLICY_BLOCKS) -> bytes:
    ids = [PAGE_ID] + [f"{i:08x}-0000-0000-0000-000000000000" for i in range(1, len(blocks))]
    recs = {}
    for i, (typ, text) in enumerate(blocks):
        val = {"id": ids[i], "type": typ, "properties": {"title": [[text]]}}
        if i == 0:
            val["content"] = ids[1:]
        recs[ids[i]] = {"value": {"value": val, "role": "reader"}}
    users = {"00000000-1111-2222-3333-444444444444": {"value": {"value": {
        "id": "00000000-1111-2222-3333-444444444444", "name": "Synthetic Member", "email": "",
        "profile_photo": "https://example.invalid/synthetic-photo"}, "role": "reader"}}}
    return json.dumps({"recordMap": {"block": recs, "notion_user": users}, "cursor": {"stack": []}}).encode()


def xlsx(tabs: list[str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        sheets = "".join(f'<sheet name="{t}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, t in enumerate(tabs))
        z.writestr("xl/workbook.xml", f'<workbook><sheets>{sheets}</sheets></workbook>')
    return buf.getvalue()


class FakeWeb:
    """Serves the synthetic fixtures; `fail`, `override`, `csv_override`, `tabs_override` inject faults."""

    def __init__(self):
        self.fail: set[str] = set()
        self.override: dict[str, bytes] = {}
        self.csv_override: dict[str, str] = {}
        self.tabs_override: dict[str, list[str]] = {}
        self.calls: list[tuple[str, str]] = []

    def __call__(self, url, method="GET", body=None, content_type=None):
        self.calls.append((method, url))
        r = fetch.Response(method=method, url=url, requested_at=utc_now())
        for key in self.fail:
            if key in url:
                r.error = "URLError: synthetic outage"
                return r
        r.status, r.final_url, r.headers = 200, url, {}
        if url in PAGES or url in self.override:
            r.data, r.content_type = self.override.get(url, PAGES.get(url)), "text/html; charset=utf-8"
        elif "docs.google.com" in url:
            name = next(n for sid, n in SHEET_IDS.items() if sid in url)
            if "format=xlsx" in url:
                r.data = xlsx(self.tabs_override.get(name, TABS[name]))
                r.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif name + "-login" in self.csv_override:
                r.data, r.content_type = b"<html><title>Sign in - Google Accounts</title></html>", "text/html"
            else:
                r.data, r.content_type = self.csv_override.get(name, CSVS[name]).encode(), "text/csv; charset=utf-8"
                # Google redirects exports to a signed, time-limited link on another host (synthetic shape).
                r.final_url = ("https://doc-00-sheets.googleusercontent.com/export/SIGNATURE/TOKEN/1791318090000/"
                               "123456789012345678901/*/" + next(k for k, v in SHEET_IDS.items() if v == name) + "?format=csv")
        elif "getPublicPageData" in url:
            r.data = json.dumps({"pageId": PAGE_ID, "requireLogin": False, "publicAccessRole": "reader",
                                 "spaceName": "Synthetic"}).encode()
            r.content_type = "application/json"
        elif "loadCachedPageChunkV2" in url:
            r.data, r.content_type = self.override.get("NOTION", notion_chunk()), "application/json"
        else:
            r.status, r.error, r.data = 404, "HTTP 404 Not Found", None
        return r
