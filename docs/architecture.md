# Public architecture

FlowStock uses a modular monolith so implemented product boundaries remain explicit without introducing distributed-system complexity prematurely.

## Runtime

1. React and TypeScript provide the authenticated browser workspace.
2. Caddy routes API and metrics traffic and serves the web application through Nginx.
3. FastAPI exposes platform, identity, user-management and master-data routes.
4. SQLAlchemy and Alembic manage PostgreSQL persistence and schema evolution.

## Backend boundaries

- `api`: HTTP routes, dependencies and error contracts.
- `modules.identity`: users, roles, permissions, sessions and audit events.
- `modules.master_data`: categories, units, products and customers.
- `infrastructure`: database integration.
- middleware and observability: correlation, security headers, logs, metrics and tracing.

The application code is the source of truth. This document intentionally omits private planning, infrastructure and operational topology.
