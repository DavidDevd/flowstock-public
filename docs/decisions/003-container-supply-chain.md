# ADR 003 — Container and supply-chain controls

**Status:** Accepted

Dependencies are locked and audited. Runtime images use multi-stage builds and non-root users. Compose adds read-only filesystems and `no-new-privileges` where supported. CI validates Compose, builds immutable candidates, scans HIGH/CRITICAL findings with Trivy and generates SPDX SBOMs.
