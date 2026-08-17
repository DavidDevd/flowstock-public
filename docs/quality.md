# Quality and validation

The repository defines these automated gates:

- Python formatting and linting with Ruff;
- strict backend type checking with mypy;
- backend tests and an 80% coverage threshold;
- Python dependency audit with pip-audit;
- frontend formatting, linting and TypeScript checks;
- Vitest tests with coverage;
- pnpm dependency audit and production build;
- Compose validation, immutable image builds, Trivy HIGH/CRITICAL gates and SPDX SBOM generation.

## Reproduced snapshot results

| Gate | Result |
| --- | --- |
| Backend tests | 24 passed |
| Backend coverage | 84.97% |
| Backend formatting, lint and strict mypy | Passed |
| Python dependency audit | No known vulnerabilities |
| Frontend tests | 22 passed across 9 files |
| Frontend statement coverage | 96.2% |
| Frontend format, lint, typecheck and build | Passed |
| pnpm dependency audit | No known vulnerabilities |

The `FlowStock CI` workflow independently validates the Compose definitions, builds the API and web images, scans both images with Trivy for HIGH and CRITICAL findings, generates SPDX SBOMs and retains the resulting container evidence as workflow artifacts.
