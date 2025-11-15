# Configuration Tuning Guide

This guide documents all centralized timing-related configuration parameters in ZiggyAI. All parameters are defined in `backend/app/core/config/time_tuning.py` and can be overridden via environment variables for production tuning without code changes.

## Overview

The configuration system provides three main categories of tuning parameters:

1. **TIMEOUTS** - Control how long operations wait before timing out
2. **BACKOFFS** - Define retry behavior for transient failures
3. **QUEUE_LIMITS** - Set maximum queue sizes and related parameters

## Environment Variable Overrides

All parameters support environment variable overrides with the following format:

- `TIMEOUT_<KEY>` for timeout overrides (e.g., `TIMEOUT_HTTP_CLIENT_DEFAULT`)
- `BACKOFF_<KEY>` for backoff overrides (e.g., `BACKOFF_MIN_DELAY`)
- `QUEUE_<KEY>` for queue limit overrides (e.g., `QUEUE_WEBSOCKET_DEFAULT`)

Example:

```bash
# Override HTTP client timeout to 30 seconds
export TIMEOUT_HTTP_CLIENT_DEFAULT=30.0

# Override WebSocket queue size to 200
export QUEUE_WEBSOCKET_DEFAULT=200

# Override provider retry count to 3
export BACKOFF_PROVIDER_RETRIES=3
```

## Timeouts

All timeout values are in **seconds** unless otherwise specified.

### HTTP Client Timeouts

| Parameter             | Default | Description                                          | Environment Variable          |
| --------------------- | ------- | ---------------------------------------------------- | ----------------------------- |
| `http_client_default` | 15.0    | Standard HTTP client timeout for most requests       | `TIMEOUT_HTTP_CLIENT_DEFAULT` |
| `http_client_short`   | 5.0     | Short timeout for quick operations                   | `TIMEOUT_HTTP_CLIENT_SHORT`   |
| `http_client_medium`  | 10.0    | Medium timeout for moderate operations               | `TIMEOUT_HTTP_CLIENT_MEDIUM`  |
| `http_client_long`    | 20.0    | Long timeout for slow operations (e.g., SEC filings) | `TIMEOUT_HTTP_CLIENT_LONG`    |

**Used by:**

- `services/market_providers.py`: Polygon and Alpaca API clients
- `services/crypto_providers.py`: Polygon crypto client
- `services/macro.py`: FRED and FMP API clients
- `services/filings.py`: SEC EDGAR API client

### WebSocket Timeouts

| Parameter             | Default | Description                                    | Environment Variable          |
| --------------------- | ------- | ---------------------------------------------- | ----------------------------- |
| `websocket_send`      | 2.5     | Timeout for WebSocket send operations          | `TIMEOUT_WEBSOCKET_SEND`      |
| `websocket_queue_get` | 1.5     | Timeout for fetching data from WebSocket queue | `TIMEOUT_WEBSOCKET_QUEUE_GET` |

**Used by:**

- `core/websocket.py`: WebSocket connection manager

### Async Operation Timeouts

| Parameter        | Default | Description                                        | Environment Variable     |
| ---------------- | ------- | -------------------------------------------------- | ------------------------ |
| `async_fast`     | 0.5     | Fast async operations (portfolio/position fetches) | `TIMEOUT_ASYNC_FAST`     |
| `async_standard` | 1.0     | Standard async operations                          | `TIMEOUT_ASYNC_STANDARD` |
| `async_medium`   | 2.5     | Medium-length async operations                     | `TIMEOUT_ASYNC_MEDIUM`   |
| `async_slow`     | 3.5     | Slower async operations (RSS news fetch)           | `TIMEOUT_ASYNC_SLOW`     |

**Used by:**

- `services/portfolio_streaming.py`: Portfolio and position data fetches
- `services/news_streaming.py`: RSS news fetches

### RSS Feed Timeouts

| Parameter       | Default | Description                  | Environment Variable    |
| --------------- | ------- | ---------------------------- | ----------------------- |
| `rss_total`     | 5.0     | Total RSS feed fetch timeout | `TIMEOUT_RSS_TOTAL`     |
| `rss_connect`   | 1.5     | RSS connection timeout       | `TIMEOUT_RSS_CONNECT`   |
| `rss_sock_read` | 2.5     | RSS socket read timeout      | `TIMEOUT_RSS_SOCK_READ` |

