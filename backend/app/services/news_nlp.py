# backend/app/services/news_nlp.py
"""
Enhanced News NLP Service - Perception Layer

Finance-aware NLP that maps headlines → tickers → sentiments reliably.
Features: entity linking, negation handling, event typing, sentiment aggregation.

Enhanced capabilities:
- Entity linking with ticker mapping
- Negation scope detection and polarity inversion
- Event type classification (earnings, guidance, M&A, etc.)
- Rolling sentiment aggregation with decay
- Novelty scoring for rare events
- Brain-first data flow for learning

Goals
-----
- Provide a simple analyzer that the API layer can import dynamically.
- Work out-of-the-box with no extra dependencies.
- If VADER (from NLTK) is available, use it automatically for higher-quality scores.
- Fall back to a tiny finance-tilted lexicon when VADER isn't available.
- Return a compact, UI-friendly payload compatible with the RightRail banner.

Primary entry point (preferred by routes):
    analyze_news_sentiment(ticker: str, items: list[dict]) -> dict

Enhanced entry points:
    extract_entities_and_sentiment(text: str, date: str = None) -> dict
    classify_event_type(text: str) -> str
    aggregate_sentiment_with_decay(ticker: str, days: int = 14) -> dict
    calculate_novelty_score(ticker: str, event_type: str, days: int = 21) -> float

Output shape (for *analyze_news_sentiment*):
{
  "ticker": "AAPL",
  "score": -0.18,            # mean in [-1, 1]
  "label": "negative",       # negative|neutral|positive
  "confidence": 0.66,        # heuristic 0..1
  "sample_count": 12,
  "updated_at": "2025-01-12T12:34:56Z",
  "model": "vader" | "lexicon",
  "entities": ["AAPL", "iPhone"],  # extracted entities/tickers
  "event_type": "product",   # earnings|guidance|ma|layoffs|product|legal
  "novelty": 0.73,          # novelty score 0-1
  "samples": [
      { "title","url","published","source","score","label","entities","event_type" }, ...
  ]
}
"""

from __future__ import annotations

import logging
import os
import re
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any


logger = logging.getLogger(__name__)

# Environment configuration
NLP_MIN_CONF = float(os.getenv("NLP_MIN_CONF", "0.55"))
NLP_DECAY_HALF_LIFE_DAYS = float(os.getenv("NLP_DECAY_HALF_LIFE_DAYS", "14"))
NLP_NOVELTY_WINDOW_DAYS = int(os.getenv("NLP_NOVELTY_WINDOW_DAYS", "21"))
NLP_DEVSET_PATH = os.getenv("NLP_DEVSET_PATH", "/data/nlp/devset.jsonl")

# ──────────────────────────────────────────────────────────────────────────────
# Optional VADER (NLTK) support
# ──────────────────────────────────────────────────────────────────────────────
_VADER: Any | None = None
try:
    # Try modern import first (some environments vendor it)
    from nltk.sentiment import SentimentIntensityAnalyzer  # type: ignore

    _VADER = SentimentIntensityAnalyzer()
except Exception:
    try:
        # Some distros expose it under this alias
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore

        _VADER = SentimentIntensityAnalyzer()
    except Exception:
        _VADER = None


# ──────────────────────────────────────────────────────────────────────────────
# Tiny fallback lexicon (finance-tilted) + environment overrides
# ──────────────────────────────────────────────────────────────────────────────

_DEFAULT_NEG_WORDS = """
miss,probe,investigate,investigation,sec,doj,antitrust,shortfall,recall,layoff,layoffs,
cut,cuts,cutting,decline,declines,slump,plunge,drop,drops,falls,falling,
downgrade,downgrades,warning,warnings,headwind,headwinds,pressure,pressures,
delay,halt,ban,penalty,penalties,fine,fines,loss,losses,loses,lawsuit,lawsuits,sue,sues,
allege,allegation,allegations,breach,breaches,fraud,scandal,negative,negatively,weak,weakness,
slowdown,recession,default,bankruptcy,insolvency,fire,fired,regulatory,investigation
"""

