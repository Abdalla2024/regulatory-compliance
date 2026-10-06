"""Stage 02 source capture: live read-only retrieval, identity/version/suitability checks,
byte preservation and claim-bearing extracts (decisions D-002, D-003, D-007, D-008)."""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from . import fetch
from .util import html_title, html_to_text, parse_iso_date, rel, sha256_bytes, utc_now, write_gzip, write_json

ACCESS_BASIS = ("Existing share-link permission on the interview-disclosed URL; no credentials, cookies "
                "or tokens are used or stored. Unauthenticated readability is not treated as making the source public.")
PUBLIC_BASIS = "Official public EU web route disclosed in the interview; no credentials used."

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "tenth": 10,
            "twentieth": 20}

STATUS_RANK = {"retrieved": 0, "unverified": 1, "stale": 2, "invalid": 3, "unavailable": 4}


@dataclass
class SourceCapture:
    name: str
    route: dict
    attempts: list = field(default_factory=list)
    status: str = "unavailable"
    parsed: dict = field(default_factory=dict)
    extracts: dict = field(default_factory=dict)      # evidence_id -> extract record
    issues: list = field(default_factory=list)         # record-level data-quality issues
    reasons: list = field(default_factory=list)        # why the source is not 'retrieved'
    version: dict = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return self.status == "retrieved"


class Ctx:
    def __init__(self, root: Path, sources_dir: Path, as_of_date: dt.date):
        self.root = root
        self.sources_dir = sources_dir
        self.as_of_date = as_of_date


# ---------------------------------------------------------------- helpers

def _check(checks: list, name: str, passed: bool, detail: str, kind: str = "identity") -> bool:
    """kind 'identity' failures make a source invalid; kind 'version' failures alone make it stale."""
    checks.append({"check": name, "passed": bool(passed), "detail": detail, "kind": kind})
    return bool(passed)


def _status_from(checks: list) -> str:
    fails = [c for c in checks if not c["passed"]]
    if any(c["kind"] != "version" for c in fails):
        return "invalid"
    return "stale" if fails else "retrieved"


def _attempt(cap: SourceCapture, ctx: Ctx, resp: fetch.Response, purpose: str, *, store_as: str | None,
             status: str, checks: list, used: bool, reason: str | None = None, extracts_ref: str | None = None,
             version: dict | None = None, extra: dict | None = None) -> dict:
    n = len(cap.attempts) + 1
    local_ref, content_hash = None, None
    if resp.data is not None and resp.status == 200 and store_as:
        path = ctx.sources_dir / f"{store_as}.gz"
        write_gzip(path, resp.data)
        local_ref = rel(path, ctx.root)
        content_hash = sha256_bytes(resp.data)
    route = cap.route
    rec = {
        "id": f"ATT-{cap.name}-{n}",
        "summary": f"{cap.name} {purpose}: {status}" + (f" ({reason})" if reason else ""),
        "evidence_ids": [],
        "source_name": cap.name,
        "source_role": route["source_role"],
        "authority": route["authority"],
        "authority_class": route["authority_class"],
        "locator": resp.url,
        "retrieved_at": resp.requested_at,
        "retrieval_status": status,
        "content_type": resp.content_type or "none (no content obtained)",
        "version_metadata": version if version is not None else None,
        "content_hash": content_hash,
        "local_reference": local_ref,
        "extracts_reference": extracts_ref,
        "attempt_purpose": purpose,
        "method": resp.method,
        "http_status": resp.status,
        "final_url": safe_final_url(resp.final_url, resp.url),
        "transport_error": resp.error,
        "used_as_evidence": used,
        "suitability_checks": checks,
        "access_basis": ACCESS_BASIS if route["authority_class"] == "company" else PUBLIC_BASIS,
        "owner": "Operations" if route["authority_class"] == "company" else "European Commission",
    }
    if content_hash is None:
        rec["content_hash"] = None
        rec["local_reference"] = None
    if extra:
        rec.update(extra)
    cap.attempts.append(rec)
    return rec


