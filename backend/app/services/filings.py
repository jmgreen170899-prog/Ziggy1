# backend/app/services/filings.py
from __future__ import annotations

import html
import os
import re
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

import httpx

from app.core.config.time_tuning import TIMEOUTS


# ──────────────────────────────────────────────────────────────────────────────
# Public API overview
# ──────────────────────────────────────────────────────────────────────────────
#
# Functions you’re likely to call from a router:
#
#   get_current_filings(forms=None, count=100, ttl=300)
#   get_company_filings(cik_or_ticker, forms=None, count=100, ttl=300)
#   get_filings_for_tickers(["AAPL","MSFT"], forms=["8-K","10-Q"], per_ticker=40, ttl=300)
#
# Each returns:
# {
#   "asof": <epoch>,
#   "count": <int>,
#   "items": [
#     {
#       "cik": "0000320193",
#       "company": "Apple Inc.",
#       "tickers": ["AAPL"],
#       "form": "8-K",
#       "title": "8-K - Apple Inc. (Filer)",
#       "summary": "plain text summary …",
#       "filed": "2025-01-15T13:20:05Z",
#       "ts": 1736947205.0,
#       "accession": "0000320193-25-000012",
#       "link": "https://www.sec.gov/Archives/…",
#       "source": "sec-edgar"
#     },
#     …
#   ]
# }
#
# Notes:
# - Sets a SEC-compliant User-Agent. Configure SEC_USER_AGENT in your .env:
#     SEC_USER_AGENT="Ziggy/1.0 (yourname@example.com)"
# - Maps tickers<->CIK via SEC’s public JSON (cached for 24h).
# - Filters by form types if provided (matches case-sensitively by default; see _form_match).
# - Safe, best-effort parsing (feeds can be quirky).
#


# ──────────────────────────────────────────────────────────────────────────────
# Config / constants
# ──────────────────────────────────────────────────────────────────────────────

SEC_BASE = "https://www.sec.gov/cgi-bin/browse-edgar"
SEC_USER_AGENT = (
    os.getenv("SEC_USER_AGENT")
    or os.getenv("USER_AGENT")
    or "ZiggyFilings/1.0 (contact: devnull@example.com)"
)
MAP_URL_DEFAULT = os.getenv(
    "SEC_TICKER_MAP_URL",
    "https://www.sec.gov/files/company_tickers.json",
)

_NS = {"atom": "http://www.w3.org/2005/Atom"}
_CACHE_TEXT: dict[str, tuple[float, str]] = {}  # URL -> (ts, text)
_CACHE_JSON: dict[str, tuple[float, Any]] = {}  # URL -> (ts, obj)

DEFAULT_FORMS = ["10-K", "10-Q", "8-K", "S-1", "S-3", "424B2", "FWP"]


# ──────────────────────────────────────────────────────────────────────────────
# Data shapes
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class Filing:
    cik: str | None
    company: str | None
    tickers: list[str]
    form: str | None
    title: str | None
    summary: str | None
    filed: str | None  # ISO8601 Z
    ts: float | None  # epoch
    accession: str | None
    link: str | None
    source: str = "sec-edgar"


# ──────────────────────────────────────────────────────────────────────────────
# Public functions
# ──────────────────────────────────────────────────────────────────────────────


def get_current_filings(
    forms: Iterable[str] | None = None,
    *,
    count: int = 100,
    ttl: int = 300,
) -> dict[str, Any]:
    """
    Latest filings across all companies. Optionally filter by form types.
    """
    url = _sec_url(
        action="getcurrent",
        owner="exclude",
        count=str(max(1, min(count, 200))),
        output="atom",
    )
    xml = _http_get_text(url, ttl=ttl)
    items = _parse_atom_feed(xml, ticker_map=_get_ticker_map(ttl=86_400))
    items = _filter_forms(items, forms)
    return _pack(items)


