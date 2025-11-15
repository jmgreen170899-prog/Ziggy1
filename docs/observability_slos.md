# Observability & Service-Level Objectives (SLOs)

## Overview

This document describes ZiggyAI's unified observability infrastructure and service-level objectives (SLOs). The observability system provides consistent metrics, monitoring, and alerting across all key subsystems to ensure production readiness.

## Architecture

### Components

1. **Metrics Collection** (`backend/app/observability/metrics.py`)
   - Centralized metrics aggregation
   - WebSocket performance metrics
   - Provider health tracking
   - SLO compliance monitoring

2. **SLO Definitions** (`backend/app/observability/slo_targets.py`)
   - Global service-level objectives
   - Threshold definitions
   - Violation detection

3. **Alert Configuration** (`backend/app/observability/configs/alerts.yaml`)
   - Production alert rules
   - Notification channels
   - Escalation policies

4. **Dashboard Templates** (`backend/app/observability/configs/dashboards.json`)
   - Pre-configured monitoring dashboards
   - Grafana/Prometheus compatible
   - Real-time visualization

## Key Metrics

### WebSocket Metrics

The system tracks WebSocket performance across all channels:

| Metric                 | Description                  | Unit         |
| ---------------------- | ---------------------------- | ------------ |
| `queue_len`            | Current message queue length | messages     |
| `dropped_msgs`         | Total messages dropped       | count        |
| `send_latency_ms`      | Message delivery latency     | milliseconds |
| `subscribers`          | Active WebSocket connections | count        |
| `broadcasts_attempted` | Total broadcast attempts     | count        |
| `broadcasts_failed`    | Failed broadcast attempts    | count        |
| `avg_uptime_s`         | Average connection uptime    | seconds      |

**Collection**: WebSocket metrics are collected in real-time from the `ConnectionManager` in `app/core/websocket.py`.

### Provider Health Metrics

Health tracking for external data providers:

| Provider      | Metrics Tracked                         |
| ------------- | --------------------------------------- |
| **Polygon**   | API availability, latency, success rate |
| **Alpaca**    | Trading API health, response times      |
| **News**      | RSS feed availability, fetch success    |
| **FRED**      | Economic data availability              |
| **IEX Cloud** | Alternative market data health          |

**Per-Provider Metrics**:

- `availability_pct`: Provider uptime percentage
- `health_score`: Composite health score (0.0 - 1.0)
- `avg_latency_ms`: Average response latency
- `p95_latency_ms`: 95th percentile latency
- `success_rate`: Request success rate
- `consecutive_failures`: Current failure streak
- `total_events`: Total requests tracked

**Collection**: Provider metrics are collected via the `ProviderHealthManager` in `app/services/provider_health.py`.

## Service-Level Objectives (SLOs)

### 1. WebSocket Delivery Latency

**Target**: < 100 ms (p95)

**Description**: 95th percentile of WebSocket message delivery latency must remain below 100ms to ensure real-time user experience.

**Measurement**:

```python
from app.observability import get_websocket_metrics

metrics = get_websocket_metrics()
avg_latency = avg([channel['send_latency_ms']
                   for channel in metrics['channels'].values()])
```

**Impact**:

- User-facing: Real-time market updates, alerts, and notifications
- Critical for: Trading decisions, price alerts, news delivery

**Alert Threshold**: Sustained latency > 100ms for 5 minutes triggers warning

### 2. Queue Drop Rate

**Target**: < 0.1%

**Description**: Message queue drop rate across all channels must remain below 0.1% to prevent data loss.

**Measurement**:

```python
from app.observability import get_websocket_metrics

metrics = get_websocket_metrics()
total_dropped = sum([ch['dropped_msgs'] for ch in metrics['channels'].values()])
total_attempted = sum([ch['broadcasts_attempted'] for ch in metrics['channels'].values()])
drop_rate = (total_dropped / total_attempted) * 100 if total_attempted > 0 else 0
```

**Impact**:

- User-facing: Missed market updates, incomplete data streams
- Critical for: Data integrity, trading signals

**Alert Threshold**: Drop rate > 0.1% for 5 minutes triggers critical alert

### 3. Provider Availability

**Target**: > 99.5%

**Description**: External data provider availability must exceed 99.5% to ensure reliable data flow.

**Measurement**:

```python
from app.observability import get_provider_health_metrics

metrics = get_provider_health_metrics()
avg_availability = avg([prov['availability_pct']
                        for prov in metrics['providers'].values()])
```

**Impact**:

- System-wide: Data availability, trading capabilities
- Critical for: Market data, news feeds, economic indicators

