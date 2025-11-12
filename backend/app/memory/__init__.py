"""
Memory & Knowledge module for ZiggyAI

This module provides:
- Event Store: append-only storage for trading decisions and outcomes
- Vector Memory: similarity search for retrieval-augmented decisions
- Learning: self-critique and drift detection
"""

from .events import append_event, iter_events, update_outcome
from .vecdb import build_embedding, search_similar, upsert_event


__all__ = [
    "append_event",
    "build_embedding",
    "iter_events",
    "search_similar",
    "update_outcome",
    "upsert_event",
]
