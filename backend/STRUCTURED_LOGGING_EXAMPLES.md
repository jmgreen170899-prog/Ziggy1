# Structured Logging Examples

This document provides practical examples of using the standardized structured logging in ZiggyAI.

## Quick Start

```python
from app.observability.structured_logging import (
    get_structured_logger,
    log_operation,
    log_external_call,
    log_slowdown
)

# Get a logger for your subsystem
logger = get_structured_logger("trading")
```

## Example 1: Trading Operations

### Backtest Execution

```python
from app.observability.structured_logging import trading_logger, log_operation

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run backtest with structured logging"""

    with log_operation(
        trading_logger,
        "backtest",
        ticker=request.symbol,
        strategy=request.strategy
    ):
        # Execute backtest
        result = await execute_backtest(request)
        return result

# Logs output:
# INFO: Starting backtest {"subsystem": "trading", "operation": "backtest", "ticker": "AAPL", "strategy": "sma50_cross"}
# INFO: Completed backtest {"subsystem": "trading", "operation": "backtest", "ticker": "AAPL", "strategy": "sma50_cross", "duration_sec": 2.456}
```

### Market Data Fetch with Timeout Logging

```python
from app.observability.structured_logging import market_data_logger, log_external_call
import time

async def fetch_ohlc(ticker: str, timeout: float = 10.0):
    """Fetch OHLC data with timeout logging"""

    start = time.time()

    try:
        # Make external call
        data = await provider.get_ohlc(ticker, timeout=timeout)
        duration = time.time() - start

        # Log successful call
        log_external_call(
            market_data_logger,
            provider="yfinance",
            operation="fetch_ohlc",
            duration_sec=duration,
            status="success",
            timeout_sec=timeout,
            ticker=ticker,
            bars_count=len(data)
        )

        return data

    except asyncio.TimeoutError:
        duration = time.time() - start

        # Log timeout
        log_external_call(
            market_data_logger,
            provider="yfinance",
            operation="fetch_ohlc",
            duration_sec=duration,
            status="timeout",
            timeout_sec=timeout,
            ticker=ticker
        )
        raise

    except Exception as e:
        duration = time.time() - start

        # Log error
        log_external_call(
            market_data_logger,
            provider="yfinance",
            operation="fetch_ohlc",
            duration_sec=duration,
            status="error",
            timeout_sec=timeout,
            ticker=ticker,
            error=str(e)
        )
        raise
```

## Example 2: Cognitive Operations

### Decision Enhancement

```python
from app.observability.structured_logging import cognitive_logger, log_operation

@router.post("/cognitive/enhance-decision")
async def enhance_decision(request: DecisionRequest):
    """Enhance decision with market brain"""

    with log_operation(
        cognitive_logger,
        "enhance_decision",
        theory_name=request.theory,
        ticker=request.ticker
    ) as context:
        # Add dynamic context
        context["confidence_threshold"] = 0.7

        # Execute enhancement
        result = await brain.enhance(request)

        # Add result metrics to context
        context["confidence_score"] = result.confidence
        context["action"] = result.action

        return result

# Logs output:
# INFO: Starting enhance_decision {"subsystem": "cognitive", "operation": "enhance_decision", "theory_name": "momentum_theory", "ticker": "TSLA"}
# INFO: Completed enhance_decision {"subsystem": "cognitive", "operation": "enhance_decision", "theory_name": "momentum_theory", "ticker": "TSLA", "duration_sec": 0.123, "confidence_score": 0.85, "action": "buy"}
```

### Learning Run with Timeout Monitoring

```python
from app.observability.structured_logging import learning_logger, log_operation, log_slowdown
import time

@router.post("/learning/train")
async def train_model(request: TrainingRequest):
    """Train model with timeout monitoring"""

    start = time.time()

    with log_operation(
        learning_logger,
        "train_model",
        theory_name=request.theory,
        dataset_size=len(request.data)
    ):
        # Execute training
        result = await trainer.train(request)

        duration = time.time() - start

        # Check for slowdown
        log_slowdown(
            learning_logger,
            operation="train_model",
            duration_sec=duration,
            threshold_sec=60.0,  # Expected under 60s
            theory_name=request.theory,
            epochs=request.epochs
        )

        return result
```

## Example 3: Paper Trading

### Trade Execution

