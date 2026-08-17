$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$windowsPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$unixPython = Join-Path $repositoryRoot ".venv/bin/python"
$pythonExecutable = if (Test-Path -LiteralPath $windowsPython) {
    $windowsPython
} elseif (Test-Path -LiteralPath $unixPython) {
    $unixPython
} else {
    $null
}

if (-not $pythonExecutable) {
    throw "Python virtual environment not found. Follow CONTRIBUTING.md."
}

Push-Location $repositoryRoot
try {
    & $pythonExecutable -m ruff format --check apps/api
    if ($LASTEXITCODE -ne 0) { throw "Backend format validation failed." }

    & $pythonExecutable -m ruff check apps/api
    if ($LASTEXITCODE -ne 0) { throw "Backend lint failed." }

    & $pythonExecutable -m mypy --config-file apps/api/pyproject.toml apps/api/src
    if ($LASTEXITCODE -ne 0) { throw "Backend type check failed." }

    & $pythonExecutable -m pytest apps/api
    if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }

    & $pythonExecutable -m pip_audit --requirement apps/api/requirements.lock
    if ($LASTEXITCODE -ne 0) { throw "Backend dependency audit failed." }

    & pnpm format:check
    if ($LASTEXITCODE -ne 0) { throw "Frontend format validation failed." }

    & pnpm lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }

    & pnpm typecheck
    if ($LASTEXITCODE -ne 0) { throw "Frontend type check failed." }

    & pnpm test:coverage
    if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed." }

    & pnpm audit
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency audit failed." }

    & pnpm build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
}
finally {
    Pop-Location
}
