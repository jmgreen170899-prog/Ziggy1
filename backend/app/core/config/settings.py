# app/core/config.py
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)  # pip install pydantic-settings


# If you don't have it yet:
# pip install pydantic-settings python-dotenv

logger = logging.getLogger("ziggy.config")


class Settings(BaseSettings):
    # ---- Core Environment ----
    ENV: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    # In development, do not fail health endpoints with 4xx/5xx; return 200 with reasons
    DEV_NON_FATAL_HEALTH: bool = True

    # ---- Provider Mode ----
    # live (default) | sandbox (use local fixtures; no network)
    PROVIDER_MODE: Literal["live", "sandbox"] = "live"

    # ---- Dev DB Selection ----
    # When set to "sqlite", force DATABASE_URL to sqlite:///./data/ziggy.db for local dev
    DEV_DB: str | None = None

    # ---- Development Configuration ----
    SEED_DEV_USER: bool = False

    # ---- Demo Mode ----
    # Enable demo mode for safe demonstrations with deterministic data
    DEMO_MODE: bool = False

    # ---- API Configuration ----
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PROJECT_NAME: str = "Ziggy AI Trading Platform"
    VERSION: str = "1.0.0"
    API_ROOT: str = ""

    # ---- External API Keys ----
    # Market Data Providers
    POLYGON_API_KEY: str | None = None
    ALPACA_KEY_ID: str | None = None
    ALPACA_SECRET_KEY: str | None = None
    NEWS_API_KEY: str | None = None
    FRED_API_KEY: str | None = None

    # AI/LLM Services
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE: str | None = None
    OPENAI_PROJECT: str | None = None
    USE_OPENAI: bool = True

    # Provider Chains (CSV format)
    PROVIDERS_PRICES: str = "polygon,yfinance"
    PROVIDERS_QUOTES: str = "polygon,alpaca,yfinance"
    PROVIDERS_CRYPTO: str = "polygon,yfinance"
    PROVIDERS_NEWS: str = "newsapi"

    # ---- Cache Configuration ----
    CACHE_TTL_SECONDS: int = 60
    REDIS_URL: str | None = None

    # ---- Search / Browse ----
    SEARCH_PROVIDER: str = "duckduckgo"
    TAVILY_API_KEY: str | None = None
    BING_API_KEY: str | None = None

    # ---- Vector Store (Qdrant) ----
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "ziggy_docs"

    # ---- Database ----
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    DATABASE_URL: str | None = None

    # ---- Security ----
    SECRET_KEY: str = "ziggy-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ---- Authentication Configuration ----
    # Enable/disable authentication (disabled by default in development)
    ENABLE_AUTH: bool = False
    # Require auth for trading endpoints
    REQUIRE_AUTH_TRADING: bool = False
    # Require auth for paper trading
    REQUIRE_AUTH_PAPER: bool = False
    # Require auth for cognitive/decision endpoints
    REQUIRE_AUTH_COGNITIVE: bool = False
    # Require auth for integration/apply endpoints
    REQUIRE_AUTH_INTEGRATION: bool = False

    # ---- Telegram ----
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    TELEGRAM_WEBHOOK_SECRET: str | None = None

    # ---- Trading & Scanning ----
    SCAN_SYMBOLS: str = "AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA"
    SCAN_INTERVAL_S: int = 60
    ZIGGY_SCAN_DEFAULT: bool = True

    # ---- Paper Trading Lab Configuration ----
    # Rate limiting and safety
    PAPER_MAX_TRADES_PER_MINUTE: int = 100
    PAPER_MAX_TRADES_PER_HOUR: int = 3000
    PAPER_MAX_POSITION_SIZE: float = 0.05  # 5% max position size
    PAPER_MAX_DAILY_LOSS: float = 0.10  # 10% max daily loss

    # Initial funding and balances
    PAPER_INITIAL_BALANCE: float = 100000.0  # $100k starting balance
    PAPER_COMMISSION_PER_TRADE: float = 1.0  # $1 per trade
    PAPER_SLIPPAGE_BPS: int = 5  # 0.5 basis points slippage

    # Execution simulation
    PAPER_MIN_FILL_LATENCY_MS: int = 10  # Minimum 10ms execution time
    PAPER_MAX_FILL_LATENCY_MS: int = 500  # Maximum 500ms execution time
    PAPER_FILL_RATE: float = 0.98  # 98% fill rate (2% rejection)

    # Theory allocation and bandit parameters
    PAPER_MIN_THEORY_ALLOCATION: float = 0.01  # Minimum 1% allocation
    PAPER_EXPLORATION_RATE: float = 0.1  # 10% exploration vs exploitation
    PAPER_DECAY_FACTOR: float = 0.999  # Daily decay for performance tracking

    # Online learning settings
    PAPER_LEARNING_RATE: float = 0.01
    PAPER_BATCH_SIZE: int = 32
    PAPER_MODEL_UPDATE_FREQUENCY: int = 100  # Update every 100 trades
    PAPER_FEATURE_WINDOW_MINUTES: int = 60  # 1 hour feature window

    # Data persistence and cleanup
    PAPER_MAX_TRADE_HISTORY_DAYS: int = 30  # Keep 30 days of trade history
    PAPER_SNAPSHOT_FREQUENCY_MINUTES: int = 60  # Model snapshots every hour
    PAPER_CLEANUP_FREQUENCY_HOURS: int = 24  # Daily cleanup of old data

    # ---- Embeddings ----
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"
    EMBEDDING_DEVICE: str = "cpu"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    # ---- Ingestion ----
    INGEST_ON_STARTUP: bool = False
    INGEST_ROOT: str = "../data"
    INGEST_COLLECTION: str = "ziggy_docs"

    # ---- WebSocket Tuning ----
    # NOTE: These settings are now managed in core.config.time_tuning
    # They remain here for backward compatibility but will be deprecated
    WS_QUEUE_MAXSIZE: int | None = None
    WS_ENQUEUE_TIMEOUT_MS: int | None = None

    # ---- Retry & Backoff (defaults; modules may override) ----
    # NOTE: These settings are now managed in core.config.time_tuning
    # They remain here for backward compatibility but will be deprecated
    BACKOFF_MIN_MS: int | None = None
    BACKOFF_MAX_MS: int | None = None
    BACKOFF_FACTOR: float | None = None
    BACKOFF_JITTER: float | None = None

    # ---- Provider Fetch Timeouts ----
    # NOTE: This setting is now managed in core.config.time_tuning
    # It remains here for backward compatibility but will be deprecated
    MARKET_FETCH_TIMEOUT_S: float | None = None

    @model_validator(mode="after")
    def validate_production_requirements(self):
        """Validate that production environment has required keys (pydantic v2)."""
        if self.ENV == "production":
            required_for_prod = {
                "SECRET_KEY": self.SECRET_KEY,
                "POLYGON_API_KEY": self.POLYGON_API_KEY,
                "DATABASE_URL": self.DATABASE_URL,
            }

            missing = [
                k
                for k, v in required_for_prod.items()
                if not v
                or (k == "SECRET_KEY" and v == "ziggy-secret-change-in-production")
            ]

            if missing:
                raise ValueError(
                    f"Production environment missing required config: {', '.join(missing)}"
                )

        return self

    @model_validator(mode="after")
    def apply_dev_sqlite_override(self):
        """If DEV_DB=sqlite, enforce a stable local SQLite URL and ensure folder exists.

        This guarantees a consistent path for Alembic migrations and local dev.
        """
        try:
            if (self.DEV_DB or "").strip().lower() == "sqlite":
                # Ensure ./data exists relative to backend working directory
                data_dir = Path("./data").resolve()
                data_dir.mkdir(parents=True, exist_ok=True)
                # Force DATABASE_URL
                self.DATABASE_URL = "sqlite:///./data/ziggy.db"
        except Exception:
            # Non-fatal; dev convenience only
            pass
        return self

    @property
    def is_development(self) -> bool:
        return self.ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins into list"""
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def has_polygon_key(self) -> bool:
        return bool(self.POLYGON_API_KEY and self.POLYGON_API_KEY.strip())

    @property
    def has_alpaca_keys(self) -> bool:
        return bool(self.ALPACA_KEY_ID and self.ALPACA_SECRET_KEY)

    @property
    def provider_chains(self) -> dict[str, list[str]]:
        """Parse provider chains into structured format"""
        return {
            "prices": [
                p.strip().lower() for p in self.PROVIDERS_PRICES.split(",") if p.strip()
            ],
            "quotes": [
                p.strip().lower() for p in self.PROVIDERS_QUOTES.split(",") if p.strip()
            ],
            "crypto": [
                p.strip().lower() for p in self.PROVIDERS_CRYPTO.split(",") if p.strip()
            ],
            "news": [
                p.strip().lower() for p in self.PROVIDERS_NEWS.split(",") if p.strip()
            ],
        }

    def get_ws_queue_maxsize(self) -> int:
        """Get WebSocket queue max size (uses time_tuning if not overridden)."""
        if self.WS_QUEUE_MAXSIZE is not None:
            return self.WS_QUEUE_MAXSIZE
        # Import here to avoid circular dependency
        from app.core.config.time_tuning import QUEUE_LIMITS

        return QUEUE_LIMITS["websocket_default"]

    def get_ws_enqueue_timeout_ms(self) -> int:
        """Get WebSocket enqueue timeout in ms (uses time_tuning if not overridden)."""
        if self.WS_ENQUEUE_TIMEOUT_MS is not None:
            return self.WS_ENQUEUE_TIMEOUT_MS
        from app.core.config.time_tuning import QUEUE_LIMITS

        return QUEUE_LIMITS["websocket_enqueue_timeout_ms"]

    def get_market_fetch_timeout_s(self) -> float:
        """Get market fetch timeout in seconds (uses time_tuning if not overridden)."""
        if self.MARKET_FETCH_TIMEOUT_S is not None:
            return self.MARKET_FETCH_TIMEOUT_S
        from app.core.config.time_tuning import TIMEOUTS

        return TIMEOUTS["provider_default"]

    # Pydantic will read a .env **relative to the working dir by default**.
    # We make it robust by pointing to the project root .env explicitly:
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
