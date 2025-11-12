# isort: skip_file
# backend/app/api/routes_news.py
from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

# Optional sandbox provider (fixtures via provider_factory)
try:
    from app.services.provider_factory import get_news_provider  # type: ignore

    _NEWS_SANDBOX = get_news_provider
except Exception:
    _NEWS_SANDBOX = None  # type: ignore


# Market Brain Integration
try:
    from app.services.market_brain.simple_data_hub import DataSource, enhance_market_data

    BRAIN_AVAILABLE = True
    _enhance_market_data = enhance_market_data
    _DataSource = DataSource
except ImportError:
    BRAIN_AVAILABLE = False
    _enhance_market_data = None
    _DataSource = None

router = APIRouter()

# ──────────────────────────────────────────────────────────────────────────────
# Simple in-memory cache (per-feed + per-response), TTL from CACHE_TTL_SECONDS
# ──────────────────────────────────────────────────────────────────────────────
_TTL = int(os.getenv("CACHE_TTL_SECONDS", "60") or "60")
_CACHE: dict[str, dict[str, Any]] = {}  # { key: { "ts": float, "data": any } }


def _cache_get(key: str):
    e = _CACHE.get(key)
    if not e:
        return None
    if time.time() - e.get("ts", 0) > _TTL:
        _CACHE.pop(key, None)
        return None
    return e.get("data")


def _cache_put(key: str, data: Any):
    _CACHE[key] = {"ts": time.time(), "data": data}
    return data


# ──────────────────────────────────────────────────────────────────────────────
# Small helpers
# ──────────────────────────────────────────────────────────────────────────────