def get_company_filings(
    cik_or_ticker: str,
    forms: Iterable[str] | None = None,
    *,
    count: int = 100,
    ttl: int = 300,
) -> dict[str, Any]:
    """
    Company filings for a given CIK or ticker.
    """
    cik, tickers, company = _resolve_company(cik_or_ticker, ttl=86_400)
    if not cik:
        return _pack([])

    url = _sec_url(
        action="getcompany",
        CIK=cik,
        owner="exclude",
        count=str(max(1, min(count, 200))),
        output="atom",
    )
    xml = _http_get_text(url, ttl=ttl)
    items = _parse_atom_feed(xml, ticker_map=_get_ticker_map(ttl=86_400))

    # (Optional) enrich known fields
    for it in items:
        it.cik = it.cik or cik
        if not it.tickers and tickers:
            it.tickers = tickers
        if not it.company and company:
            it.company = company

    items = _filter_forms(items, forms)
    return _pack(items)


def get_filings_for_tickers(
    tickers: Iterable[str],
    *,
    forms: Iterable[str] | None = None,
    per_ticker: int = 40,
    ttl: int = 300,
) -> dict[str, Any]:
    """
    Fetch filings for multiple tickers (convenience).
    """
    out: list[Filing] = []
    tickers = [t.strip().upper() for t in (tickers or []) if t and str(t).strip()]
    for t in tickers[:40]:  # cheap guardrail
        data = get_company_filings(t, forms=forms, count=per_ticker, ttl=ttl)
        for it in data.get("items", []):
            out.append(_to_filing(it))
    # de-dupe by (accession|link|title), newest first
    out = _dedupe_filings(out)
    return _pack(out)


# ──────────────────────────────────────────────────────────────────────────────
# Core: SEC Atom parsing
# ──────────────────────────────────────────────────────────────────────────────


def _parse_atom_feed(
    xml_text: str, *, ticker_map: dict[str, dict[str, Any]] | None = None
) -> list[Filing]:
    """
    Parse SEC Atom feed (latest or company). Be defensive with malformed feeds.
    """
    root = _parse_xml(xml_text)
    entries = root.findall(".//atom:entry", _NS) or root.findall(".//entry")
    filings: list[Filing] = []

    for en in entries:
        title = _txt(en.find("atom:title", _NS)) or _txt(en.find("title"))
        updated = _txt(en.find("atom:updated", _NS)) or _txt(en.find("updated"))
        summary = _txt(en.find("atom:summary", _NS)) or _txt(en.find("summary"))
        link = None
        for ln in en.findall("atom:link", _NS) or en.findall("link"):
            href = (ln.attrib.get("href") or "").strip()
            rel = (ln.attrib.get("rel") or "alternate").strip().lower()
            if href and (rel in ("alternate", "canonical") or not rel):
                link = href
                break
            if href and not link:
                link = href

        # form type appears in <category term="8-K"/>
        form = None
        cat = en.find("atom:category", _NS) or en.find("category")
        if cat is not None:
            form = cat.attrib.get("term") or cat.attrib.get("label")

        # The summary HTML often contains "CIK: 0000320193  Company: Apple Inc."
        company, cik = _extract_company_and_cik(summary or "") or (None, None)
        # Accessions are usually detectable from link
        accession = (
            _extract_accession(link or "") or _extract_accession(title or "") or None
        )

        ts, iso = _parse_time(updated)

        # map tickers from CIK if we know it
        tickers: list[str] = []
        if cik and ticker_map:
            meta = ticker_map.get(cik)
            if meta and meta.get("tickers"):
                tickers = list(meta["tickers"])

        filings.append(
            Filing(
                cik=cik,
                company=company,
                tickers=tickers,
                form=form,
                title=_clean(summary=title),
                summary=_clean(summary=summary),
                filed=iso,
                ts=ts,
                accession=accession,
                link=link,
            )
        )

    filings.sort(key=lambda x: x.ts or 0, reverse=True)
    return filings


# ──────────────────────────────────────────────────────────────────────────────
# SEC company map (ticker <-> CIK), cached ~24h
# ──────────────────────────────────────────────────────────────────────────────

