# Observability Configuration Templates

This directory contains configuration templates for production monitoring, alerting, and dashboards.

## Files

### alerts.yaml

Alert rules configuration compatible with:

- Prometheus AlertManager
- Grafana Alerting
- Custom alerting systems (via webhook)

**Key features:**

- SLO-based alert rules
- Provider health monitoring
- WebSocket performance alerts
- Configurable notification channels
- Alert throttling rules

**Usage:**

1. Replace environment variable placeholders (`${SLACK_WEBHOOK_OPS}`, etc.)
2. Import into your monitoring system
3. Adjust thresholds based on your production requirements

### dashboards.json

Dashboard configuration for real-time monitoring:

- SLO compliance overview
- WebSocket performance metrics
- Provider health status
- Detailed performance tables

**Supported platforms:**

- Grafana
- Prometheus-compatible dashboards
- Custom visualization tools

**Usage:**

1. Import JSON into Grafana or monitoring platform
2. Configure data source to point to metrics API endpoint
3. Adjust refresh intervals as needed

## Integration

### Metrics API Endpoint

The dashboards and alerts query metrics from:

```
GET /__debug/metrics
```

### Example Response Structure

```json
{
  "websocket": {
    "total_connections": 42,
    "channels": {
      "market_data": {
        "queue_len": 5,
        "dropped_msgs": 0,
        "send_latency_ms": 23.5
      }
    }
  },
  "providers": {
    "providers": {
      "polygon": {
        "availability_pct": 99.8,
        "health_score": 0.95
      }
    }
  },
  "slo": {
    "compliance_pct": 100.0,
    "violations": []
  }
}
```

## Customization

### Adding New Alerts

To add a custom alert rule:

1. Add to `alerts.yaml`:

```yaml
- name: CustomAlert
  description: Custom alert description
  severity: warning
  condition:
    metric: your.metric.path
    threshold: 100
    operator: ">"
    duration: 5m
  actions:
    - notify: ops-team
  labels:
    component: custom
```

### Adding Dashboard Panels

To add a new dashboard panel:

1. Add to `dashboards.json` under `panels`:

```json
{
  "id": "custom_panel",
  "title": "Custom Metric",
  "type": "timeseries",
  "metrics": [
    {
      "query": "your.metric.path",
      "label": "Custom"
    }
  ],
  "position": { "x": 0, "y": 0, "w": 12, "h": 4 }
}
```

## Environment Variables

Required for alert notifications:

```bash
# Slack integration
export SLACK_WEBHOOK_OPS="https://hooks.slack.com/services/..."

# PagerDuty integration
export PAGERDUTY_INTEGRATION_KEY="your-integration-key"
```

## Testing

Test alert rules:

```bash
# Check metrics endpoint
curl http://localhost:8000/__debug/metrics

# Check SLO status
curl http://localhost:8000/__debug/slo

# Check provider health
curl http://localhost:8000/__debug/provider-health
```

## Production Deployment

1. **Validate configurations** before deployment
2. **Test alert delivery** to all channels
3. **Configure retention** for metrics data
4. **Set up escalation policies** for critical alerts
5. **Document on-call procedures**

## Support

For configuration issues:

- Review metrics API endpoint responses
- Validate JSON/YAML syntax
- Check environment variable configuration
- Consult main documentation at `docs/observability_slos.md`