**Used by:**

- `services/rss_news_provider.py`: RSS feed fetcher

### Provider-Specific Timeouts

| Parameter              | Default | Description                                   | Environment Variable           |
| ---------------------- | ------- | --------------------------------------------- | ------------------------------ |
| `provider_default`     | 5.0     | Default provider fetch timeout                | `TIMEOUT_PROVIDER_DEFAULT`     |
| `provider_market_data` | 15.0    | Market data provider timeout (YFinance, etc.) | `TIMEOUT_PROVIDER_MARKET_DATA` |

**Used by:**

- `services/market_providers.py`: YFinance history fetches
- `services/chart_streaming.py`: Chart data fetches

### Other Timeouts

| Parameter             | Default | Description                                           | Environment Variable          |
| --------------------- | ------- | ----------------------------------------------------- | ----------------------------- |
| `telemetry_http`      | 5       | HTTP timeout for telemetry endpoint (integer seconds) | `TIMEOUT_TELEMETRY_HTTP`      |
| `telemetry_queue_get` | 1.0     | Queue.get() timeout for telemetry events              | `TIMEOUT_TELEMETRY_QUEUE_GET` |
| `health_check`        | 5.0     | Health check HTTP timeout                             | `TIMEOUT_HEALTH_CHECK`        |

**Used by:**

- `services/telemetry.py`: Telemetry system
- `core/health.py`: Health checker

## Backoff Configuration

Backoff parameters control exponential backoff and retry behavior for transient failures.

### Default Backoff Settings

These are used by the `JitterBackoff` class in `core/retry.py`.

| Parameter   | Default | Description                    | Environment Variable |
| ----------- | ------- | ------------------------------ | -------------------- |
| `min_delay` | 0.5     | Minimum retry delay (seconds)  | `BACKOFF_MIN_DELAY`  |
| `max_delay` | 10.0    | Maximum retry delay (seconds)  | `BACKOFF_MAX_DELAY`  |
| `factor`    | 2.0     | Exponential backoff multiplier | `BACKOFF_FACTOR`     |
| `jitter`    | 0.2     | Random jitter factor (0.0-1.0) | `BACKOFF_JITTER`     |

**Formula:** `delay = min(max_delay, min_delay * factor^attempts * (1 ± jitter))`

### News Streaming Backoff

| Parameter        | Default | Description                    | Environment Variable     |
| ---------------- | ------- | ------------------------------ | ------------------------ |
| `news_min_delay` | 1.0     | Minimum news fetch retry delay | `BACKOFF_NEWS_MIN_DELAY` |
| `news_max_delay` | 15.0    | Maximum news fetch retry delay | `BACKOFF_NEWS_MAX_DELAY` |
| `news_factor`    | 2.0     | News retry exponential factor  | `BACKOFF_NEWS_FACTOR`    |
| `news_jitter`    | 0.25    | News retry jitter factor       | `BACKOFF_NEWS_JITTER`    |

**Used by:**

- `services/news_streaming.py`: News streaming error backoff

### Portfolio Streaming Backoff

| Parameter              | Default | Description                                        | Environment Variable           |
| ---------------------- | ------- | -------------------------------------------------- | ------------------------------ |
| `portfolio_max_delay`  | 30.0    | Maximum portfolio fetch retry delay                | `BACKOFF_PORTFOLIO_MAX_DELAY`  |
| `portfolio_base`       | 2.0     | Portfolio retry base for exponential backoff       | `BACKOFF_PORTFOLIO_BASE`       |
| `portfolio_max_streak` | 5       | Maximum error streak count for backoff calculation | `BACKOFF_PORTFOLIO_MAX_STREAK` |

**Formula:** `delay = min(portfolio_max_delay, portfolio_base^min(portfolio_max_streak, error_streak))`

**Used by:**

- `services/portfolio_streaming.py`: Portfolio streaming error backoff

### Provider Retry Configuration

