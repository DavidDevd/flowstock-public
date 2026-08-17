# Contributing to FlowStock

## Scope

- Keep pull requests focused and describe the behavior that remains unchanged.
- Update tests and public documentation with implementation changes.
- Never commit credentials, personal data or private environment details.

## Branches and review

- Prefer short-lived branches and semantic commit messages.
- Require review and green CI before merging.
- Review security, migrations and releases explicitly.

## Backend setup

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install --requirement apps/api/requirements-dev.lock
./.venv/Scripts/python.exe -m pip install --no-deps --editable apps/api
```

## Frontend setup

```powershell
corepack enable
pnpm install --frozen-lockfile
```

## Required validation

Run `./quality/check.ps1` before requesting review.