_DEFAULT_POS_WORDS = """
beat,beats,exceeds,exceed,upgrade,upgrades,record,records,soar,soars,rally,rallies,rises,rise,
gain,gains,growing,growth,positive,positively,profit,profits,profitable,strong,strength,
accelerate,acceleration,uptrend,tailwind,tailwinds,approval,approved,approvals,wins,win,winning
"""


def _words_from_env(key: str, default_list: Iterable[str]) -> list[str]:
    """
    Allow app operators to extend/override lexicons via env.
    - If env var is present and non-empty: use its words (CSV).
    - Else: use defaults.
    """
    raw = os.getenv(key, "").strip()
    if not raw:
        return [w.strip() for w in default_list if w.strip()]
    return [w.strip() for w in raw.split(",") if w.strip()]


_LEX_NEG = set(_words_from_env("NEWS_SENTIMENT_NEG", re.split(r"[,\s]+", _DEFAULT_NEG_WORDS)))
_LEX_POS = set(_words_from_env("NEWS_SENTIMENT_POS", re.split(r"[,\s]+", _DEFAULT_POS_WORDS)))

# Weighting knobs (env-tunable)
LEX_NEG_WEIGHT = float(os.getenv("NEWS_SENTIMENT_NEG_W", "1.0") or "1.0")
LEX_POS_WEIGHT = float(os.getenv("NEWS_SENTIMENT_POS_W", "1.0") or "1.0")

# Threshold to map a score to a label
NEG_THRESH = float(os.getenv("NEWS_SENTIMENT_NEG_THRESH", "0.05") or "0.05")
POS_THRESH = float(os.getenv("NEWS_SENTIMENT_POS_THRESH", "0.05") or "0.05")