| Parameter               | Default | Description                             | Environment Variable            |
| ----------------------- | ------- | --------------------------------------- | ------------------------------- |
| `provider_base`         | 0.5     | Base backoff delay for provider retries | `BACKOFF_PROVIDER_BASE`         |
| `provider_retries`      | 2       | Number of retry attempts for providers  | `BACKOFF_PROVIDER_RETRIES`      |
| `provider_fail_penalty` | 10      | Seconds to skip a failing provider      | `BACKOFF_PROVIDER_FAIL_PENALTY` |

**Used by:**

- `services/provider_factory.py`: Multi-provider failover system

## Queue Limits

Queue limits control the maximum size of various async queues throughout the application.

### WebSocket Queues

| Parameter                      | Default | Description                              | Environment Variable                 |
| ------------------------------ | ------- | ---------------------------------------- | ------------------------------------ |
| `websocket_default`            | 100     | Default WebSocket queue size per channel | `QUEUE_WEBSOCKET_DEFAULT`            |
| `websocket_enqueue_timeout_ms` | 50      | Enqueue timeout in milliseconds          | `QUEUE_WEBSOCKET_ENQUEUE_TIMEOUT_MS` |

**Used by:**

- `core/websocket.py`: Per-channel broadcast queues

**Behavior:** When queue is full:

- Attempts to enqueue wait up to `websocket_enqueue_timeout_ms`
- If still full, message is dropped and metrics are updated
- At 80% capacity, upstream backpressure may be applied

### Telemetry Queue

| Parameter                  | Default | Description                        | Environment Variable             |
| -------------------------- | ------- | ---------------------------------- | -------------------------------- |
| `telemetry_events`         | 1000    | Maximum telemetry event queue size | `QUEUE_TELEMETRY_EVENTS`         |
| `telemetry_batch_size`     | 50      | Number of events per batch send    | `QUEUE_TELEMETRY_BATCH_SIZE`     |
| `telemetry_flush_interval` | 30      | Seconds between batch flushes      | `QUEUE_TELEMETRY_FLUSH_INTERVAL` |

**Used by:**

- `services/telemetry.py`: Telemetry event batching system

**Behavior:**

- Events are batched until `telemetry_batch_size` is reached OR `telemetry_flush_interval` seconds pass
- If queue is full, new events are dropped and `events_dropped` metric is incremented

### Portfolio Streaming Queue

| Parameter             | Default | Description                   | Environment Variable        |
| --------------------- | ------- | ----------------------------- | --------------------------- |
| `portfolio_snapshots` | 100     | Portfolio snapshot queue size | `QUEUE_PORTFOLIO_SNAPSHOTS` |

**Used by:**

- `services/portfolio_streaming.py`: Portfolio data streaming

**Behavior:**

- Producer creates portfolio snapshots every 5 seconds
- Consumer broadcasts from queue to WebSocket clients
- If queue is full, QueueFull exception is caught and logged

## Tuning Recommendations

### Development Environment

For local development, the default values are optimized for responsiveness:

- Short timeouts to fail fast and show issues quickly
- Small queue sizes to avoid memory buildup
- Moderate retry counts to balance reliability and speed

### Production Environment

For production deployments, consider these adjustments:

```bash
# Increase timeouts for slower networks
export TIMEOUT_HTTP_CLIENT_DEFAULT=30.0
export TIMEOUT_PROVIDER_MARKET_DATA=25.0

# Increase queue sizes for high throughput
export QUEUE_WEBSOCKET_DEFAULT=500
export QUEUE_TELEMETRY_EVENTS=5000

# More aggressive retries
export BACKOFF_PROVIDER_RETRIES=3
export BACKOFF_MAX_DELAY=30.0

# Larger batches for telemetry
export QUEUE_TELEMETRY_BATCH_SIZE=100
export QUEUE_TELEMETRY_FLUSH_INTERVAL=60
```

### High-Latency Environments

For deployment in high-latency environments (e.g., intercontinental):

```bash
# Increase all HTTP timeouts
export TIMEOUT_HTTP_CLIENT_DEFAULT=45.0
export TIMEOUT_HTTP_CLIENT_MEDIUM=25.0
export TIMEOUT_HTTP_CLIENT_LONG=60.0

# Increase provider timeouts
export TIMEOUT_PROVIDER_MARKET_DATA=30.0

# More patient backoff
export BACKOFF_MAX_DELAY=60.0
export BACKOFF_PROVIDER_RETRIES=4
```

