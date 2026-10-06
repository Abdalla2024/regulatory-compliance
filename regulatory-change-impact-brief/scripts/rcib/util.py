"""Hashing, time, JSON and HTML-text helpers shared by every stage."""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import html
import json
import re
from pathlib import Path


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def dump_json(obj) -> bytes:
    """Deterministic UTF-8 JSON so hashes are reproducible from the same content."""
    return (json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n").encode("utf-8")


def write_json(path: Path, obj) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = dump_json(obj)
    path.write_bytes(data)
    return sha256_bytes(data)


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_gzip(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 keeps the compressed file byte-stable for identical content.
    with open(path, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
        gz.write(data)


def read_gzip(path: Path) -> bytes:
    with gzip.open(path, "rb") as gz:
        return gz.read()


_SCRIPT_STYLE = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def html_title(markup: str) -> str | None:
    m = re.search(r"<title[^>]*>(.*?)</title>", markup, re.S | re.I)
    return _WS.sub(" ", html.unescape(m.group(1))).strip() if m else None


def html_to_text(markup: str) -> str:
    """Flatten HTML to single-spaced text; offsets in this text are used as locators."""
    s = _SCRIPT_STYLE.sub(" ", markup)
    s = _TAG.sub(" ", s)
    s = html.unescape(s).replace("\xa0", " ")
    return _WS.sub(" ", s).strip()


def parse_iso_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def rel(path: Path, root: Path) -> str:
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
