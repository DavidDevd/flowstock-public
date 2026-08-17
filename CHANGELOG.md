# Changelog

All notable public technical changes to FlowStock are recorded here.

## Unreleased

### Changed

- Restored strict backend type-check configuration in CI.
- Synchronized runtime and development dependency locks.
- Updated `cryptography` to `50.0.0`.
- Pinned patched transitive frontend dependencies identified by audit.

## 0.3.0 — Master Data

### Added

- Categories with an optional single-level parent hierarchy.
- Seeded and manageable units of measure.
- Products with SKU, optional barcode, category, unit, prices in minor units and minimum stock.
- Individual and company customers.
- Local CPF/CNPJ validation, encryption at rest, keyed active uniqueness and masked API responses.
- Search, pagination, sorting, logical activation/deactivation, RBAC and audit events.
- Responsive authenticated master-data interface.

## 0.2.0 — Identity and Security

### Added

- Users and Administrator, Manager and Cashier roles.
- Argon2id password storage and PostgreSQL-backed opaque sessions.
- CSRF protection, logout and immediate session revocation.
- Temporary-password replacement and Administrator-assisted recovery.
- User creation, editing, role changes and activation/deactivation.
- Identity audit events and the authenticated React workspace.

## 0.1.0 — Engineering Foundation

### Added

- FastAPI, React, PostgreSQL and container foundations.
- Health, readiness, metrics, structured logging and error contracts.
- Development and Acceptance environments.
- CI, quality, image scanning and SBOM controls.
