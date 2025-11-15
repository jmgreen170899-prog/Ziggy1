"""
Ticker Linker - Perception Layer

Maps organization names to ticker symbols with exchange context.
Handles company name variations, subsidiaries, and temporal changes.
"""

from __future__ import annotations

import json
import logging
import os
import re


logger = logging.getLogger(__name__)

# Environment configuration
TICKER_DB_PATH = os.getenv("TICKER_DB_PATH", "/data/ticker_mapping.json")
FUZZY_MATCH_THRESHOLD = float(os.getenv("FUZZY_MATCH_THRESHOLD", "0.8"))


class TickerLinker:
    """
    Links organization names to ticker symbols using multiple strategies.
    """

    def __init__(self):
        self.exact_matches: dict[str, list[str]] = {}
        self.fuzzy_matches: dict[str, list[str]] = {}
        self.aliases: dict[str, str] = {}
        self.subsidiaries: dict[str, str] = {}
        self.exchange_context: dict[str, str] = {}

        self._load_mappings()
        self._build_common_aliases()

    def _load_mappings(self) -> None:
        """Load ticker mappings from configuration file."""
        try:
            if os.path.exists(TICKER_DB_PATH):
                with open(TICKER_DB_PATH, encoding="utf-8") as f:
                    mappings = json.load(f)

                self.exact_matches = mappings.get("exact_matches", {})
                self.fuzzy_matches = mappings.get("fuzzy_matches", {})
                self.aliases = mappings.get("aliases", {})
                self.subsidiaries = mappings.get("subsidiaries", {})
                self.exchange_context = mappings.get("exchange_context", {})

                logger.info(
                    f"Loaded ticker mappings: {len(self.exact_matches)} exact matches"
                )
            else:
                logger.warning(f"Ticker mapping file not found: {TICKER_DB_PATH}")

        except Exception as e:
            logger.error(f"Failed to load ticker mappings: {e}")

    def _build_common_aliases(self) -> None:
        """Build common company name aliases and variations."""
        # Common suffixes to normalize
        common_suffixes = [
            "inc",
            "inc.",
            "incorporated",
            "corp",
            "corp.",
            "corporation",
            "ltd",
            "ltd.",
            "limited",
            "llc",
            "l.l.c.",
            "plc",
            "p.l.c.",
            "co",
            "co.",
            "company",
            "group",
            "holdings",
            "international",
            "technologies",
            "tech",
            "systems",
            "solutions",
            "services",
        ]

        # Build default mappings for major companies
        default_mappings = {
            # Technology
            "apple": ["AAPL"],
            "microsoft": ["MSFT"],
            "amazon": ["AMZN"],
            "google": ["GOOGL", "GOOG"],
            "alphabet": ["GOOGL", "GOOG"],
            "meta": ["META"],
            "facebook": ["META"],
            "tesla": ["TSLA"],
            "nvidia": ["NVDA"],
            "intel": ["INTC"],
            "cisco": ["CSCO"],
            "oracle": ["ORCL"],
            "salesforce": ["CRM"],
            "adobe": ["ADBE"],
            "netflix": ["NFLX"],
            # Financial
            "jpmorgan": ["JPM"],
            "jp morgan": ["JPM"],
            "bank of america": ["BAC"],
            "wells fargo": ["WFC"],
            "goldman sachs": ["GS"],
            "morgan stanley": ["MS"],
            "citigroup": ["C"],
            "american express": ["AXP"],
            "visa": ["V"],
            "mastercard": ["MA"],
            "berkshire hathaway": ["BRK.A", "BRK.B"],
            # Healthcare
            "johnson & johnson": ["JNJ"],
            "pfizer": ["PFE"],
            "abbvie": ["ABBV"],
            "merck": ["MRK"],
            "bristol myers": ["BMY"],
            "eli lilly": ["LLY"],
            "unitedhealth": ["UNH"],
            # Consumer
            "procter & gamble": ["PG"],
            "coca cola": ["KO"],
            "pepsi": ["PEP"],
            "walmart": ["WMT"],
            "home depot": ["HD"],
            "mcdonalds": ["MCD"],
            "nike": ["NKE"],
            "disney": ["DIS"],
            # Energy
            "exxon": ["XOM"],
            "exxon mobil": ["XOM"],
            "chevron": ["CVX"],
            "conocophillips": ["COP"],
        }

        # Merge with existing exact matches
        for name, tickers in default_mappings.items():
            if name not in self.exact_matches:
                self.exact_matches[name] = tickers

        # Build suffix variations
        self.common_suffixes = set(common_suffixes)

    def map_org_to_tickers(
        self, text: str, date: str = None, venue: str = None
    ) -> list[str]:
        """
        Map organization names in text to ticker symbols.

        Args:
            text: Text containing organization names
            date: Date context for temporal mappings
            venue: News venue for context (Reuters, Bloomberg, etc.)

        Returns:
            List of ticker symbols found
        """
        if not text or not text.strip():
            return []

        found_tickers = set()

        # Extract potential company names from text
        company_names = self._extract_company_names(text)

        for name in company_names:
            tickers = self._resolve_name_to_tickers(name, date, venue)
            found_tickers.update(tickers)

        return sorted(list(found_tickers))

    def _extract_company_names(self, text: str) -> list[str]:
        """Extract potential company names from text."""
        # Common patterns for company names
        patterns = [
            # Capitalized sequences (2+ words)
            r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s+(?:Inc|Corp|Ltd|LLC|PLC|Co)\.?)?",
            # Known company suffixes
            r"\b[A-Z][a-zA-Z\s&]+(?:Inc\.|Corp\.|Ltd\.|LLC|PLC|Company|Group|Holdings|International|Technologies|Systems|Solutions|Services)\b",
            # All caps sequences (likely acronyms)
            r"\b[A-Z]{2,8}\b",
            # Mixed case with common business words
            r"\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\s+(?:Bank|Financial|Insurance|Energy|Oil|Gas|Electric|Motors|Airlines|Airways)\b",
        ]

        candidates = set()

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            candidates.update(match.strip() for match in matches)

        # Filter out common false positives
        false_positives = {
            "US",
            "USA",
            "NYSE",
            "NASDAQ",
            "SEC",
            "CEO",
            "CFO",
            "IPO",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        }

        filtered_candidates = []
        for candidate in candidates:
            if (
                len(candidate) >= 2
                and candidate.upper() not in false_positives
                and not candidate.isdigit()
            ):
                filtered_candidates.append(candidate)

        return filtered_candidates

    def _resolve_name_to_tickers(
        self, name: str, date: str = None, venue: str = None
    ) -> list[str]:
        """Resolve a single company name to ticker symbols."""
        if not name:
            return []

        normalized_name = self._normalize_name(name)

        # 1. Try exact match
        if normalized_name in self.exact_matches:
            return self.exact_matches[normalized_name]

        # 2. Try aliases
        if normalized_name in self.aliases:
            canonical_name = self.aliases[normalized_name]
            if canonical_name in self.exact_matches:
                return self.exact_matches[canonical_name]

        # 3. Try subsidiaries
        if normalized_name in self.subsidiaries:
            parent_name = self.subsidiaries[normalized_name]
            if parent_name in self.exact_matches:
                return self.exact_matches[parent_name]

        # 4. Try fuzzy matching
        fuzzy_tickers = self._fuzzy_match(normalized_name)
        if fuzzy_tickers:
            return fuzzy_tickers

        # 5. Try partial matching for known patterns
        partial_tickers = self._partial_match(normalized_name)
        if partial_tickers:
            return partial_tickers

        return []

    def _normalize_name(self, name: str) -> str:
        """Normalize company name for matching."""
        # Convert to lowercase
        normalized = name.lower().strip()

        # Remove common punctuation
        normalized = re.sub(r'[.,\'"!?]', "", normalized)

        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        # Remove common suffixes for broader matching
        for suffix in self.common_suffixes:
            pattern = rf"\b{re.escape(suffix)}\b$"
            normalized = re.sub(pattern, "", normalized).strip()

        # Handle special characters
        normalized = normalized.replace("&", "and")
        normalized = normalized.replace("+", "plus")

        return normalized

    def _fuzzy_match(self, name: str) -> list[str]:
        """Perform fuzzy matching against known company names."""
        best_matches = []

        for known_name, tickers in self.exact_matches.items():
            similarity = self._calculate_similarity(name, known_name)
            if similarity >= FUZZY_MATCH_THRESHOLD:
                best_matches.extend(tickers)

        return list(set(best_matches))

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two company names."""
        # Simple Jaccard similarity on word sets
        words1 = set(name1.split())
        words2 = set(name2.split())

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        if union == 0:
            return 0.0

        return intersection / union

    def _partial_match(self, name: str) -> list[str]:
        """Try partial matching for multi-word company names."""
        name_words = name.split()

        if len(name_words) >= 2:
            # Try first word only (e.g., "Apple" from "Apple Inc")
            first_word = name_words[0]
            if first_word in self.exact_matches:
                return self.exact_matches[first_word]

            # Try first two words (e.g., "JP Morgan" from "JP Morgan Chase")
            if len(name_words) >= 2:
                first_two = " ".join(name_words[:2])
                if first_two in self.exact_matches:
                    return self.exact_matches[first_two]

        return []

    def add_mapping(
        self, company_name: str, tickers: list[str], mapping_type: str = "exact"
    ) -> None:
        """
        Add a new company name to ticker mapping.

        Args:
            company_name: Company name to map
            tickers: List of ticker symbols
            mapping_type: Type of mapping ("exact", "alias", "subsidiary")
        """
        normalized_name = self._normalize_name(company_name)

        if mapping_type == "exact":
            self.exact_matches[normalized_name] = tickers
        elif mapping_type == "alias":
            if tickers:
                # Find the canonical name for this ticker
                canonical_name = None
                for name, mapped_tickers in self.exact_matches.items():
                    if tickers[0] in mapped_tickers:
                        canonical_name = name
                        break

                if canonical_name:
                    self.aliases[normalized_name] = canonical_name
        elif mapping_type == "subsidiary":
            if tickers:
                # Find parent company
                parent_name = None
                for name, mapped_tickers in self.exact_matches.items():
                    if tickers[0] in mapped_tickers:
                        parent_name = name
                        break

                if parent_name:
                    self.subsidiaries[normalized_name] = parent_name

        logger.info(f"Added {mapping_type} mapping: {company_name} -> {tickers}")

    def get_stats(self) -> dict[str, int]:
        """Get mapping statistics."""
        return {
            "exact_matches": len(self.exact_matches),
            "aliases": len(self.aliases),
            "subsidiaries": len(self.subsidiaries),
            "exchange_mappings": len(self.exchange_context),
            "total_tickers": len(
                set(
                    ticker
                    for tickers in self.exact_matches.values()
                    for ticker in tickers
                )
            ),
        }


# Global instance
_ticker_linker = TickerLinker()


def map_org_to_tickers(text: str, date: str = None, venue: str = None) -> list[str]:
    """
    Map organization names in text to ticker symbols.

    Args:
        text: Text containing organization names
        date: Date context for temporal mappings
        venue: News venue for context

    Returns:
        List of ticker symbols found
    """
    return _ticker_linker.map_org_to_tickers(text, date, venue)


def add_ticker_mapping(
    company_name: str, tickers: list[str], mapping_type: str = "exact"
) -> None:
    """Add a new ticker mapping."""
    _ticker_linker.add_mapping(company_name, tickers, mapping_type)


def get_ticker_linker_stats() -> dict[str, int]:
    """Get ticker linker statistics."""
    return _ticker_linker.get_stats()
