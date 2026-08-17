# Observability

The implemented platform exposes:

- `/api/v1/health/live` for process liveness;
- `/api/v1/health/ready` for dependency readiness;
- `/metrics` for Prometheus request metrics;
- JSON structured logs through structlog;
- correlation IDs propagated through request handling;
- optional OpenTelemetry export.

The development Compose profile includes Prometheus and Grafana with local-only example configuration. No private endpoint, dashboard identifier or operational environment is included.
