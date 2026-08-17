#!/bin/sh
set -eu

if [ "${FLOWSTOCK_RUN_MIGRATIONS:-false}" = "true" ]; then
  alembic upgrade head
fi

exec uvicorn flowstock_api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips="${FLOWSTOCK_TRUSTED_PROXY_IPS:-127.0.0.1}"