_MAP_TTL_DEFAULT = 86_400  # 24h


def _get_ticker_map(*, ttl: int = _MAP_TTL_DEFAULT) -> dict[str, dict[str, Any]]:
    """
    Returns dict keyed by CIK (zero-padded to 10): {
      "0000320193": {"company": "Apple Inc.", "tickers": ["AAPL"]},
      ...
    }
    """
    url = MAP_URL_DEFAULT
    try:
        data = _http_get_json(
            url, ttl=ttl
        )  # SEC returns { "0":{cik:..., ticker:..., title:...}, ... }
        by_cik: dict[str, dict[str, Any]] = {}
        if isinstance(data, dict):
            # Newer file shape: dict-of-rows with 0..N keys
            for _, row in data.items():
                try:
                    cik_int = int(row.get("cik", 0))
                    cik10 = f"{cik_int:010d}"
                    ticker = (row.get("ticker") or "").strip().upper()
                    title = (row.get("title") or "").strip()
                    if cik10 not in by_cik:
                        by_cik[cik10] = {"company": title, "tickers": set()}
                    if ticker:
                        by_cik[cik10]["tickers"].add(ticker)
                except Exception:
                    continue
        # collapse sets to lists
        for k, v in by_cik.items():
            v["tickers"] = sorted(v["tickers"])
        return by_cik
    except Exception:
        return {}


def _resolve_company(
    cik_or_ticker: str, *, ttl: int = _MAP_TTL_DEFAULT
) -> tuple[str | None, list[str], str | None]:
    """
    Returns (cik10, tickers, company).
    Accepts either a CIK (with or without leading zeros) or a ticker.
    """
    s = (cik_or_ticker or "").strip()
    if not s:
        return None, [], None

    # If it's numeric-ish, treat as CIK
    if re.fullmatch(r"\d{1,10}", s):
        cik10 = f"{int(s):010d}"
        meta = _get_ticker_map(ttl=ttl).get(cik10) or {}
        return cik10, list(meta.get("tickers") or []), meta.get("company")

    # Else assume ticker
    t = s.upper()
    # Build reverse map
    rev: dict[str, tuple[str, str]] = {}
    for cik, meta in _get_ticker_map(ttl=ttl).items():
        for tk in meta.get("tickers") or []:
            rev[tk] = (cik, meta.get("company") or "")
    if t in rev:
        cik10, company = rev[t]
        # gather all tickers for this CIK
        tickers = list(_get_ticker_map(ttl=ttl).get(cik10, {}).get("tickers") or [])
        return cik10, tickers, company

    return None, [], None


# ──────────────────────────────────────────────────────────────────────────────
# HTTP helpers (with tiny TTL caches)
# ──────────────────────────────────────────────────────────────────────────────


def _http_get_text(url: str, *, ttl: int) -> str:
    now = time.time()
    cached = _CACHE_TEXT.get(url)
    if cached and now - cached[0] < max(10, ttl):
        return cached[1]

    headers = {
        "User-Agent": SEC_USER_AGENT,
        "Accept": "application/atom+xml, application/xml;q=0.9, */*;q=0.8",
    }
    with httpx.Client(
        timeout=TIMEOUTS["http_client_long"], headers=headers, follow_redirects=True
    ) as c:
        r = c.get(url)
        r.raise_for_status()
        text = r.text
    _CACHE_TEXT[url] = (now, text)
    return text


def _http_get_json(url: str, *, ttl: int) -> Any:
    now = time.time()
    cached = _CACHE_JSON.get(url)
    if cached and now - cached[0] < max(10, ttl):
        return cached[1]

    headers = {
        "User-Agent": SEC_USER_AGENT,
        "Accept": "application/json, text/json;q=0.9, */*;q=0.8",
    }
    with httpx.Client(
        timeout=TIMEOUTS["http_client_long"], headers=headers, follow_redirects=True
    ) as c:
        r = c.get(url)
        r.raise_for_status()
        data = r.json()
    _CACHE_JSON[url] = (now, data)
    return data