### High-Volume/Load Testing

For load testing or high-volume production:

```bash
# Very large queues
export QUEUE_WEBSOCKET_DEFAULT=1000
export QUEUE_TELEMETRY_EVENTS=10000
export QUEUE_PORTFOLIO_SNAPSHOTS=500

# Larger telemetry batches
export QUEUE_TELEMETRY_BATCH_SIZE=200
export QUEUE_TELEMETRY_FLUSH_INTERVAL=120
```

## Monitoring Queue Health

WebSocket queue statistics are available via the connection manager:

```python
from app.core.websocket import connection_manager

stats = connection_manager.get_connection_stats()
for channel, metrics in stats.get("per_channel", {}).items():
    queue_len = metrics.get("queue_len", 0)
    queue_dropped = metrics.get("queue_dropped", 0)

    # Alert if queue is consistently near capacity
    if queue_len / QUEUE_LIMITS["websocket_default"] > 0.8:
        logger.warning(f"Channel {channel} queue at {queue_len} capacity")
```

## Helper Functions

The `time_tuning` module provides helper functions for programmatic access:

```python
from app.core.config.time_tuning import get_timeout, get_backoff, get_queue_limit

# Get values
timeout = get_timeout("http_client_default")  # Returns 15.0
retries = get_backoff("provider_retries")     # Returns 2
queue_size = get_queue_limit("websocket_default")  # Returns 100

# With defaults for missing keys
custom_timeout = get_timeout("custom_key", default=5.0)
```

## Backward Compatibility

The Settings class in `core/config.py` maintains backward compatibility:

```python
from app.core.config import get_settings

settings = get_settings()

# These methods delegate to time_tuning module
ws_queue_size = settings.get_ws_queue_maxsize()
market_timeout = settings.get_market_fetch_timeout_s()
```

Direct attribute access (`settings.WS_QUEUE_MAXSIZE`) is deprecated but still works. Set environment variables to override:

```bash
# Old style (still works but deprecated)
export WS_QUEUE_MAXSIZE=200

# New style (recommended)
export QUEUE_WEBSOCKET_DEFAULT=200
```

## Migration Guide

If you have existing code using hardcoded values:

**Before:**

```python
timeout = 15.0
queue = asyncio.Queue(maxsize=100)
retries = 2
```

**After:**

```python
from app.core.config.time_tuning import TIMEOUTS, QUEUE_LIMITS, BACKOFFS

timeout = TIMEOUTS["http_client_default"]
queue = asyncio.Queue(maxsize=QUEUE_LIMITS["websocket_default"])
retries = BACKOFFS["provider_retries"]
```

## Troubleshooting

### Symptoms: Frequent timeouts

**Diagnosis:** Timeouts may be too aggressive for your environment.

**Solution:** Increase relevant timeout values:

```bash
export TIMEOUT_HTTP_CLIENT_DEFAULT=30.0
export TIMEOUT_PROVIDER_MARKET_DATA=25.0
```

### Symptoms: High memory usage

**Diagnosis:** Queue sizes may be too large, allowing excessive buffering.

**Solution:** Reduce queue sizes:

```bash
export QUEUE_WEBSOCKET_DEFAULT=50
export QUEUE_TELEMETRY_EVENTS=500
```

### Symptoms: Dropped messages/events

**Diagnosis:** Queues filling up faster than they're being consumed.

**Solution:** Either:

1. Increase queue sizes (if you have memory):
   ```bash
   export QUEUE_WEBSOCKET_DEFAULT=500
   ```
2. Or add more consumer capacity (scale horizontally)
3. Or reduce producer rate

### Symptoms: Slow retry recovery

**Diagnosis:** Backoff delays may be too aggressive.

**Solution:** Reduce backoff parameters:

```bash
export BACKOFF_MAX_DELAY=5.0
export BACKOFF_FACTOR=1.5
```

## See Also

- `backend/app/core/config/time_tuning.py` - Source implementation
- `backend/app/core/retry.py` - JitterBackoff implementation
- `backend/app/core/websocket.py` - WebSocket queue management
- `backend/app/services/telemetry.py` - Telemetry batching