**Alert Threshold**: Availability < 99.5% for 10 minutes triggers warning

## API Endpoints

### Get All Metrics

```http
GET /__debug/metrics
```

Returns comprehensive metrics from all subsystems:

```json
{
  "websocket": {
    "total_connections": 42,
    "channels": {
      "market_data": {
        "queue_len": 5,
        "dropped_msgs": 0,
        "send_latency_ms": 23.5,
        "subscribers": 10
      }
    }
  },
  "providers": {
    "providers": {
      "polygon": {
        "availability_pct": 99.8,
        "health_score": 0.95,
        "avg_latency_ms": 45.2
      }
    }
  },
  "slo": {
    "targets": [...],
    "violations": [],
    "compliance_pct": 100.0
  }
}
```

### Get SLO Status

```python
from app.observability import get_slo_status

status = get_slo_status()
# Returns:
# {
#   "targets": [...],
#   "violations": ["ws_delivery_latency_p95"],
#   "compliance_pct": 66.67,
#   "timestamp": 1699564943.2
# }
```

## Integration

### Prometheus Integration

The metrics can be exposed in Prometheus format by installing `prometheus-client`:

```python
from prometheus_client import Counter, Gauge, Histogram
from app.observability import get_all_metrics

# Example: Convert to Prometheus metrics
metrics = get_all_metrics()
```

### Grafana Dashboards

Use the provided dashboard configuration in `backend/app/observability/configs/dashboards.json`:

1. Import the JSON into Grafana
2. Configure data source (Prometheus/API endpoint)
3. Adjust refresh intervals and time ranges as needed

### Alert Manager

Alert rules in `backend/app/observability/configs/alerts.yaml` can be:

1. Imported into Prometheus AlertManager
2. Configured in Grafana Alerting
3. Integrated with custom alerting systems via webhook

## Monitoring Best Practices

### 1. Regular Review

- Review SLO compliance weekly
- Investigate trends in provider health
- Monitor WebSocket performance during peak hours

### 2. Alert Response

- **Critical Alerts**: Page on-call engineer immediately
- **Warning Alerts**: Notify ops team, investigate within 1 hour
- **Info Alerts**: Log for review during business hours

### 3. Capacity Planning

- Monitor queue lengths to identify capacity constraints
- Track connection growth for scaling decisions
- Review provider latency trends for optimization

### 4. Incident Response

When SLO violations occur:

1. Check `/health` and `/__debug/metrics` endpoints
2. Review provider health for external failures
3. Investigate WebSocket queue backlogs
4. Check recent deployments or configuration changes
5. Review application logs for errors

## Custom Metrics

Add custom application metrics using the `MetricsCollector`:

```python
from app.observability.metrics import get_metrics_collector

collector = get_metrics_collector()

# Set a metric value
collector.set_metric("custom_metric_name", 42.5)

# Increment a counter
collector.increment_metric("requests_total", 1)

# Retrieve metrics
value = collector.get_metric("custom_metric_name")
```

## Testing

Run observability tests:

```bash
cd backend
pytest tests/test_observability.py -v
```

## Production Deployment

### Environment Variables

Configure notification channels:

```bash
export SLACK_WEBHOOK_OPS="https://hooks.slack.com/..."
export PAGERDUTY_INTEGRATION_KEY="..."
```

### Monitoring Setup

1. Deploy metrics collection to production
2. Configure alert notification channels
3. Import Grafana dashboards
4. Set up alert rules in monitoring system
5. Test alert delivery paths

### Validation

Verify observability is working:

```bash
# Check metrics endpoint
curl http://localhost:8000/__debug/metrics

# Check SLO status
curl http://localhost:8000/__debug/metrics | jq .slo

# Verify provider health
curl http://localhost:8000/__debug/metrics | jq .providers
```

## Troubleshooting

### Metrics Not Updating

- Verify WebSocket connections are active
- Check provider health tracking is enabled
- Ensure metric collection isn't blocked by errors

### High Latency

- Check queue lengths for backpressure
- Review provider response times
- Investigate network connectivity

### SLO Violations

- Review detailed metrics for root cause
- Check recent configuration changes
- Verify external provider status

## References

- [WebSocket Implementation](../backend/app/core/websocket.py)
- [Provider Health Tracking](../backend/app/services/provider_health.py)
- [Metrics API](../backend/app/observability/metrics.py)
- [SLO Definitions](../backend/app/observability/slo_targets.py)

## Support

For observability issues:

1. Check application logs
2. Review metrics dashboard
3. Consult on-call engineer
4. Escalate to platform team if needed
