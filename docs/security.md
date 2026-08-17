# Security model

Security controls demonstrated by the current implementation include:

- Argon2id password hashing;
- opaque session credentials, with only keyed hashes persisted;
- idle and absolute expiration;
- CSRF validation for authenticated mutations;
- server-side role and permission checks;
- immediate session revocation after sensitive account changes;
- trusted-host, CORS and response security headers;
- encryption and masking for customer documents;
- audit records for identity, user and master-data actions.

The repository contains placeholders only. Runtime secrets must be generated independently and stored outside version control. This public document intentionally excludes threat-model details, operational credentials and internal security findings.