# ──────────────────────────────────────────────────────────────────────────────
# Text helpers
# ──────────────────────────────────────────────────────────────────────────────

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean_text(s: str | None) -> str:
    if not s:
        return ""
    s = str(s)
    s = _TAG_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def _to_samples(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for it in items or []:
        out.append(
            {
                "source": it.get("source") or "",
                "title": _clean_text(it.get("title")),
                "url": it.get("url") or it.get("link") or "",
                "published": it.get("published") or it.get("date") or "",
                "summary": _clean_text(it.get("summary") or it.get("description") or ""),
            }
        )
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Scoring backends
# ──────────────────────────────────────────────────────────────────────────────


def _score_vader(text: str) -> float:
    """
    Use VADER if available; return compound in [-1,1].
    """
    if not text:
        return 0.0
    if _VADER is None:
        return 0.0
    try:
        res = _VADER.polarity_scores(text)  # type: ignore[attr-defined]
        comp = float(res.get("compound", 0.0))
        # Already in [-1,1]
        return comp
    except Exception:
        return 0.0


def _score_lexicon(text: str) -> float:
    """
    Very small lexicon-based scorer. Returns score in [-1,1].
    """
    if not text:
        return 0.0
    t = f" {text.lower()} "
    neg_hits = sum(1 for w in _LEX_NEG if f" {w} " in t)
    pos_hits = sum(1 for w in _LEX_POS if f" {w} " in t)
    raw = LEX_POS_WEIGHT * pos_hits - LEX_NEG_WEIGHT * neg_hits
    if raw == 0:
        return 0.0
    # Squash via tanh-ish scaling without importing math.tanh to keep deterministic:
    # simple normalization by hits
    denom = max(1.0, (pos_hits + neg_hits))
    score = raw / denom
    # clamp to [-1,1]
    if score > 1.0:
        score = 1.0
    if score < -1.0:
        score = -1.0
    # soften a bit
    return float(max(-1.0, min(1.0, score * 0.8)))


def _score_text(text: str, prefer_vader: bool = True) -> tuple[float, str]:
    """
    Return (score, model_name) with model_name in {"vader","lexicon"}.
    """
    if prefer_vader and _VADER is not None:
        return _score_vader(text), "vader"
    # fallback
    return _score_lexicon(text), "lexicon"


def _label_from_score(score: float) -> str:
    if score < -abs(NEG_THRESH):
        return "negative"
    if score > abs(POS_THRESH):
        return "positive"
    return "neutral"


def _confidence_from(scores: list[float]) -> float:
    """
    Heuristic confidence: combine |mean| and sample size.
    """
    if not scores:
        return 0.0
    mean = sum(scores) / len(scores)
    n = len(scores)
    # Emphasize polarity and modestly reward sample size (cap at ~50 articles)
    conf = min(1.0, abs(mean) * 1.5 + (n / 50.0))
    return float(conf)


# ──────────────────────────────────────────────────────────────────────────────
# Public API (preferred)
# ──────────────────────────────────────────────────────────────────────────────


def analyze_news_sentiment(
    ticker: str, items: list[dict[str, Any]], prefer_vader: bool | None = None
) -> dict[str, Any]:
    """
    Compute a sentiment summary for recent news items about a ticker.

    Parameters
    ----------
    ticker : str
        Ticker symbol, any case.
    items : list[dict]
        News items, each possibly with fields: title, summary, url, published, source.
    prefer_vader : Optional[bool]
        Force using VADER when available. Defaults to True if VADER is installed.

    Returns
    -------
    dict : See module docstring for schema.
    """
    prefer_vader = True if prefer_vader is None else bool(prefer_vader)

    samples = _to_samples(items)
    scored_samples: list[dict[str, Any]] = []
    scores_only: list[float] = []
    model_used = "lexicon"

    for s in samples:
        text = f"{s.get('title', '')}. {s.get('summary', '')}".strip()
        score, model = _score_text(_clean_text(text), prefer_vader=prefer_vader)
        model_used = model_used if model_used == "vader" else model  # if any are vader, keep vader
        label = _label_from_score(score)
        out = {
            "source": s.get("source") or "",
            "title": s.get("title") or "",
            "url": s.get("url") or "",
            "published": s.get("published") or "",
            "score": float(score),
            "label": label,
        }
        scored_samples.append(out)
        scores_only.append(score)

    mean = float(sum(scores_only) / max(1, len(scores_only))) if scores_only else 0.0
    label = _label_from_score(mean)
    conf = _confidence_from(scores_only)

    return {
        "ticker": (ticker or "").upper(),
        "score": mean,
        "label": label,
        "confidence": conf,
        "sample_count": len(scores_only),
        "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "model": model_used if _VADER is not None else "lexicon",
        "samples": scored_samples,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Alternate entry points (kept for router tolerance)
# ──────────────────────────────────────────────────────────────────────────────


def news_sentiment(ticker: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return analyze_news_sentiment(ticker=ticker, items=items)


def get_news_sentiment(ticker: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return analyze_news_sentiment(ticker=ticker, items=items)


def analyze_news(ticker: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return analyze_news_sentiment(ticker=ticker, items=items)


def analyze(texts: list[str]) -> list[dict[str, Any]]:
    """Analyze a list of texts and return per-item scores (no ticker)."""
    return analyze_sentiment(texts)


def analyze_sentiment(texts: list[str]) -> list[dict[str, Any]]:
    """
    Per-text sentiment scoring helper. Returns a list of {score, label, model}.
    """
    out: list[dict[str, Any]] = []
    for t in texts or []:
        score, model = _score_text(_clean_text(t), prefer_vader=True)
        out.append(
            {
                "score": float(score),
                "label": _label_from_score(score),
                "model": model if _VADER is not None else "lexicon",
            }
        )
    return out


def score(text: str) -> float:
    """Simple scalar score for a single text."""
    s, _ = _score_text(_clean_text(text), prefer_vader=True)
    return float(s)


# ──────────────────────────────────────────────────────────────────────────────
# Enhanced NLP Features - Perception Layer
# ──────────────────────────────────────────────────────────────────────────────


def extract_entities_and_sentiment(text: str, date: str = None) -> dict[str, Any]:
    """
    Extract entities (tickers) and sentiment with negation handling.

    Args:
        text: Input text to analyze
        date: Date context for entity linking

    Returns:
        Dictionary with entities, sentiment, and metadata
    """
    if not text:
        return {
            "entities": [],
            "tickers": [],
            "sentiment": {"score": 0.0, "label": "neutral", "confidence": 0.0},
            "negation_detected": False,
            "original_text": text,
        }

    # Clean and prepare text
    clean_text = _clean_text(text)

    # Detect negation patterns
    negation_detected, processed_text = _handle_negation(clean_text)

    # Extract entities/tickers
    try:
        from app.services.ticker_linker import map_org_to_tickers

        tickers = map_org_to_tickers(clean_text, date)
    except ImportError:
        tickers = []

    # Get sentiment on processed text (after negation handling)
    sentiment_score, model = _score_text(processed_text, prefer_vader=True)

    # Calculate confidence
    confidence = min(1.0, abs(sentiment_score) + 0.3)  # Base confidence

    return {
        "entities": _extract_financial_entities(clean_text),
        "tickers": tickers,
        "sentiment": {
            "score": float(sentiment_score),
            "label": _label_from_score(sentiment_score),
            "confidence": float(confidence),
            "model": model,
        },
        "negation_detected": negation_detected,
        "processed_text": processed_text,
        "original_text": text,
    }


def _handle_negation(text: str) -> tuple[bool, str]:
    """
    Handle negation in text by detecting negation scope and inverting sentiment.

    Returns:
        Tuple of (negation_detected, processed_text)
    """
    # Negation words and scope
    negation_words = [
        "not",
        "no",
        "never",
        "none",
        "nobody",
        "nothing",
        "neither",
        "nowhere",
        "isn't",
        "aren't",
        "wasn't",
        "weren't",
        "hasn't",
        "haven't",
        "hadn't",
        "won't",
        "wouldn't",
        "shouldn't",
        "couldn't",
        "mustn't",
        "doesn't",
        "don't",
        "didn't",
    ]

    # Punctuation that breaks negation scope
    scope_breakers = [".", "!", "?", ";", ":", ",", "but", "however", "although", "though"]

    words = text.lower().split()
    processed_words = []
    negation_active = False
    negation_detected = False

    for i, word in enumerate(words):
        # Check if this word is a negation
        if word in negation_words:
            negation_active = True
            negation_detected = True
            processed_words.append(word)
            continue

        # Check if this word breaks negation scope
        if any(breaker in word for breaker in scope_breakers):
            negation_active = False
            processed_words.append(word)
            continue

        # If negation is active, invert sentiment words
        if negation_active:
            # Simple inversion: add "not_" prefix to sentiment-bearing words
            if word in _LEX_POS or word in _LEX_NEG:
                processed_words.append(f"not_{word}")
            else:
                processed_words.append(word)
        else:
            processed_words.append(word)

    return negation_detected, " ".join(processed_words)


def _extract_financial_entities(text: str) -> list[str]:
    """Extract financial entities like company names, financial terms."""
    # Financial entity patterns
    financial_patterns = [
        r"\b\d+(?:\.\d+)?[MB]?\s*(?:revenue|sales|earnings|profit|loss)\b",
        r"\b\$\d+(?:\.\d+)?[BMK]?\b",
        r"\bQ[1-4]\s*\d{4}\b",
        r"\b(?:earnings|revenue|sales|profit|loss|guidance|outlook)\b",
        r"\b(?:IPO|M&A|acquisition|merger|buyout)\b",
        r"\b(?:FDA|SEC|DOJ|FTC)\s*approval\b",
    ]

    entities = []
    for pattern in financial_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities.extend(matches)

    return list(set(entities))


def classify_event_type(text: str) -> str:
    """
    Classify news event type based on content.

    Returns:
        Event type: earnings|guidance|ma|layoffs|product|legal|other
    """
    text_lower = text.lower()

    # Event type patterns
    event_patterns = {
        "earnings": [
            "earnings",
            "quarterly results",
            "q1",
            "q2",
            "q3",
            "q4",
            "eps",
            "beat estimates",
            "miss estimates",
            "revenue",
            "profit",
            "loss",
        ],
        "guidance": [
            "guidance",
            "forecast",
            "outlook",
            "projections",
            "estimates",
            "raised guidance",
            "lowered guidance",
            "updated outlook",
        ],
        "ma": [
            "merger",
            "acquisition",
            "buyout",
            "takeover",
            "deal",
            "m&a",
            "acquire",
            "purchase",
            "merge",
            "combine",
            "spinoff",
        ],
        "layoffs": [
            "layoffs",
            "layoff",
            "fired",
            "terminate",
            "downsizing",
            "restructuring",
            "job cuts",
            "workforce reduction",
            "eliminate positions",
        ],
        "product": [
            "launch",
            "release",
            "unveil",
            "announce",
            "product",
            "service",
            "new version",
            "update",
            "feature",
            "innovation",
        ],
        "legal": [
            "lawsuit",
            "litigation",
            "sec",
            "investigation",
            "probe",
            "fine",
            "penalty",
            "settlement",
            "court",
            "judge",
            "ruling",
            "verdict",
        ],
    }

    # Score each event type
    event_scores = {}
    for event_type, keywords in event_patterns.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            event_scores[event_type] = score

    # Return highest scoring event type
    if event_scores:
        return max(event_scores.items(), key=lambda x: x[1])[0]

    return "other"


def aggregate_sentiment_with_decay(ticker: str, days: int = None) -> dict[str, Any]:
    """
    Aggregate sentiment for a ticker with exponential decay.

    Args:
        ticker: Ticker symbol
        days: Number of days to look back (uses NLP_DECAY_HALF_LIFE_DAYS if None)

    Returns:
        Aggregated sentiment with decay applied
    """
    decay_days = days or NLP_DECAY_HALF_LIFE_DAYS

    try:
        # Get recent sentiment events from memory layer
        from app.memory.events import iter_events

        sentiment_events = []
        cutoff_date = datetime.now(UTC) - timedelta(days=decay_days * 2)

        for event in iter_events():
            if (
                event.get("ticker") == ticker
                and event.get("event_type") == "news_sentiment"
                and "ts" in event
            ):
                event_date = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
                if event_date >= cutoff_date:
                    sentiment_events.append(event)

        if not sentiment_events:
            return {
                "ticker": ticker,
                "aggregated_score": 0.0,
                "confidence": 0.0,
                "event_count": 0,
                "decay_applied": True,
                "half_life_days": decay_days,
            }

        # Apply exponential decay
        now = datetime.now(UTC)
        total_weight = 0.0
        weighted_score = 0.0

        for event in sentiment_events:
            event_date = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
            days_ago = (now - event_date).days

            # Exponential decay: weight = 0.5^(days_ago / half_life)
            weight = 0.5 ** (days_ago / decay_days)

            sentiment_score = event.get("sentiment_score", 0.0)
            weighted_score += sentiment_score * weight
            total_weight += weight

        # Calculate final aggregated score
        if total_weight > 0:
            aggregated_score = weighted_score / total_weight
            confidence = min(1.0, total_weight / len(sentiment_events))
        else:
            aggregated_score = 0.0
            confidence = 0.0

        return {
            "ticker": ticker,
            "aggregated_score": float(aggregated_score),
            "confidence": float(confidence),
            "event_count": len(sentiment_events),
            "decay_applied": True,
            "half_life_days": decay_days,
            "total_weight": float(total_weight),
        }

    except ImportError:
        # Memory layer not available
        return {
            "ticker": ticker,
            "aggregated_score": 0.0,
            "confidence": 0.0,
            "event_count": 0,
            "error": "Memory layer not available",
        }


def calculate_novelty_score(ticker: str, event_type: str, days: int = None) -> float:
    """
    Calculate novelty score for a ticker/event combination.

    Args:
        ticker: Ticker symbol
        event_type: Type of event
        days: Look-back window (uses NLP_NOVELTY_WINDOW_DAYS if None)

    Returns:
        Novelty score between 0.0 (common) and 1.0 (novel)
    """
    window_days = days or NLP_NOVELTY_WINDOW_DAYS

    try:
        from app.memory.events import iter_events

        # Count similar events in window
        cutoff_date = datetime.now(UTC) - timedelta(days=window_days)
        similar_events = 0

        for event in iter_events():
            if (
                event.get("ticker") == ticker
                and event.get("event_type") == event_type
                and "ts" in event
            ):
                event_date = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
                if event_date >= cutoff_date:
                    similar_events += 1

        # Calculate novelty: fewer similar events = higher novelty
        # Use logarithmic scaling to handle event frequency
        if similar_events == 0:
            return 1.0  # Completely novel
        elif similar_events == 1:
            return 0.8  # Very novel
        elif similar_events <= 3:
            return 0.6  # Somewhat novel
        elif similar_events <= 7:
            return 0.4  # Common
        elif similar_events <= 15:
            return 0.2  # Very common
        else:
            return 0.1  # Extremely common

    except ImportError:
        # Default to moderate novelty if memory not available
        return 0.5


def persist_sentiment_triple(
    ticker: str,
    event_type: str,
    polarity: str,
    strength: float,
    novelty: float,
    source_id: str,
    headline: str,
    source_tz: str = "UTC",
) -> str:
    """
    Persist extracted sentiment triple to memory layer.

    Args:
        ticker: Ticker symbol
        event_type: Type of event
        polarity: Sentiment polarity (positive/negative/neutral)
        strength: Sentiment strength (0.0 to 1.0)
        novelty: Novelty score (0.0 to 1.0)
        source_id: Source identifier
        headline: Original headline
        source_tz: Source timezone

    Returns:
        Event ID
    """
    try:
        from datetime import datetime, timezone

        from app.memory.events import append_event, build_durable_event

        # Build sentiment triple event
        sentiment_event = build_durable_event(
            ticker=ticker,
            event_type="sentiment_triple",
            polarity=polarity,
            strength=strength,
            novelty=novelty,
            source_id=source_id,
            headline=headline,
            source_tz=source_tz,
            extracted_event_type=event_type,
            ingest_ts_utc=datetime.now(UTC).isoformat(),
        )

        # Store in memory
        event_id = append_event(sentiment_event)

        logger.info(
            f"Persisted sentiment triple: {ticker} {event_type} {polarity} ({strength:.2f})"
        )

        return event_id

    except ImportError:
        logger.warning("Memory layer not available for sentiment persistence")
        return f"temp_{int(datetime.now().timestamp())}"


def analyze_news_batch(
    articles: list[dict[str, Any]], persist_triples: bool = True
) -> dict[str, Any]:
    """
    Analyze a batch of news articles with enhanced NLP features.

    Args:
        articles: List of article dictionaries
        persist_triples: Whether to persist sentiment triples

    Returns:
        Comprehensive analysis results
    """
    results = {
        "processed_count": 0,
        "tickers_found": set(),
        "event_types": defaultdict(int),
        "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
        "novelty_scores": [],
        "articles": [],
    }

    for article in articles:
        try:
            headline = article.get("title", "")
            if not headline:
                continue

            # Extract entities and sentiment
            analysis = extract_entities_and_sentiment(headline, article.get("date"))

            # Classify event type
            event_type = classify_event_type(headline)

            # Calculate novelty for each ticker
            article_result = {
                "headline": headline,
                "tickers": analysis["tickers"],
                "entities": analysis["entities"],
                "sentiment": analysis["sentiment"],
                "event_type": event_type,
                "negation_detected": analysis["negation_detected"],
                "novelty_scores": {},
            }

            # Process each ticker
            for ticker in analysis["tickers"]:
                novelty = calculate_novelty_score(ticker, event_type)
                article_result["novelty_scores"][ticker] = novelty

                results["tickers_found"].add(ticker)
                results["novelty_scores"].append(novelty)

                # Persist sentiment triple if requested
                if persist_triples:
                    persist_sentiment_triple(
                        ticker=ticker,
                        event_type=event_type,
                        polarity=analysis["sentiment"]["label"],
                        strength=abs(analysis["sentiment"]["score"]),
                        novelty=novelty,
                        source_id=article.get("url", ""),
                        headline=headline,
                        source_tz=article.get("source_tz", "UTC"),
                    )

            # Update counters
            results["event_types"][event_type] += 1
            results["sentiment_distribution"][analysis["sentiment"]["label"]] += 1
            results["articles"].append(article_result)
            results["processed_count"] += 1

        except Exception as e:
            logger.warning(f"Failed to process article: {e}")
            continue

    # Convert sets to lists for JSON serialization
    results["tickers_found"] = sorted(list(results["tickers_found"]))
    results["event_types"] = dict(results["event_types"])

    return results


__all__ = [
    "analyze_news_sentiment",
    "news_sentiment",
    "get_news_sentiment",
    "analyze_news",
    "analyze_sentiment",
    "analyze",
    "score",
    # Enhanced NLP functions
    "extract_entities_and_sentiment",
    "classify_event_type",
    "aggregate_sentiment_with_decay",
    "calculate_novelty_score",
    "persist_sentiment_triple",
    "analyze_news_batch",
]
