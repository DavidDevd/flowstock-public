# FlowStock API

FastAPI modular-monolith core for the implemented FlowStock increments:

- platform health, readiness, metrics and structured logging;
- identity, opaque sessions, RBAC and user management;
- categories, units, products and customers;
- PostgreSQL migrations and audit events.

Install the locked development environment from the repository root:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install --requirement apps/api/requirements-dev.lock
./.venv/Scripts/python.exe -m pip install --no-deps --editable apps/api
```

Set the required `FLOWSTOCK_*` variables, apply migrations with `alembic upgrade head`, then run `flowstock-api`.