def _split_csv(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def _try_import_news_funcs():
    """
    Be tolerant about function names from app.services.news.
    Expected implementations (any of these):
      - get_headlines(...) OR fetch_headlines(...) OR headlines(...)
      - get_sources() OR list_sources() OR default_sources()
    """
    try:
        import importlib

        mod = importlib.import_module("app.services.news")
    except Exception:
        return None, None

    get_sources = None
    for name in ("get_sources", "list_sources", "default_sources"):
        if hasattr(mod, name) and callable(getattr(mod, name)):
            get_sources = getattr(mod, name)
            break

    get_headlines = None
    for name in ("get_headlines", "fetch_headlines", "headlines"):
        if hasattr(mod, name) and callable(getattr(mod, name)):
            get_headlines = getattr(mod, name)
            break

    return get_sources, get_headlines


def _try_import_filings_funcs():
    """
    Be tolerant about function names from app.services.filings.
    Expected implementations (any of these):
      - get_recent_filings(...) OR recent_filings(...) OR fetch_filings(...)
    """
    try:
        import importlib

        mod = importlib.import_module("app.services.filings")
    except Exception:
        return None

    for name in ("get_recent_filings", "recent_filings", "fetch_filings"):
        if hasattr(mod, name) and callable(getattr(mod, name)):
            return getattr(mod, name)

    return None


def _try_import_nlp_analyzer() -> Callable[..., Any] | None:
    """
    Try to import a sentiment analyzer from app.services.news_nlp (new).
    Accept several function names, prefer article-aware variants.
    """
    try:
        import importlib

        mod = importlib.import_module("app.services.news_nlp")
    except Exception:
        return None

    for name in (
        "analyze_news_sentiment",  # preferred: (ticker:str, items:list[dict]) -> dict
        "news_sentiment",
        "get_news_sentiment",
        "analyze_news",
        "analyze_sentiment",
        "analyze",
        "score",  # catch-all
    ):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Built-in RSS defaults (no keys). NEWS_RSS_EXTRA may append CSV URLs.
# ──────────────────────────────────────────────────────────────────────────────
def _default_sources() -> list[dict[str, str]]:
    base = [
        {
            "id": "reuters-markets",
            "label": "Reuters Markets",
            "url": "https://www.reuters.com/markets/rss",
        },
        {
            "id": "reuters-business",
            "label": "Reuters Business",
            "url": "https://www.reuters.com/finance/rss",
        },
        {
            "id": "yahoo-finance",
            "label": "Yahoo Finance",
            "url": "https://finance.yahoo.com/news/rssindex",
        },
        {
            "id": "npr-business",
            "label": "NPR Business",
            "url": "https://feeds.npr.org/1006/rss.xml",
        },
        {
            "id": "cnbc-top",
            "label": "CNBC Top News",
            "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        },
    ]
    extra = os.getenv("NEWS_RSS_EXTRA", "")
    for i, u in enumerate(_split_csv(extra), start=1):
        base.append({"id": f"extra-{i}", "label": f"Extra {i}", "url": u})
    return base


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(s: str | None) -> str:
    if not s:
        return ""
    # Unescape &strip tags and condense whitespace
    s = html.unescape(str(s))
    s = _TAG_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _pick_text(elem: ET.Element, *tags: str) -> str:
    for t in tags:
        x = elem.find(t)
        if x is not None and (x.text or "").strip():
            return _strip_html(x.text)
    return ""


def _pick_link(elem: ET.Element) -> str:
    # RSS: <link>https://...</link>
    ln = elem.find("link")
    if ln is not None:
        # Atom: <link href="..."/>
        href = ln.attrib.get("href")
        if href:
            return href.strip()
        if ln.text:
            return ln.text.strip()
    # Alternate form
    alt = elem.find("atom:link")
    if alt is not None:
        href = alt.attrib.get("href")
        if href:
            return href.strip()
    return ""


def _pick_published(elem: ET.Element) -> str | None:
    # Try Atom first
    for tag in ("updated", "published"):
        x = elem.find(tag)
        if x is not None and (x.text or "").strip():
            try:
                txt = x.text or ""
                # Many Atom feeds are ISO 8601
                dtv = datetime.fromisoformat(txt.replace("Z", "+00:00"))
                return dtv.astimezone(UTC).isoformat().replace("+00:00", "Z")
            except Exception:
                pass
    # RSS
    x = elem.find("pubDate")
    if x is not None and (x.text or "").strip():
        try:
            txt = x.text or ""
            dtv = parsedate_to_datetime(txt)
            if not dtv.tzinfo:
                dtv = dtv.replace(tzinfo=UTC)
            return dtv.astimezone(UTC).isoformat().replace("+00:00", "Z")
        except Exception:
            return None
    return None


def _host_from_url(url: str) -> str:
    try:
        from urllib.parse import urlparse

        netloc = urlparse(url).netloc or ""
        return netloc.replace("www.", "")
    except Exception:
        return ""


def _favicon_from_url(url: str) -> str | None:
    try:
        from urllib.parse import urlparse

        u = urlparse(url)
        if not u.scheme or not u.netloc:
            return None
        return f"{u.scheme}://{u.netloc}/favicon.ico"
    except Exception:
        return None


def _fetch_feed(url: str) -> list[dict[str, Any]]:
    """
    Fetch + parse an RSS/Atom feed with stdlib only. Returns list of items:
      { source, title, url, published, summary, image? }
    """
    cache_key = f"feed:{url}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ziggy-rss/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        # Parse XML (tolerant-ish)
        root = ET.fromstring(data)
    except Exception:
        return _cache_put(cache_key, [])

    # Namespaces (best-effort)
    # Allow bare tags too by not qualifying lookups.
    channel = root.find("channel")
    items: list[dict[str, Any]] = []
    if channel is not None:
        # RSS
        for it in channel.findall("item"):
            title = _pick_text(it, "title")
            link = _pick_link(it)
            pub = _pick_published(it)
            summary = _pick_text(it, "description", "summary")
            items.append({"title": title, "url": link, "published": pub, "summary": summary})
    else:
        # Atom
        for it in root.findall(".//entry"):
            title = _pick_text(it, "title")
            link = _pick_link(it)
            pub = _pick_published(it)
            summary = _pick_text(it, "summary", "content")
            items.append({"title": title, "url": link, "published": pub, "summary": summary})

    return _cache_put(cache_key, items)


# ──────────────────────────────────────────────────────────────────────────────
# Routes: Sources
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/news/sources")
def news_sources():
    """
    Return the configured/default RSS sources.
    Shape:
      { "asof": <epoch>, "sources": [ { "id","label","url" }, ... ] }
    """
    # Sandbox fixtures take precedence when available
    if callable(_NEWS_SANDBOX):
        try:
            prov = _NEWS_SANDBOX()
            if prov is not None and hasattr(prov, "list_sources"):
                sources = prov.list_sources()
                return {"asof": time.time(), "sources": sources}
        except Exception:
            pass
    # Prefer service override if available, else built-ins (+ NEWS_RSS_EXTRA)
    get_sources, _ = _try_import_news_funcs()
    try:
        sources = get_sources() if get_sources else _default_sources()
        return {"asof": time.time(), "sources": sources}
    except Exception:
        return {"asof": time.time(), "sources": _default_sources()}


# ──────────────────────────────────────────────────────────────────────────────
# Routes: Headlines
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/news/headlines")
def news_headlines(
    # NEW: compatibility with UI calling ?symbol=SYM
    symbol: str | None = Query(None, description="Single ticker (compat)"),
    symbols: str | None = Query(
        None, description="Comma-separated tickers to match in title/summary (e.g., AAPL,MSFT)"
    ),
    q: str | None = Query(
        None, description="Keyword filter (case-insensitive) across title/summary"
    ),
    sources: str | None = Query(
        None, description="Comma-separated source IDs or URLs; defaults to the service's built-ins"
    ),
    lookback_days: int = Query(
        3, ge=1, le=30, description="Limit items to roughly the last N days (as supported by feeds)"
    ),
    limit: int = Query(
        30, ge=1, le=200, description="Max items after merge & sort (freshest first)"
    ),
):
    """
    Unified RSS headlines (no paid keys). De-duplicates and normalizes fields.
    Response shape:
      {
        "asof": <epoch>,
        "count": <int>,
        "items": [
          {
            "id": "<stable-id>",
            "source": "Reuters Markets",
            "site": "reuters.com",
            "title": "...",
            "url": "https://...",
            "published": "2025-01-12T13:45:00Z",
            "date": "2025-01-12T13:45:00Z",   # alias for convenience
            "summary": "...",
            "tickers": ["AAPL", "MSFT"],
            "symbols": ["AAPL", "MSFT"],      # alias for convenience
            "favicon": "https://.../favicon.ico",
            # NEW (non-breaking): when available we include per-headline sentiment
            # "score": float in [-1,1], "label": "positive"|"neutral"|"negative"
          }, ...
        ]
      }
    """
    # Build a cache key for the whole request (filters affect results)
    _sym_list = _split_csv(symbols)
    if symbol and symbol.strip():
        _sym_list = [symbol.strip(), *_sym_list]
    _src_list = _split_csv(sources)
    req_key = json.dumps(
        {
            "sym": _sym_list,
            "q": (q or "").strip().lower(),
            "src": _src_list,
            "lb": lookback_days,
            "lim": limit,
        },
        sort_keys=True,
    )
    cached = _cache_get(f"headlines:{req_key}")
    if cached is not None:
        return cached

    # Sandbox fixtures take precedence when available
    if callable(_NEWS_SANDBOX):
        try:
            prov = _NEWS_SANDBOX()
            if prov is not None and hasattr(prov, "get_headlines"):
                data = prov.get_headlines(
                    symbols=_sym_list,
                    q=q,
                    sources=_src_list if _src_list else None,
                    lookback_days=lookback_days,
                    limit=limit,
                )
                return _cache_put(f"headlines:{req_key}", data)
        except Exception:
            pass

    # Resolve source list: allow IDs or direct URLs
    try:
        default_sources = _default_sources()
        id_map = {s["id"]: s for s in default_sources}
        use_sources: list[dict[str, str]] = []
        if _src_list:
            for token in _src_list:
                if token in id_map:
                    use_sources.append(id_map[token])
                elif token.startswith("http"):
                    use_sources.append({"id": token, "label": token, "url": token})
        else:
            use_sources = default_sources

        # Allow service override/augmentation if present
        _, svc_headlines = _try_import_news_funcs()
        svc_items: list[dict[str, Any]] = []
        if svc_headlines:
            try:
                svc_items = (
                    svc_headlines(
                        symbols=(_sym_list or None),
                        q=(q or None),
                        sources=[s["url"] for s in use_sources],
                        lookback_days=lookback_days,
                        limit=limit,
                    )
                    or []
                )
                if not isinstance(svc_items, list):
                    svc_items = (svc_items or {}).get("items", [])
            except Exception:
                svc_items = []

        # Fetch & merge RSS (built-in)
        merged: list[dict[str, Any]] = []
        now = datetime.now(UTC)
        min_dt = now - timedelta(days=lookback_days)
        sym_set = {s.upper() for s in _sym_list}
        q_lc = (q or "").strip().lower()
        seen_urls: set[str] = set()

        for src in use_sources:
            items = _fetch_feed(src["url"])
            for it in items:
                url = it.get("url") or ""
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                title = _strip_html(it.get("title"))
                summary = _strip_html(it.get("summary"))
                pub_iso = it.get("published")
                # Filter by lookback
                if pub_iso:
                    try:
                        dt = datetime.fromisoformat(pub_iso.replace("Z", "+00:00"))
                    except Exception:
                        dt = None
                    if dt and dt < min_dt:
                        continue

                # Filters: symbols & keywords
                blob = f"{title} {summary}".lower()
                if q_lc and q_lc not in blob:
                    continue
                matched_syms = sorted([s for s in sym_set if s and s in blob]) if sym_set else []
                if sym_set and not matched_syms:
                    continue

                # ── NEW: per-headline sentiment (fallback/naive) ───────────────
                sc = _naive_sentiment_score(f"{title}. {summary}".strip())
                lb = "negative" if sc < -0.05 else "positive" if sc > 0.05 else "neutral"

                merged.append(
                    {
                        "id": url,  # stable enough
                        "source": src["label"],
                        "site": _host_from_url(url),
                        "title": title,
                        "url": url,
                        "published": pub_iso,
                        "date": pub_iso,  # alias for UI convenience
                        "summary": summary,
                        "tickers": matched_syms,
                        "symbols": matched_syms,  # alias for UI convenience
                        "favicon": _favicon_from_url(url),
                        "source_id": src.get("id"),
                        # NEW: add sentiment so the UI can color-score headlines
                        "score": sc,
                        "label": lb,
                    }
                )

        # Merge with service items (if any), favoring most recent
        if svc_items:
            for it in svc_items:
                url = (it.get("url") or it.get("link") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                pub = it.get("published") or it.get("date")
                title = _strip_html(it.get("title"))
                summary = _strip_html(it.get("summary") or it.get("description"))
                # Build symbols/tickers set
                svc_syms = it.get("symbols") or it.get("tickers") or it.get("related") or []
                if isinstance(svc_syms, str):
                    svc_syms = _split_csv(svc_syms)
                svc_syms = [str(s).upper() for s in (svc_syms or [])]

                # Preserve any provider sentiment keys if present; otherwise compute locally
                # We DO NOT rename existing keys; we only add "score"/"label" when absent.
                sc: float
                val_any = it.get("score", None)
                if isinstance(val_any, (int, float)):
                    sc = float(val_any)
                else:
                    val_any = it.get("sentiment_score", None)
                    if isinstance(val_any, (int, float)):
                        sc = float(val_any)
                    else:
                        val_any = it.get("sentiment", None)
                        if isinstance(val_any, (int, float)):
                            sc = float(val_any)
                        else:
                            val_any = it.get("compound", None)
                            if isinstance(val_any, (int, float)):
                                sc = float(val_any)
                            else:
                                sc = _naive_sentiment_score(f"{title}. {summary}".strip())

                if "label" in it and isinstance(it.get("label"), str):
                    lb = str(it.get("label")).lower()
                elif "sentiment_label" in it and isinstance(it.get("sentiment_label"), str):
                    lb = str(it.get("sentiment_label")).lower()
                elif "sentimentLabel" in it and isinstance(it.get("sentimentLabel"), str):
                    lb = str(it.get("sentimentLabel")).lower()
                else:
                    lb = "negative" if sc < -0.05 else "positive" if sc > 0.05 else "neutral"

                merged.append(
                    {
                        "id": url,
                        "source": it.get("source") or it.get("publisher") or "news",
                        "site": _host_from_url(url),
                        "title": title,
                        "url": url,
                        "published": pub,
                        "date": pub,
                        "summary": summary,
                        "tickers": svc_syms,
                        "symbols": svc_syms,
                        "favicon": _favicon_from_url(url),
                        "source_id": it.get("source_id"),
                        # NEW: ensure per-headline sentiment fields exist
                        "score": sc,
                        "label": lb,
                        # Also pass-through any original sentiment keys unmodified
                        **(
                            {
                                k: it[k]
                                for k in (
                                    "sentiment",
                                    "sentiment_score",
                                    "sentimentScore",
                                    "sentiment_label",
                                    "sentimentLabel",
                                    "confidence",
                                    "prob",
                                    "probability",
                                    "softmax",
                                    "updated_at",
                                    "asof",
                                    "as_of",
                                    "samples",
                                    "sample_count",
                                    "n",
                                    "compound",
                                )
                                if k in it
                            }
                        ),
                    }
                )

        # Sort newest first
        def _key(x: dict[str, Any]):
            p = x.get("published")
            try:
                return datetime.fromisoformat((p or "").replace("Z", "+00:00"))
            except Exception:
                return datetime.min.replace(tzinfo=UTC)

        merged.sort(key=_key, reverse=True)
        merged = merged[:limit]

        resp = {"asof": time.time(), "count": len(merged), "items": merged}

        # Enhance with market brain intelligence
        if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
            resp = _enhance_market_data(resp, _DataSource.NEWS, symbols=symbols)

        return _cache_put(f"headlines:{req_key}", resp)
    except Exception as e:
        # Keep the UI resilient
        return {"asof": time.time(), "count": 0, "items": [], "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# Routes: SEC Filings (free)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/news/filings")
def news_filings(
    symbols: str | None = Query(
        None,
        description="Comma-separated tickers (e.g., AAPL,MSFT). If omitted, a small default universe may be used.",
    ),
    forms: str | None = Query(
        "10-K,10-Q,8-K",
        description="Comma-separated SEC form codes to include (e.g., 10-K,10-Q,8-K,13F,S-1).",
    ),
    limit: int = Query(30, ge=1, le=200),
):
    """
    Recent SEC filings via the free SEC Atom feed.

    Response shape:
      {
        "asof": <epoch>,
        "count": n,
        "items": [
          {
            "ticker": "AAPL",
            "cik": "0000320193",
            "form": "8-K",
            "filed": "2025-01-12T21:10:00Z",
            "title": "Apple Inc - 8-K",
            "link": "https://www.sec.gov/Archives/edgar/data/...",
            "description": "...",   # optional
          }, ...
        ]
      }
    """
    fetch_filings = _try_import_filings_funcs()
    if not fetch_filings:
        return {
            "asof": time.time(),
            "count": 0,
            "items": [],
            "error": "filings service not available",
        }

    try:
        sym_list = _split_csv(symbols)
        form_list = _split_csv(forms) or None

        items = fetch_filings(
            symbols=sym_list or None,
            forms=form_list,
            limit=limit,
        )
        if not isinstance(items, list):
            items = (items or {}).get("items", [])

        items = list(items)[:limit]
        resp = {"asof": time.time(), "count": len(items), "items": items}

        # Enhance with market brain intelligence
        if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
            resp = _enhance_market_data(resp, _DataSource.NEWS, symbols=sym_list)

        return resp
    except Exception as e:
        return {"asof": time.time(), "count": 0, "items": [], "error": str(e)}


# NEW: compatibility alias the UI expects: /news/filings/recent?ticker=SYM&limit=5
@router.get("/news/filings/recent")
def news_filings_recent(
    ticker: str | None = Query(None, description="Single ticker (compat)"),
    limit: int = Query(5, ge=1, le=200),
):
    """
    Compatibility wrapper for `/news/filings` so the UI can call:
      /news/filings/recent?ticker=SYM&limit=5
    """
    if not ticker:
        return {"asof": time.time(), "count": 0, "items": []}
    # Delegate to the main endpoint logic
    return news_filings(symbols=ticker, limit=limit)  # type: ignore[arg-type]


# ──────────────────────────────────────────────────────────────────────────────
# NEW: NLP sentiment / "news headwind"
# ──────────────────────────────────────────────────────────────────────────────


def _naive_sentiment_score(text: str) -> float:
    """
    Very small lexicon-based fallback. Returns score in [-1, 1].
    """
    if not text:
        return 0.0
    t = text.lower()
    # Tiny curated word lists; intentionally minimal and finance-tilted
    neg = [
        "miss",
        "probe",
        "investigate",
        "investigation",
        "SEC",
        "doj",
        "antitrust",
        "shortfall",
        "recall",
        "layoff",
        "cut",
        "decline",
        "slump",
        "plunge",
        "drop",
        "falls",
        "falling",
        "跌",
        "亏损",
        "downgrade",
        "warning",
        "headwind",
        "pressure",
        "delay",
        "halt",
        "ban",
        "penalty",
        "fine",
        "loss",
        "loses",
        "lawsuit",
        "sue",
        "allege",
        "allegation",
        "breach",
        "breaches",
        "fraud",
        "scandal",
        "negative",
        "negatively",
        "weak",
        "weakness",
        "slowdown",
        "recession",
        "default",
        "bankruptcy",
        "insolvency",
        "fire",
        "probe",
    ]
    pos = [
        "beat",
        "beats",
        "exceeds",
        "exceed",
        "upgrade",
        "record",
        "soar",
        "rally",
        "rises",
        "rise",
        "gain",
        "gains",
        "growing",
        "growth",
        "positive",
        "positively",
        "profit",
        "profitable",
        "strong",
        "strength",
        "accelerate",
        "acceleration",
        "uptrend",
        "tailwind",
        "approval",
        "approved",
        "wins",
        "win",
    ]
    score = 0
    for w in neg:
        if not w:
            continue
        if f" {w} " in f" {t} ":
            score -= 1
    for w in pos:
        if not w:
            continue
        if f" {w} " in f" {t} ":
            score += 1
    if score == 0:
        return 0.0
    # squish to [-1,1]
    if score > 0:
        return min(1.0, 0.2 * score)
    return max(-1.0, 0.2 * score)


def _aggregate_sentiment(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate per-article scores to a compact summary.
    """
    if not samples:
        return {
            "score": 0.0,
            "label": "neutral",
            "confidence": 0.0,
            "sample_count": 0,
            "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "samples": [],
        }
    scores = [s.get("score", 0.0) for s in samples]
    score = sum(scores) / max(1, len(scores))
    label = "negative" if score < -0.05 else "positive" if score > 0.05 else "neutral"
    # crude confidence by |score| and sample size (capped)
    confidence = min(1.0, abs(score) * 1.5 + (len(samples) / 50.0))
    return {
        "score": float(score),
        "label": label,
        "confidence": float(confidence),
        "sample_count": len(samples),
        "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "samples": samples,
    }


def _compute_sentiment_locally(ticker: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    for it in items:
        title = _strip_html(it.get("title"))
        summary = _strip_html(it.get("summary") or "")
        text = f"{title}. {summary}".strip()
        sc = _naive_sentiment_score(text)
        label = "negative" if sc < -0.05 else "positive" if sc > 0.05 else "neutral"
        samples.append(
            {
                "source": it.get("source") or "",
                "title": title,
                "url": it.get("url") or "",
                "published": it.get("published") or "",
                "score": sc,
                "label": label,
            }
        )
    agg = _aggregate_sentiment(samples)
    agg["ticker"] = ticker
    return agg


def _get_articles_for_sentiment(
    ticker: str, lookback_days: int, limit: int
) -> list[dict[str, Any]]:
    """
    Reuse the headlines route to obtain items for a single ticker.
    """
    try:
        resp = news_headlines(
            symbol=ticker,
            symbols=None,
            q=None,
            sources=None,
            lookback_days=lookback_days,
            limit=limit,
        )  # type: ignore
        items = (resp or {}).get("items", []) if isinstance(resp, dict) else []
    except Exception:
        items = []
    return items


@router.get("/news/sentiment")
def news_sentiment(
    ticker: str | None = Query(None, description="Primary ticker (alias: symbol)"),
    symbol: str | None = Query(None, description="Alias for ticker"),
    lookback_days: int = Query(3, ge=1, le=30),
    limit: int = Query(40, ge=1, le=200),
):
    """
    Return an NLP sentiment summary for recent headlines mentioning `ticker`.
    Output shape (compact, UI-friendly):
      {
        "ticker": "AAPL",
        "score": -0.18,               # mean score in [-1,1]
        "label": "negative",          # negative|neutral|positive
        "confidence": 0.66,           # heuristic 0..1
        "sample_count": 12,
        "updated_at": "2025-01-12T12:34:56Z",
        "samples": [ { title, url, published, source, score, label }, ... ]
      }
    """
    t = (ticker or symbol or "").strip().upper()
    if not t:
        raise HTTPException(status_code=400, detail="ticker (or symbol) is required")

    cache_key = f"nlp:{t}:{lookback_days}:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # Gather articles
    items = _get_articles_for_sentiment(t, lookback_days, limit)

    # If a pluggable analyzer is available, try it first
    analyzer = _try_import_nlp_analyzer()
    if analyzer:
        try:
            # Try item-aware signature first
            out = analyzer(ticker=t, items=items)  # type: ignore
        except TypeError:
            try:
                texts = [
                    f"{_strip_html(x.get('title'))}. {_strip_html(x.get('summary') or '')}"
                    for x in items
                ]
                out = analyzer(t, texts)  # type: ignore
            except Exception:
                out = None
        except Exception:
            out = None

        if isinstance(out, dict) and "score" in out and "label" in out:
            out.setdefault("ticker", t)
            out.setdefault("updated_at", datetime.now(UTC).isoformat().replace("+00:00", "Z"))
            return _cache_put(cache_key, out)

        # If analyzer returned per-sample scores, aggregate them
        if isinstance(out, list) and out:
            samples = []
            for i, s in enumerate(out):
                try:
                    sc = float(s.get("score", 0.0))
                except Exception:
                    sc = 0.0
                label = s.get("label") or (
                    "negative" if sc < -0.05 else "positive" if sc > 0.05 else "neutral"
                )
                it = items[i] if i < len(items) else {}
                samples.append(
                    {
                        "source": it.get("source") or "",
                        "title": _strip_html(it.get("title")),
                        "url": it.get("url") or "",
                        "published": it.get("published") or "",
                        "score": sc,
                        "label": str(label).lower(),
                    }
                )
            agg = _aggregate_sentiment(samples)
            agg["ticker"] = t

            # Enhance with market brain intelligence
            if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
                agg = _enhance_market_data(agg, _DataSource.NEWS, symbols=[t])

            return _cache_put(cache_key, agg)

    # Fallback: naive local scoring
    out = _compute_sentiment_locally(t, items)

    # Enhance with market brain intelligence
    if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
        out = _enhance_market_data(out, _DataSource.NEWS, symbols=[t])

    return _cache_put(cache_key, out)


# Alias for tolerant clients (frontend maps to /news/sentiment anyway, but keep this):
@router.get("/news/headwind")
def news_headwind(
    ticker: str | None = Query(None, description="Primary ticker (alias: symbol)"),
    symbol: str | None = Query(None, description="Alias for ticker"),
    lookback_days: int = Query(3, ge=1, le=30),
    limit: int = Query(40, ge=1, le=200),
):
    """
    Compatibility alias that returns the same payload as /news/sentiment.
    """
    return news_sentiment(ticker=ticker, symbol=symbol, lookback_days=lookback_days, limit=limit)  # type: ignore[arg-type]


# ──────────────────────────────────────────────────────────────────────────────
# Lightweight ping (optional)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/news/ping")
def news_ping():
    return {"status": "ok", "asof": time.time()}