def safe_final_url(final_url: str | None, requested: str) -> str | None:
    """Record where a request ended without keeping signed or time-limited redirect paths.
    A redirect to another host (e.g. Google's signed *.googleusercontent.com export link, which embeds an access
    signature, expiry and the owner's account ID) is recorded as its host only."""
    if not final_url or final_url == requested:
        return final_url
    fu, rq = urlparse(final_url), urlparse(requested)
    if fu.netloc != rq.netloc:
        return f"{fu.scheme}://{fu.netloc}/[signed redirect path not recorded]"
    return final_url


def _http_version(resp: fetch.Response) -> dict:
    return {k: resp.headers.get(k) for k in ("last-modified", "etag") if resp.headers.get(k)}


def _parse_dmy_words(s: str) -> dt.date | None:
    m = re.match(r"(\d{1,2}) (\w+) (\d{4})", s.strip())
    if not m or m.group(2).lower() not in MONTHS:
        return None
    return dt.date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))


def _write_extracts(cap: SourceCapture, ctx: Ctx) -> str | None:
    if not cap.extracts:
        return None
    path = ctx.sources_dir / f"{cap.name}.extracts.json"
    write_json(path, {"source": cap.name, "locator": cap.route["url"], "extracts": list(cap.extracts.values())})
    return rel(path, ctx.root)


def _extract(cap: SourceCapture, eid: str, locator: str, text: str, **extra) -> str:
    cap.extracts[eid] = {"id": eid, "locator": locator, "text": text, **extra}
    return eid


# ---------------------------------------------------------------- legal text parsing

ART50_HEADING = "Article 50 Transparency obligations for providers and deployers of certain AI systems"


def article50_paragraphs(text: str) -> dict[int, str]:
    start = text.rfind(ART50_HEADING)
    if start < 0:
        return {}
    end = text.find("CHAPTER V", start)
    body = text[start + len(ART50_HEADING): end if end > 0 else start + 20000]
    paras: dict[int, str] = {}
    positions = []
    pos = 0
    for n in range(1, 8):
        m = re.compile(rf"(?:^|\s)(?:▼\w+\s+)?{n}\.\s+(?=[A-Z])").search(body, pos)
        if not m:
            break
        positions.append((n, m.end()))
        pos = m.end()
    for i, (n, p) in enumerate(positions):
        q = positions[i + 1][1] if i + 1 < len(positions) else len(body)
        seg = body[p:q]
        if i + 1 < len(positions):
            seg = re.sub(rf"\s*(?:▼\w+\s+)?{positions[i + 1][0]}\.\s*$", "", seg)
        paras[n] = re.sub(r"\s*▼\w+\s*$", "", seg).strip()
    return paras


def _segment(text: str, heading: str, stops: list[str], use_last: bool = True, limit: int = 4000) -> str | None:
    i = text.rfind(heading) if use_last else text.find(heading)
    if i < 0:
        return None
    ends = [j for j in (text.find(s, i + len(heading)) for s in stops) if j > 0]
    return text[i: min(ends) if ends else i + limit].strip()


# ---------------------------------------------------------------- adapters

