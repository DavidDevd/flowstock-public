FROM python:3.14.8-alpine3.24@sha256:f6a589d43c42b9e7f7dc67a12d37132491f362859a5d750607710cc56da3bc72 AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN python -m venv /opt/venv
COPY apps/api/requirements.lock /tmp/requirements.lock
RUN /opt/venv/bin/python -m pip install --upgrade pip==26.1.2 \
    && /opt/venv/bin/python -m pip install --requirement /tmp/requirements.lock

COPY apps/api/pyproject.toml /build/pyproject.toml
COPY apps/api/src /build/src
RUN /opt/venv/bin/python -m pip install --no-deps /build

FROM python:3.14.8-alpine3.24@sha256:f6a589d43c42b9e7f7dc67a12d37132491f362859a5d750607710cc56da3bc72 AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system --gid 10001 flowstock \
    && adduser --system --disabled-password --no-create-home \
        --uid 10001 --ingroup flowstock flowstock

COPY --from=builder /opt/venv /opt/venv
COPY apps/api/alembic.ini /app/alembic.ini
COPY apps/api/alembic /app/alembic
COPY deployment/docker/api-entrypoint.sh /app/api-entrypoint.sh

WORKDIR /app
USER 10001:10001
EXPOSE 8000

CMD ["sh", "/app/api-entrypoint.sh"]
