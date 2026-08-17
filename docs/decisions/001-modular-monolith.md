# ADR 001 — Modular monolith

**Status:** Accepted

FlowStock keeps identity and master-data boundaries inside one deployable FastAPI application. This preserves transactional simplicity and clear module ownership while the product evolves. Distributed services may be evaluated only when evidence justifies their operational cost.