def capture_eurlex_or_html(cap: SourceCapture, ctx: Ctx) -> None:
    route, exp = cap.route, cap.route["expect"]
    resp = fetch.request(route["url"])
    checks: list = []
    version = _http_version(resp)
    if not resp.ok:
        cap.reasons.append(f"retrieval failed: {resp.error or resp.status}")
        _attempt(cap, ctx, resp, "document retrieval", store_as=None, status="unavailable", checks=checks,
                 used=False, reason=resp.error or f"HTTP {resp.status}", version=version or None)
        cap.status = "unavailable"
        return
    markup = resp.data.decode("utf-8", errors="replace")
    title = html_title(markup) or ""
    text = html_to_text(markup)
    host_ok = urlparse(resp.final_url or "").netloc == urlparse(route["url"]).netloc
    _check(checks, "same-host final URL (not redirected to login)", host_ok, resp.final_url or "")
    _check(checks, "content type is HTML", "html" in (resp.content_type or ""), resp.content_type or "")
    _check(checks, "expected title", exp["title_contains"] in title, f"title: {title}")
    for t in exp.get("text_contains", []):
        _check(checks, "expected content present", t in text, t[:90])
    if exp.get("anchor"):
        _check(checks, "Article 50 anchor present", exp["anchor"] in markup, exp["anchor"])
    if exp.get("identifier"):
        _check(checks, "legal identifier present", exp["identifier"] in title or exp["identifier"] in text,
               exp["identifier"])
    status = "retrieved" if all(c["passed"] for c in checks) else "invalid"
    parsed: dict = {"title": title, "text_length": len(text)}
    version.update({"title": title})

    if cap.name in ("OJ", "CONSOLIDATED"):
        paras = article50_paragraphs(text)
        parsed["article50"] = paras
        _check(checks, "Article 50 paragraphs 1-7 parsed", sorted(paras) == list(range(1, 8)),
               f"parsed paragraphs {sorted(paras)}")
        for n, ptext in paras.items():
            _extract(cap, f"EXT-{cap.name}-ART50-{n}", f"Article 50({n})", ptext)
        a113 = _segment(text, "Article 113 Entry into force and application", ["ANNEX I", "Done at"])
        if a113:
            parsed["article113"] = a113
            _extract(cap, f"EXT-{cap.name}-ART113", "Article 113", a113)
            m = re.search(r"It shall apply from (\d{1,2} \w+ \d{4})", a113)
            parsed["general_application_date"] = (_parse_dmy_words(m.group(1)).isoformat()
                                                  if m and _parse_dmy_words(m.group(1)) else None)
        if cap.name == "CONSOLIDATED":
            m = re.search(r"02024R1689-(\d{8})", title)
            vdate = dt.datetime.strptime(m.group(1), "%Y%m%d").date() if m else None
            version.update({"consolidated_version_date": vdate.isoformat() if vdate else None,
                            "celex": f"02024R1689-{m.group(1)}" if m else None})
            parsed["version_date"] = vdate.isoformat() if vdate else None
            requested = re.search(r"02024R1689-(\d{8})", route["url"])
            if _check(checks, "consolidated version date determinable", vdate is not None, str(vdate)):
                _check(checks, "consolidated version on or before review date", vdate <= ctx.as_of_date,
                       f"{vdate} <= {ctx.as_of_date}", kind="version")
                _check(checks, "returned version is the requested consolidated version",
                       requested is not None and m.group(1) == requested.group(1),
                       f"returned {m.group(1)}, requested {requested.group(1) if requested else None}", kind="version")
            m4 = re.search(r"4\. Providers of AI systems, including general-purpose AI systems, generating "
                           r"synthetic audio, image, video or text content, that have been placed on the market "
                           r"before (\d{1,2} \w+ \d{4}) shall take the necessary steps in order to comply with "
                           r"Article 50\(2\) by (\d{1,2} \w+ \d{4})", text)
            if m4:
                parsed["art111_4"] = {"placed_before": _parse_dmy_words(m4.group(1)).isoformat(),
                                      "comply_by": _parse_dmy_words(m4.group(2)).isoformat(),
                                      "text": m4.group(0)}
                _extract(cap, "EXT-CONSOLIDATED-ART111-4", "Article 111(4)", m4.group(0))
        else:
            m = re.search(r"OJ L, 2024/1689, (\d{1,2}\.\d{1,2}\.\d{4})", text)
            version.update({"eli": "http://data.europa.eu/eli/reg/2024/1689/oj",
                            "publication": m.group(0) if m else None})

    if cap.name == "AMEND":
        art1 = _segment(text, "Article 1 Amendments to Regulation (EU) 2024/1689", ["Article 2 Amendments to"],
                        use_last=False, limit=200000) or ""
        items = []
        for m in re.finditer(r"\((\d+)\) (?:in )?Article (50|111|113)\b([^‘]{0,160})", art1):
            items.append({"item": int(m.group(1)), "article": int(m.group(2)), "text": m.group(0).strip()})
            _extract(cap, f"EXT-AMEND-ITEM-{m.group(1)}", f"Article 1, point ({m.group(1)})", m.group(0).strip())
        parsed["items_on_50_111_113"] = items
        parsed["art50_paragraphs_replaced"] = sorted({int(x) for it in items if it["article"] == 50
                                                      for x in re.findall(r"paragraph (\d+) is replaced", it["text"])})
        pub = re.search(r"OJ L, 2026/1744, (\d{1,2})\.(\d{1,2})\.(\d{4})", text)
        eif = re.search(r"shall enter into force on the (\w+) day following that of its publication", text)
        pub_date = dt.date(int(pub.group(3)), int(pub.group(2)), int(pub.group(1))) if pub else None
        eif_days = ORDINALS.get(eif.group(1).lower()) if eif else None
        eif_date = pub_date + dt.timedelta(days=eif_days) if pub_date and eif_days else None
        if pub:
            _extract(cap, "EXT-AMEND-PUBLICATION", "document header", pub.group(0))
        if eif:
            _extract(cap, "EXT-AMEND-EIF", "Article 4", eif.group(0))
        version.update({"eli": "http://data.europa.eu/eli/reg/2026/1744/oj",
                        "publication_date": pub_date.isoformat() if pub_date else None,
                        "entry_into_force_date": eif_date.isoformat() if eif_date else None,
                        "entry_into_force_basis": (f"{eif.group(0)}; computed as publication date + {eif_days} days"
                                                   if eif else None)})
        parsed.update({"publication_date": version["publication_date"],
                       "entry_into_force_date": version["entry_into_force_date"]})
        if _check(checks, "amendment entry-into-force date determinable", eif_date is not None, str(eif_date)):
            _check(checks, "amendment in force by review date", eif_date <= ctx.as_of_date,
                   f"{eif_date} <= {ctx.as_of_date}", kind="version")

    if cap.name == "LAW":
        i = text.find("Providers shall ensure that AI systems intended to interact directly")
        if i >= 0:
            _extract(cap, "EXT-LAW-ART50-1", "Article 50 page, paragraph 1", text[i:i + 600])
        j = text.find("The summaries are meant to provide helpful explanation")
        if j >= 0:
            _extract(cap, "EXT-LAW-DISCLAIMER", "Article 50 page, summary note", text[j:j + 120])
    if cap.name == "TIME":
        start = text.find("Timeline for the Implementation of the EU AI Act The EU")
        body = text[start:] if start >= 0 else text
        stop = body.find("AI Act Service Desk Contact us")
        body = body[:stop] if stop > 0 else body
        ms, prev = [], None
        # Milestone headings are strictly ascending; a date mentioned inside a milestone's text
        # (e.g. "placed on the market before 02 Aug 2026") is not a heading.
        for m in re.finditer(r"(\d{2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4})", body):
            d = dt.datetime.strptime(m.group(0), "%d %b %Y").date()
            if prev is None or d > prev:
                ms.append(m)
                prev = d
        milestones = []
        for k, m in enumerate(ms):
            seg = body[m.start(): ms[k + 1].start() if k + 1 < len(ms) else len(body)].strip()
            d = dt.datetime.strptime(m.group(0), "%d %b %Y").date()
            eid = _extract(cap, f"EXT-TIME-{d.isoformat()}", f"timeline milestone {m.group(0)}", seg)
            milestones.append({"date": d.isoformat(), "text": seg, "evidence_id": eid})
        parsed["milestones"] = milestones
        _check(checks, "timeline milestones parsed", len(milestones) > 0, f"{len(milestones)} milestones")
    if cap.name == "FAQ":
        m = re.search(r"Last update (\d{1,2} \w+ \d{4})", text)
        if m:
            version["page_last_update"] = _parse_dmy_words(m.group(1)).isoformat()
            _extract(cap, "EXT-FAQ-LAST-UPDATE", "page header", m.group(0))
        i = text.find("This page provides answers")
        if i >= 0:
            _extract(cap, "EXT-FAQ-INTRO", "page introduction", text[i:i + 3000])
    if cap.name in ("LAW", "TIME", "FAQ"):
        lm = resp.headers.get("last-modified")
        if lm:
            version["revision_after_review_date"] = (
                dt.datetime.strptime(lm, "%a, %d %b %Y %H:%M:%S %Z").date() > ctx.as_of_date)

    status = _status_from(checks)
    cap.status = status
    if status != "retrieved":
        cap.reasons += [f"{c['check']} failed ({c['detail']})" for c in checks if not c["passed"]]
    cap.parsed = parsed
    cap.version = version
    ext = _write_extracts(cap, ctx)
    ext_name = {"eurlex": "html", "html": "html"}[route["adapter"]]
    _attempt(cap, ctx, resp, "document retrieval", store_as=f"{cap.name}.{ext_name}", status=status, checks=checks,
             used=status == "retrieved", reason="; ".join(cap.reasons) or None, extracts_ref=ext, version=version)


