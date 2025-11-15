# Configuration Package

This package contains all configuration-related modules for ZiggyAI.

## Modules

### `settings.py`

Main application settings using Pydantic. Contains the `Settings` class and `get_settings()` function.

**Usage:**

```python
from app.core.config import get_settings

settings = get_settings()
print(settings.ENV)  # development, staging, or production
```

### `time_tuning.py`

Centralized timeout, retry, and queue configuration parameters.

**Usage:**

```python
from app.core.config.time_tuning import TIMEOUTS, BACKOFFS, QUEUE_LIMITS

# Direct access
timeout = TIMEOUTS["http_client_default"]
retries = BACKOFFS["provider_retries"]
queue_size = QUEUE_LIMITS["websocket_default"]

# Using helper functions
from app.core.config.time_tuning import get_timeout, get_backoff, get_queue_limit

timeout = get_timeout("http_client_default")
retries = get_backoff("provider_retries")
queue_size = get_queue_limit("websocket_default")
```

**Environment Overrides:**

```bash
# Override any parameter via environment variables
export TIMEOUT_HTTP_CLIENT_DEFAULT=30.0
export BACKOFF_PROVIDER_RETRIES=3
export QUEUE_WEBSOCKET_DEFAULT=200
```

## Quick Reference

### Common Timeouts

```python
from app.core.config.time_tuning import TIMEOUTS

# HTTP clients
http_timeout = TIMEOUTS["http_client_default"]  # 15.0s
quick_timeout = TIMEOUTS["http_client_short"]   # 5.0s
long_timeout = TIMEOUTS["http_client_long"]     # 20.0s

# WebSocket
ws_send = TIMEOUTS["websocket_send"]            # 2.5s

# Async operations
fast_op = TIMEOUTS["async_fast"]                # 0.5s
slow_op = TIMEOUTS["async_slow"]                # 3.5s
```

### Common Backoff Settings

```python
from app.core.config.time_tuning import BACKOFFS

# Provider retries
retries = BACKOFFS["provider_retries"]          # 2
backoff_base = BACKOFFS["provider_base"]        # 0.5s

# News streaming
news_min = BACKOFFS["news_min_delay"]           # 1.0s
news_max = BACKOFFS["news_max_delay"]           # 15.0s
```

### Common Queue Limits

```python
from app.core.config.time_tuning import QUEUE_LIMITS

# WebSocket queues
ws_queue = QUEUE_LIMITS["websocket_default"]    # 100

# Telemetry
telem_queue = QUEUE_LIMITS["telemetry_events"]  # 1000
batch_size = QUEUE_LIMITS["telemetry_batch_size"]  # 50
```

## Documentation

See `docs/config_tuning.md` for comprehensive documentation including:

- Complete parameter reference
- Environment variable overrides
- Tuning recommendations for different environments
- Migration guide
- Troubleshooting

## Backward Compatibility

The Settings class provides backward-compatible methods:

```python
from app.core.config import get_settings

settings = get_settings()

# These methods delegate to time_tuning module
ws_queue = settings.get_ws_queue_maxsize()
timeout = settings.get_market_fetch_timeout_s()
```

## Adding New Parameters

When adding new timing parameters:

1. Add to appropriate dictionary in `time_tuning.py`:

```python
TIMEOUTS = {
    # ... existing entries ...
    "my_new_timeout": _get_float_env("TIMEOUT_MY_NEW_TIMEOUT", 10.0),
}
```

2. Document in `docs/config_tuning.md`

3. Update this README with common usage examples

4. Use in your code:

```python
from app.core.config.time_tuning import TIMEOUTS

timeout = TIMEOUTS["my_new_timeout"]
```
