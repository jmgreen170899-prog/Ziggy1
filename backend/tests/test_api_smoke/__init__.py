"""
API Smoke Tests for ZiggyAI Backend

Feature-level tests per domain to verify:
- Status codes (not just 200)
- Key response fields and invariants
- Realistic payloads from Pydantic schemas
- Fast, independent tests suitable for CI

Tests act as contracts for UI and future refactors.
"""