```python
from app.observability.structured_logging import paper_lab_logger, log_operation

@router.post("/paper/trade")
async def execute_paper_trade(request: TradeRequest):
    """Execute paper trade with logging"""

    with log_operation(
        paper_lab_logger,
        "execute_trade",
        run_id=request.run_id,
        ticker=request.ticker
    ) as context:
        # Add trade details
        context["side"] = request.side
        context["quantity"] = request.quantity
        context["order_type"] = request.order_type

        # Execute trade
        result = await paper_engine.execute(request)

        # Add execution details
        context["fill_price"] = result.fill_price
        context["status"] = result.status

        return result

# Logs output:
# INFO: Starting execute_trade {"subsystem": "paper_lab", "operation": "execute_trade", "run_id": "run_12345", "ticker": "AAPL", "side": "buy", "quantity": 100, "order_type": "market"}
# INFO: Completed execute_trade {"subsystem": "paper_lab", "operation": "execute_trade", "run_id": "run_12345", "ticker": "AAPL", "side": "buy", "quantity": 100, "order_type": "market", "duration_sec": 0.045, "fill_price": 175.50, "status": "filled"}
```

## Example 4: Screener Operations

### Market Scan with Slowdown Detection

```python
from app.observability.structured_logging import screener_logger, log_operation, log_slowdown
import time

@router.post("/screener/scan")
async def scan_market(request: ScanRequest):
    """Scan market with performance monitoring"""

    start = time.time()

    with log_operation(
        screener_logger,
        "market_scan",
        preset=request.preset
    ) as context:
        # Execute scan
        results = await screener.scan(request)

        duration = time.time() - start

        # Add scan metrics
        context["tickers_scanned"] = len(request.tickers)
        context["results_count"] = len(results)

        # Check for slowdown
        if duration > 5.0:
            log_slowdown(
                screener_logger,
                operation="market_scan",
                duration_sec=duration,
                threshold_sec=5.0,
                tickers_scanned=len(request.tickers),
                preset=request.preset
            )

        return results
```

## Example 5: Chat/LLM Operations

### Chat Completion

```python
from app.observability.structured_logging import chat_logger, log_operation, log_external_call
import time

@router.post("/chat/completion")
async def chat_completion(request: ChatRequest):
    """Chat completion with LLM call logging"""

    with log_operation(
        chat_logger,
        "chat_completion",
        model=request.model,
        provider=request.provider
    ) as context:
        # Add request details
        context["message_count"] = len(request.messages)
        context["max_tokens"] = request.max_tokens

        # Make LLM call with timeout logging
        start = time.time()

        try:
            response = await llm_client.complete(request, timeout=60.0)
            duration = time.time() - start

            # Log external LLM call
            log_external_call(
                chat_logger,
                provider=request.provider,
                operation="chat_completion",
                duration_sec=duration,
                status="success",
                timeout_sec=60.0,
                model=request.model,
                tokens_used=response.usage.total_tokens
            )

            # Add response details to operation context
            context["tokens_used"] = response.usage.total_tokens
            context["finish_reason"] = response.finish_reason

            return response

        except asyncio.TimeoutError:
            duration = time.time() - start

            log_external_call(
                chat_logger,
                provider=request.provider,
                operation="chat_completion",
                duration_sec=duration,
                status="timeout",
                timeout_sec=60.0,
                model=request.model
            )
            raise

# Logs output:
# INFO: Starting chat_completion {"subsystem": "chat", "operation": "chat_completion", "model": "gpt-4", "provider": "openai", "message_count": 3, "max_tokens": 1000}
# DEBUG: External call: openai.chat_completion {"provider": "openai", "operation": "chat_completion", "duration_sec": 2.345, "status": "success", "timeout_sec": 60.0, "model": "gpt-4", "tokens_used": 456}
# INFO: Completed chat_completion {"subsystem": "chat", "operation": "chat_completion", "model": "gpt-4", "provider": "openai", "message_count": 3, "max_tokens": 1000, "duration_sec": 2.345, "tokens_used": 456, "finish_reason": "stop"}
```

## Example 6: News Operations

### RSS Feed Fetch

```python
from app.observability.structured_logging import get_structured_logger, log_external_call
import time
import urllib.request

news_logger = get_structured_logger("news")

async def fetch_rss_feed(url: str):
    """Fetch RSS feed with timeout logging"""

    start = time.time()

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ziggy-rss/1.0"})

        with urllib.request.urlopen(req, timeout=8.0) as resp:
            data = resp.read()
            duration = time.time() - start

            log_external_call(
                news_logger,
                provider="rss_feed",
                operation="fetch_feed",
                duration_sec=duration,
                status="success",
                timeout_sec=8.0,
                url=url,
                bytes_received=len(data)
            )

            return data

    except urllib.error.URLError as e:
        if "timeout" in str(e).lower():
            duration = time.time() - start

            log_external_call(
                news_logger,
                provider="rss_feed",
                operation="fetch_feed",
                duration_sec=duration,
                status="timeout",
                timeout_sec=8.0,
                url=url
            )
        raise
```