def _sec_url(**params: str) -> str:
    return f"{SEC_BASE}?{urlencode(params)}"


# ──────────────────────────────────────────────────────────────────────────────
# Parse helpers
# ──────────────────────────────────────────────────────────────────────────────


def _parse_xml(xml_text: str) -> ET.Element:
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError:
        # Remove problematic control chars and retry
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", xml_text)
        return ET.fromstring(cleaned)


def _txt(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    if node.text:
        return node.text.strip()
    # include descendants text if present
    text = "".join(node.itertext()).strip()
    return text or None


def _parse_time(s: str | None) -> tuple[float | None, str | None]:
    if not s:
        return None, None
    # Atom uses RFC 3339/822 formats
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        dt = dt.astimezone(UTC)
        return dt.timestamp(), dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            dt = dt.astimezone(UTC)
            return dt.timestamp(), dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return None, None


_SUMMARY_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean(*, summary: str | None) -> str | None:
    if summary is None:
        return None
    s = html.unescape(summary)
    s = _SUMMARY_TAG_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s or None


_CIK_RE = re.compile(r"\bCIK[:\s]+(\d{7,10})\b", re.I)
_COMPANY_RE = re.compile(r"\bCompany[:\s]+(.+?)(?:\(|$)", re.I)


def _extract_company_and_cik(text: str) -> tuple[str, str] | None:
    """
    Returns (company, cik10) if found in the feed summary snippet.
    """
    if not text:
        return None
    m_cik = _CIK_RE.search(text)
    m_comp = _COMPANY_RE.search(text)
    cik = f"{int(m_cik.group(1)):010d}" if m_cik else None
    company = m_comp.group(1).strip() if m_comp else None
    if cik or company:
        return (company, cik or None)
    return None


# Common accession patterns present in feed title or link paths
_ACC_RE = re.compile(r"(\d{10})-?(\d{2})-?(\d{6})")


def _extract_accession(s: str) -> str | None:
    m = _ACC_RE.search(s or "")
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def _form_match(form: str | None, wanted: Iterable[str]) -> bool:
    if not wanted:
        return True
    if not form:
        return False
    # Exact (case-sensitive) first
    if form in wanted:
        return True
    # Case-insensitive fallback
    up = form.upper()
    return any((w or "").upper() == up for w in wanted)


def _filter_forms(items: list[Filing], forms: Iterable[str] | None) -> list[Filing]:
    wanted = list(forms) if forms else []
    if not wanted:
        return items
    return [f for f in items if _form_match(f.form, wanted)]


def _dedupe_filings(items: list[Filing]) -> list[Filing]:
    seen = {}
    for f in items:
        key = f.accession or f.link or f.title or ""
        if key not in seen:
            seen[key] = f
        else:
            # prefer one with ts/company/tickers if present
            cur = seen[key]
            if (f.ts or 0) > (cur.ts or 0):
                seen[key] = f
            else:
                # merge metadata
                if not cur.company and f.company:
                    cur.company = f.company
                if not cur.cik and f.cik:
                    cur.cik = f.cik
                if not cur.tickers and f.tickers:
                    cur.tickers = f.tickers
    out = list(seen.values())
    out.sort(key=lambda x: x.ts or 0, reverse=True)
    return out


def _to_filing(obj: Any) -> Filing:
    if isinstance(obj, Filing):
        return obj
    return Filing(
        cik=obj.get("cik"),
        company=obj.get("company"),
        tickers=list(obj.get("tickers") or []),
        form=obj.get("form"),
        title=obj.get("title"),
        summary=obj.get("summary"),
        filed=obj.get("filed"),
        ts=obj.get("ts"),
        accession=obj.get("accession"),
        link=obj.get("link"),
    )


def _pack(items: list[Filing]) -> dict[str, Any]:
    return {
        "asof": time.time(),
        "count": len(items),
        "items": [asdict(i) for i in items],
    }