def capture_gsheet(cap: SourceCapture, ctx: Ctx) -> None:
    route, exp = cap.route, cap.route["expect"]
    m = re.search(r"/spreadsheets/d/([\w-]+)", route["url"])
    sheet_id = m.group(1)
    base = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"

    # Attempt 1: tab-structure verification via XLSX export (decision D-003).
    xresp = fetch.request(f"{base}?format=xlsx")
    xchecks: list = []
    tabs = None
    if xresp.ok:
        try:
            wb = zipfile.ZipFile(io.BytesIO(xresp.data)).read("xl/workbook.xml").decode("utf-8")
            tabs = re.findall(r'<sheet [^>]*name="([^"]+)"', wb)
        except (zipfile.BadZipFile, KeyError):
            tabs = None
    _check(xchecks, "workbook returned (not a login page)", tabs is not None, xresp.content_type or str(xresp.error))
    tab_ok = tabs == exp["tabs"]
    if tabs is not None:
        _check(xchecks, "expected single tab structure", tab_ok, f"tabs found: {tabs}; expected {exp['tabs']}")
    xstatus = "unavailable" if not xresp.ok else ("retrieved" if all(c["passed"] for c in xchecks) else "invalid")
    _attempt(cap, ctx, xresp, "tab-structure verification (XLSX export)", store_as=f"{cap.name}.xlsx", status=xstatus,
             checks=xchecks, used=False, reason=None if xstatus == "retrieved" else
             ("; ".join(c["detail"] for c in xchecks if not c["passed"]) or xresp.error),
             version={"tabs": tabs})

    # Attempt 2: content via CSV export of the (single) tab.
    resp = fetch.request(f"{base}?format=csv")
    checks: list = []
    if not resp.ok:
        cap.status = "unavailable"
        cap.reasons.append(f"CSV retrieval failed: {resp.error or resp.status}")
        _attempt(cap, ctx, resp, "content retrieval (CSV export)", store_as=None, status="unavailable", checks=checks,
                 used=False, reason=resp.error or f"HTTP {resp.status}")
        return
    is_csv = "text/csv" in (resp.content_type or "")
    _check(checks, "CSV content type (not a login page)", is_csv, resp.content_type or "")
    rows, header = [], []
    if is_csv:
        txt = resp.data.decode("utf-8-sig", errors="replace")
        reader = list(csv.reader(io.StringIO(txt)))
        header = [h.strip() for h in reader[0]] if reader else []
        for idx, r in enumerate(reader[1:], start=2):
            if not any(c.strip() for c in r):
                continue
            row = {header[i]: (r[i].strip() if i < len(r) else "") for i in range(len(header)) if header[i]}
            row["_row"] = idx
            rows.append(row)
    missing = [c for c in exp["required_columns"] if c not in header]
    dup_cols = sorted({h for h in header if h and header.count(h) > 1})
    _check(checks, "required columns present", not missing, f"missing: {missing}" if missing else "all present")
    _check(checks, "no duplicated column headers", not dup_cols, f"duplicated: {dup_cols}" if dup_cols else "none")
    extra = [h for h in header if h and h not in exp["required_columns"]]
    idcol = exp["id_column"]
    ids = [r.get(idcol, "") for r in rows]
    dup_ids = sorted({i for i in ids if ids.count(i) > 1})
    _check(checks, "records present", len(rows) > 0, f"{len(rows)} records")
    _check(checks, "unique record identifiers", not dup_ids and all(ids),
           f"duplicates: {dup_ids}" if dup_ids else ("blank id present" if not all(ids) else "unique"))
    if tabs is not None or xstatus != "retrieved":
        _check(checks, "tab structure verified", xstatus == "retrieved", f"tab check status: {xstatus}")

    # Value-level problems stay record-level issues (affected items become unresolved).
    if not missing:
        blanks_ok = set(exp.get("optional_blank_columns", []))
        for r in rows:
            for col in exp["required_columns"]:
                if not r.get(col) and col not in blanks_ok:
                    cap.issues.append({"record_id": r.get(idcol), "field": col, "value": "",
                                       "problem": "required value blank", "row": r["_row"]})
            for col in exp.get("date_columns", []):
                v = r.get(col, "")
                if v and parse_iso_date(v) is None:
                    cap.issues.append({"record_id": r.get(idcol), "field": col, "value": v,
                                       "problem": "not a YYYY-MM-DD date", "row": r["_row"]})
            for col, allowed in exp.get("enums", {}).items():
                v = r.get(col, "")
                if v and v not in allowed:
                    cap.issues.append({"record_id": r.get(idcol), "field": col, "value": v,
                                       "problem": f"value outside disclosed meanings {allowed}", "row": r["_row"]})
    status = "retrieved" if all(c["passed"] for c in checks) else "invalid"
    vers = sorted({r.get("record_version") or r.get("source_version") for r in rows
                   if r.get("record_version") or r.get("source_version")})
    version = {"in_source_versions": vers, "tabs": tabs, "columns": header, "extra_columns": extra}
    later = [v for v in vers if (d := re.search(r"(\d{4}-\d{2}-\d{2})$", v)) and parse_iso_date(d.group(1)) > ctx.as_of_date]
    version["versions_after_review_date"] = later
    for r in rows:
        rid = r.get(idcol)
        _extract(cap, f"EXT-{cap.name}-{rid}", f"tab '{(tabs or ['?'])[0]}' row {r['_row']} ({idcol}={rid})",
                 " | ".join(f"{k}={v}" for k, v in r.items() if k != "_row"),
                 fields={k: v for k, v in r.items() if k != "_row"})
    cap.status = status
    if status != "retrieved":
        cap.reasons += [f"{c['check']} failed ({c['detail']})" for c in checks if not c["passed"]]
    cap.parsed = {"header": header, "rows": rows, "extra_columns": extra}
    cap.version = version
    ext = _write_extracts(cap, ctx)
    _attempt(cap, ctx, resp, "content retrieval (CSV export)", store_as=f"{cap.name}.csv", status=status,
             checks=checks, used=status == "retrieved", reason="; ".join(cap.reasons) or None, extracts_ref=ext,
             version=version)