## Example 7: Signals Operations

### Signal Generation

```python
from app.observability.structured_logging import signals_logger, log_operation

@router.post("/signals/generate")
async def generate_signal(request: SignalRequest):
    """Generate trading signal with logging"""

    with log_operation(
        signals_logger,
        "generate_signal",
        ticker=request.ticker,
        strategy=request.strategy
    ) as context:
        # Generate signal
        signal = await signal_generator.generate(request)

        # Add signal details
        context["signal_type"] = signal.type
        context["strength"] = signal.strength
        context["confidence"] = signal.confidence

        return signal
```

## Example 8: Error Handling

### Operation with Error Logging

```python
from app.observability.structured_logging import trading_logger, log_operation

@router.post("/trade/execute")
async def execute_trade(request: TradeRequest):
    """Execute trade with automatic error logging"""

    try:
        with log_operation(
            trading_logger,
            "execute_trade",
            ticker=request.ticker,
            side=request.side
        ):
            # This will automatically log errors with full context
            result = await broker.execute(request)
            return result

    except Exception as e:
        # Error is already logged by log_operation context manager
        # Just handle the error appropriately
        raise HTTPException(status_code=500, detail=str(e))

# If an error occurs:
# ERROR: Failed execute_trade {"subsystem": "trading", "operation": "execute_trade", "ticker": "AAPL", "side": "buy", "duration_sec": 0.123, "error": "Insufficient funds", "error_type": "InsufficientFundsError"}
```

## Filtering and Analyzing Logs

### Filter by Subsystem

```bash
# View all trading logs
grep '"subsystem": "trading"' logs.json

# View all cognitive logs
grep '"subsystem": "cognitive"' logs.json
```

### Filter by Operation

```bash
# View all backtest operations
grep '"operation": "backtest"' logs.json

# View all enhance_decision operations
grep '"operation": "enhance_decision"' logs.json
```

### Find Slow Operations

```bash
# Find operations taking > 5 seconds
grep '"duration_sec"' logs.json | awk '$2 > 5.0'

# Find slow external calls
grep '"status": "timeout"' logs.json
```

### Track Specific Ticker

```bash
# All operations for AAPL
grep '"ticker": "AAPL"' logs.json

# All backtests for TSLA
grep '"ticker": "TSLA"' logs.json | grep '"operation": "backtest"'
```

### Monitor External Calls

```bash
# All external provider calls
grep '"provider":' logs.json

# Timeout incidents
grep '"status": "timeout"' logs.json

# Slow external calls (> 5s)
grep '"provider":' logs.json | awk '$duration_sec > 5.0'
```

## Best Practices

### 1. Always Use Context Manager

```python
# ✅ Good - uses context manager
with log_operation(logger, "operation_name", ticker=ticker):
    do_work()

# ❌ Bad - manual logging (harder to maintain)
logger.info(f"Starting operation for {ticker}")
start = time.time()
do_work()
logger.info(f"Completed in {time.time() - start}s")
```

### 2. Add Relevant Context

```python
# ✅ Good - includes relevant context
with log_operation(
    logger,
    "backtest",
    ticker=ticker,
    strategy=strategy,
    timeframe="1d",
    lookback_days=365
):
    do_backtest()

# ❌ Bad - missing useful context
with log_operation(logger, "backtest"):
    do_backtest()
```

### 3. Log External Calls

```python
# ✅ Good - logs external call with timing
start = time.time()
data = await provider.fetch()
log_external_call(logger, "provider", "fetch", time.time() - start, "success")

# ❌ Bad - no visibility into external call
data = await provider.fetch()
```

### 4. Check for Slowdowns

```python
# ✅ Good - alerts on unexpected slowness
if duration > threshold:
    log_slowdown(logger, "operation", duration, threshold)

# ❌ Bad - silent performance degradation
# (no one knows it's slow)
```

## Summary

Use structured logging to:

- ✅ Consistent log format across all subsystems
- ✅ Automatic duration tracking
- ✅ Error capture with full context
- ✅ External call monitoring
- ✅ Slowdown detection
- ✅ Easy filtering and analysis
- ✅ Better operational visibility
