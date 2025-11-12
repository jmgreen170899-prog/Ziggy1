# backend/app/services/news.py
from __future__ import annotations

import hashlib
import html
import os
import re
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

import httpx


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────


def fetch_and_unify(
    feed_urls: Iterable[str],
    *,
    per_feed: int = 30,
    limit_total: int = 100,
    timeout: float = 12.0,
    ttl: int = 300,
) -> dict[str, Any]:
    """
    Fetch multiple RSS/Atom feeds and return a unified payload:
    {
      "asof": <epoch>,
      "count": <int>,
      "items": [
        {
          "id": "sha1-…",            # stable id (prefers feed guid/id, else sha1(link|title))
          "source": "Financial Times",
          "source_url": "https://www.ft.com/…",  # feed URL (not item)
          "title": "Headline…",
          "url": "https://…",
          "summary": "plain text summary",
          "image": "https://…",      # if provided in media tags (may be None)
          "published": "2025-01-15T13:20:05Z",
          "ts": 1736947205,          # epoch seconds
          "tickers": ["AAPL","MSFT"] # quick-and-dirty symbol hints ($AAPL, NASDAQ:AAPL, etc.)
        },
        …
      ]
    }
    """
    now = time.time()
    items: list[dict[str, Any]] = []

    for url in _uniq([u for u in (feed_urls or []) if isinstance(u, str) and u.strip()]):
        try:
            feed = _fetch_feed(url, timeout=timeout, ttl=ttl)
            parsed = _parse_feed(feed.xml, feed_url=url)
            # tag source on each item
            for e in parsed.entries[: max(1, per_feed)]:
                e.source = parsed.title or e.source or _guess_source_from_url(url)
                e.source_url = url
                items.append(asdict(e))
        except Exception as e:
            # Soft-fail per feed; continue with others
            items.append(_error_item(url, str(e)))

    # De-dupe by URL+title, prefer newer timestamps
    items = _dedupe_sorted(items)

    if limit_total and limit_total > 0:
        items = items[:limit_total]

    return {"asof": now, "count": len(items), "items": items}


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class NewsItem:
    id: str
    source: str | None
    source_url: str | None
    title: str
    url: str
    summary: str | None
    image: str | None
    published: str | None  # ISO8601 Z
    ts: float | None
    tickers: list[str]


@dataclass
class ParsedFeed:
    title: str | None
    entries: list[NewsItem]


@dataclass
class RawFeed:
    url: str
    xml: str
    fetched_at: float


# ──────────────────────────────────────────────────────────────────────────────
# Fetch (with tiny in-memory TTL cache)
# ──────────────────────────────────────────────────────────────────────────────

_CACHE: dict[str, tuple[float, str]] = {}  # {url: (fetched_ts, xml)}
_DEFAULT_UA = os.getenv("USER_AGENT", "ZiggyRSS/1.0 (+https://example.local)")


def _fetch_feed(url: str, *, timeout: float, ttl: int) -> RawFeed:
    now = time.time()
    cached = _CACHE.get(url)
    if cached and (now - cached[0] < max(10, int(ttl))):
        return RawFeed(url=url, xml=cached[1], fetched_at=cached[0])

    headers = {
        "User-Agent": _DEFAULT_UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
    }
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as c:
        r = c.get(url)
        r.raise_for_status()
        xml = r.text

    _CACHE[url] = (now, xml)
    return RawFeed(url=url, xml=xml, fetched_at=now)


# ──────────────────────────────────────────────────────────────────────────────
# Parse RSS/Atom
# ──────────────────────────────────────────────────────────────────────────────

