# ADR 002 — Opaque sessions and server-side authorization

**Status:** Accepted

The browser receives an opaque session credential. The server persists only a keyed hash, enforces idle and absolute expiration, validates CSRF on authenticated mutations and evaluates permissions server-side. Sensitive account changes revoke active sessions immediately.