def _notion_value(entry: dict) -> dict:
    v = entry.get("value", {})
    return v.get("value", v) if isinstance(v, dict) else {}


def _notion_text(val: dict) -> str:
    t = val.get("properties", {}).get("title")
    return "".join(seg[0] for seg in t if seg) if t else ""


# Third-party personal data returned alongside the page content. It carries no policy content, identity,
# version or date information (verified 2026-10-06: member IDs and names occur nowhere else in the response).
NOTION_REDACTED_TABLES = ("notion_user",)


def redact_notion_chunk(data: dict) -> tuple[dict, dict]:
    """Drop the workspace member table (names, user IDs, profile photos); keep every other byte of meaning."""
    rm = dict(data.get("recordMap", {}))
    removed = {t: len(rm.pop(t)) for t in NOTION_REDACTED_TABLES if t in rm}
    return {**data, "recordMap": rm}, removed


def notion_ordered_blocks(blocks: dict, page_id: str) -> list[dict]:
    """Document-order blocks reachable from the page block (used for extracts and for re-derivation checks)."""
    ordered: list[dict] = []

    def walk(bid, depth=0):
        entry = blocks.get(bid)
        if not entry or depth > 6:
            return
        val = _notion_value(entry)
        ordered.append({"id": bid, "type": val.get("type"), "text": _notion_text(val)})
        for child in val.get("content", []) or []:
            walk(child, depth + 1)
    walk(page_id)
    return ordered