_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def _parse_feed(xml_text: str, *, feed_url: str) -> ParsedFeed:
    # Some feeds include invalid chars; be defensive
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        # Try to strip control chars and retry
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", xml_text)
        root = ET.fromstring(cleaned)

    tag = _local(root.tag).lower()

    if tag == "rss" or tag == "rdf":
        title = _text_or_none(root.find("./channel/title"))
        entries = _parse_rss_items(root, base=feed_url)
    elif tag == "feed":  # Atom
        title = _text_or_none(root.find("./atom:title", _NS)) or _text_or_none(root.find("./title"))
        entries = _parse_atom_entries(root, base=feed_url)
    else:
        # Unknown root — try both ways
        title = _text_or_none(root.find(".//channel/title")) or _text_or_none(root.find(".//title"))
        entries = _parse_rss_items(root, base=feed_url) or _parse_atom_entries(root, base=feed_url)

    return ParsedFeed(title=title, entries=entries)


def _parse_rss_items(root: ET.Element, *, base: str) -> list[NewsItem]:
    items = root.findall(".//item")
    out: list[NewsItem] = []
    for it in items:
        title = _text_or_none(it.find("title")) or "(no title)"
        link = _text_or_none(it.find("link")) or _text_or_none(it.find("./guid")) or ""
        link = urljoin(base, link) if link else ""

        # time
        pub = (
            _text_or_none(it.find("pubDate"))
            or _text_or_none(it.find("dc:date", _NS))
            or _text_or_none(it.find("date"))
        )
        ts, iso = _parse_when(pub)

        # summary/content
        summary = (
            _text_or_none(it.find("description"))
            or _text_or_none(it.find("content:encoded", _NS))
            or _text_or_none(it.find("summary"))
        )
        summary = _clean_text(summary)

        # media image
        image = _first_attr(
            it,
            [
                ("media:content", "url"),
                ("media:thumbnail", "url"),
                ("image", "href"),
                ("image", "url"),
            ],
        )

        # id
        guid = _text_or_none(it.find("guid"))
        ident = _stable_id(guid, link, title)

        out.append(
            NewsItem(
                id=ident,
                source=None,
                source_url=None,
                title=_clean_text(title),
                url=link,
                summary=summary,
                image=image,
                published=iso,
                ts=ts,
                tickers=_extract_tickers(title, summary),
            )
        )
    # Sort newest first
    out.sort(key=lambda x: (x.ts or 0), reverse=True)
    return out