def capture_notion(cap: SourceCapture, ctx: Ctx) -> None:
    """Notion adapter (decision D-003): isolated so the mechanism can be replaced."""
    route, exp = cap.route, cap.route["expect"]
    host = urlparse(route["url"]).netloc
    page_id = exp["page_id"]
    hexid = page_id.replace("-", "")
    if hexid not in route["url"].replace("-", ""):
        cap.reasons.append("configured page_id does not match the disclosed URL")

    # Attempt 1: access/identity verification (read-only page metadata the page client loads).
    meta_body = json.dumps({"type": "block-space", "name": "page", "blockId": page_id, "saveParent": False,
                            "showMoveTo": False, "shouldDuplicate": False, "projectManagementLaunch": False,
                            "configureOpenInDesktopApp": False, "mobileData": {"isPush": False}}).encode()
    mresp = fetch.request(f"https://{host}/api/v3/getPublicPageData", "POST", meta_body, "application/json")
    mchecks: list = []
    meta = {}
    if mresp.ok:
        try:
            meta = json.loads(mresp.data)
        except ValueError:
            meta = {}
    _check(mchecks, "page metadata returned", bool(meta), mresp.content_type or str(mresp.error))
    if meta:
        _check(mchecks, "page identity matches disclosed URL", meta.get("pageId") == page_id, str(meta.get("pageId")))
        _check(mchecks, "no login required for the share link", meta.get("requireLogin") is False,
               f"requireLogin={meta.get('requireLogin')}, publicAccessRole={meta.get('publicAccessRole')}")
    mstatus = "unavailable" if not mresp.ok else ("retrieved" if all(c["passed"] for c in mchecks) else "invalid")
    _attempt(cap, ctx, mresp, "access and identity verification", store_as="POLICY-page-metadata.json",
             status=mstatus, checks=mchecks, used=False,
             reason=None if mstatus == "retrieved" else "; ".join(c["detail"] for c in mchecks if not c["passed"]),
             version={"space": meta.get("spaceName"), "share_role": meta.get("publicAccessRole")} if meta else None)

    # Attempt 2..n: page content chunks.
    blocks: dict = {}
    cursor = {"stack": []}
    chunk_ok = True
    last_resp = None
    for chunk_no in range(1, 11):
        body = json.dumps({"page": {"id": page_id}, "limit": 100, "cursor": cursor,
                           "verticalColumns": False}).encode()
        resp = fetch.request(f"https://{host}/api/v3/loadCachedPageChunkV2", "POST", body, "application/json")
        last_resp = resp
        data = None
        if resp.ok:
            try:
                data = json.loads(resp.data)
            except ValueError:
                data = None
        cchecks: list = []
        _check(cchecks, "page chunk JSON returned", data is not None and "recordMap" in data,
               resp.content_type or str(resp.error))
        cstatus = "unavailable" if not resp.ok else ("retrieved" if data and "recordMap" in data else "invalid")
        extra = None
        if data is not None:
            original_hash = sha256_bytes(resp.data)
            data, removed = redact_notion_chunk(data)
            resp.data = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            extra = {"redaction": {
                "applied": bool(removed), "removed_tables": removed,
                "reason": "Third-party workspace member data (names, user IDs, profile-photo links) removed before "
                          "saving; it carries no policy content, identity, version or date information (D-008).",
                "original_response_sha256": original_hash,
                "content_hash_basis": "content_hash is the sha256 of the preserved (redacted) bytes"}}
        _attempt(cap, ctx, resp, f"content retrieval (page chunk {chunk_no})", store_as=f"POLICY-chunk-{chunk_no}.json",
                 status=cstatus, checks=cchecks, used=cstatus == "retrieved",
                 reason=None if cstatus == "retrieved" else (resp.error or "unexpected response"), extra=extra)
        if cstatus != "retrieved":
            chunk_ok = False
            break
        blocks.update(data["recordMap"].get("block", {}))
        cursor = data.get("cursor") or {"stack": []}
        if not cursor.get("stack"):
            break

    checks: list = []
    ordered = []
    if chunk_ok:
        ordered = notion_ordered_blocks(blocks, page_id)
    title = ordered[0]["text"] if ordered else ""
    full = "\n".join(b["text"] for b in ordered)
    _check(checks, "page content retrieved", bool(ordered) and chunk_ok, f"{len(ordered)} blocks")
    _check(checks, "expected page title", exp["title_contains"] in title, f"title: {title}")
    pv = re.search(exp["policy_version_pattern"], full)
    cr = re.search(exp["context_revision_pattern"], full)
    _check(checks, "policy version present", pv is not None, pv.group(1) if pv else "not found")
    _check(checks, "context revision present", cr is not None, cr.group(1) if cr else "not found")
    _check(checks, "access verification passed", mstatus == "retrieved", mstatus)
    status = "retrieved" if all(c["passed"] for c in checks) and not cap.reasons else "invalid"
    if not chunk_ok:
        status = "unavailable"

    # Sections: headers split the page; system sections are sub_sub_header blocks named AI-nnn.
    sections, current = {}, None
    for b in ordered[1:]:
        if b["type"] in ("header", "sub_header", "sub_sub_header"):
            current = b["text"]
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(b)
    for k, b in enumerate(ordered):
        _extract(cap, f"EXT-POLICY-BLK-{b['id'][:8]}", f"Notion block {b['id']} (#{k}, {b['type']})", b["text"],
                 block_id=b["id"], block_type=b["type"])
    obs = re.search(r"Business observation date: (\d{1,2} \w+ \d{4})", full)
    acd = re.search(r"Authoring clarification date: (\d{1,2} \w+ \d{4})", full)
    version = {"page_id": page_id, "title": title,
               "policy_version": pv.group(1) if pv else None,
               "context_revision": cr.group(1) if cr else None,
               "business_observation_date": _parse_dmy_words(obs.group(1)).isoformat() if obs else None,
               "authoring_clarification_date": _parse_dmy_words(acd.group(1)).isoformat() if acd else None}
    if last_resp is not None:
        version.update(_http_version(last_resp))
    if version["authoring_clarification_date"]:
        version["revision_after_review_date"] = parse_iso_date(version["authoring_clarification_date"]) > ctx.as_of_date
    cap.status = status
    if status != "retrieved":
        cap.reasons += [f"{c['check']} failed ({c['detail']})" for c in checks if not c["passed"]]
    cap.parsed = {"title": title, "blocks": ordered, "sections": sections, "full_text": full}
    cap.version = version
    ext = _write_extracts(cap, ctx)
    # Summary record for the assembled document (points at the stored chunks).
    for a in cap.attempts:
        if a["used_as_evidence"]:
            a["extracts_reference"] = ext
            a["version_metadata"] = version
            if status != "retrieved":
                a["retrieval_status"] = status
                a["used_as_evidence"] = False  # retained, but an unsuitable page is not evidence
                a["summary"] += f"; assembled page {status}: " + "; ".join(cap.reasons)
            a["suitability_checks"] = a["suitability_checks"] + checks


ADAPTERS = {"eurlex": capture_eurlex_or_html, "html": capture_eurlex_or_html,
            "gsheet": capture_gsheet, "notion": capture_notion}


def capture_all(routes: list[dict], ctx: Ctx) -> dict[str, SourceCapture]:
    caps = {}
    for route in routes:
        cap = SourceCapture(name=route["name"], route=route)
        try:
            ADAPTERS[route["adapter"]](cap, ctx)
        except Exception as e:  # adapter bug or unexpected format: retained as an invalid attempt
            cap.status = "invalid"
            cap.reasons.append(f"adapter error {type(e).__name__}: {e}")
            _attempt(cap, ctx, fetch.Response(method="GET", url=route["url"], requested_at=utc_now(), error=str(e)),
                     "adapter processing", store_as=None, status="invalid", checks=[], used=False,
                     reason=f"{type(e).__name__}: {e}")
        caps[route["name"]] = cap
    return caps