def _parse_atom_entries(root: ET.Element, *, base: str) -> list[NewsItem]:
    entries = root.findall(".//atom:entry", _NS) or root.findall(".//entry")
    out: list[NewsItem] = []
    for en in entries:
        title = (
            _text_or_none(en.find("atom:title", _NS))
            or _text_or_none(en.find("title"))
            or "(no title)"
        )

        # Atom links
        link = ""
        for ln in en.findall("atom:link", _NS) or en.findall("link"):
            href = (ln.attrib.get("href") or "").strip()
            rel = (ln.attrib.get("rel") or "alternate").strip().lower()
            if href and (rel in ("alternate", "canonical") or not rel):
                link = href
                break
            if href and not link:
                link = href
        link = urljoin(base, link) if link else ""

        # time
        pub = (
            _text_or_none(en.find("atom:published", _NS))
            or _text_or_none(en.find("atom:updated", _NS))
            or _text_or_none(en.find("published"))
            or _text_or_none(en.find("updated"))
        )
        ts, iso = _parse_when(pub)

        # summary/content
        summary = (
            _text_or_none(en.find("atom:summary", _NS))
            or _text_or_none(en.find("summary"))
            or _text_or_none(en.find("atom:content", _NS))
            or _text_or_none(en.find("content"))
        )
        summary = _clean_text(summary)

        # media image (common Atom patterns)
        image = _first_attr(
            en,
            [
                ("media:content", "url"),
                ("media:thumbnail", "url"),
            ],
        )

        # id
        guid = _text_or_none(en.find("atom:id", _NS)) or _text_or_none(en.find("id"))
        ident = _stable_id(guid, link, title)

        out.append(
            NewsItem(
                id=ident,
                source=None,
                source_url=None,
                title=_clean_text(title),
                url=link,
                summary=summary,
                image=image,
                published=iso,
                ts=ts,
                tickers=_extract_tickers(title, summary),
            )
        )

    out.sort(key=lambda x: (x.ts or 0), reverse=True)
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _uniq(seq: Iterable[str]) -> list[str]:
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _local(tag: str) -> str:
    # Strip namespace: '{ns}tag' -> 'tag'
    if not tag:
        return ""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _text_or_none(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    text = node.text or "".join(node.itertext()) or None
    return text.strip() if text else None


def _parse_when(s: str | None) -> tuple[float | None, str | None]:
    if not s:
        return None, None
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        dt_utc = dt.astimezone(UTC)
        ts = dt_utc.timestamp()
        return ts, dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        # Try ISO-ish fallback
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            dt_utc = dt.astimezone(UTC)
            return dt_utc.timestamp(), dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return None, None


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean_text(s: str | None) -> str | None:
    if s is None:
        return None
    s = html.unescape(s)
    s = _TAG_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s or None


def _first_attr(node: ET.Element, paths: list[tuple[str, str]]) -> str | None:
    for tag, attr in paths:
        # support namespaces like media:content
        if ":" in tag:
            pfx, local = tag.split(":", 1)
            ns = _NS.get(pfx)
            if ns:
                q = f".//{{{ns}}}{local}"
                el = node.find(q)
                if el is not None and el.attrib.get(attr):
                    return el.attrib[attr]
        # raw tag
        el = node.find(f".//{tag}")
        if el is not None and el.attrib.get(attr):
            return el.attrib[attr]
    return None


_TICK_RE = re.compile(
    r"(?:(?<=\s)|^)(?:\$([A-Z]{1,5})(?:\b)|(?:NASDAQ|NYSE|AMEX|OTC|LSE):\s*([A-Z]{1,5}))"
)


def _extract_tickers(title: str | None, summary: str | None) -> list[str]:
    text = " ".join([t for t in [title, summary] if t]) + " "
    found = set()
    for m in _TICK_RE.finditer(text):
        sym = (m.group(1) or m.group(2) or "").strip().upper()
        if 1 <= len(sym) <= 5:
            found.add(sym)
    return sorted(found)


def _stable_id(guid: str | None, link: str, title: str) -> str:
    base = (guid or "").strip() or link or title
    h = hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest()
    return f"sha1:{h}"


def _guess_source_from_url(feed_url: str) -> str:
    try:
        host = re.sub(r"^https?://", "", feed_url).split("/", 1)[0]
        return host.lower()
    except Exception:
        return "feed"


def _dedupe_sorted(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Keep the newest by (url|title) key; remove error items if we have real ones.
    bykey: dict[str, dict[str, Any]] = {}
    for it in items:
        key = (it.get("url") or "") + "||" + (it.get("title") or "")
        prev = bykey.get(key)
        if prev is None or (it.get("ts") or 0) > (prev.get("ts") or 0):
            bykey[key] = it

    out = list(bykey.values())
    out.sort(key=lambda x: (x.get("ts") or 0), reverse=True)
    return out


def _error_item(feed_url: str, reason: str) -> dict[str, Any]:
    ident = _stable_id(None, feed_url, reason)
    return {
        "id": ident,
        "source": _guess_source_from_url(feed_url),
        "source_url": feed_url,
        "title": f"[feed error] {feed_url}",
        "url": feed_url,
        "summary": reason,
        "image": None,
        "published": None,
        "ts": None,
        "tickers": [],
        "error": True,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Example default feeds (optional helper)
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_MARKETS_FEEDS: list[str] = [
    # General markets/business
    "https://www.reuters.com/finance/markets/rss",  # Reuters (markets)
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",  # WSJ Markets (public RSS headline feed)
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # CNBC Top News & Analysis
    "https://www.coindesk.com/arc/outboundfeeds/rss/",  # CoinDesk
    # Note: FT premium content doesn't offer a free, full RSS—avoid or expect partial.
]


def get_default_news(*, limit_total: int = 100) -> dict[str, Any]:
    """
    Convenience wrapper to fetch a sensible default list of feeds.
    """
    return fetch_and_unify(DEFAULT_MARKETS_FEEDS, per_feed=30, limit_total=limit_total)
