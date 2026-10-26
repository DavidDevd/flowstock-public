FROM python:3.15.0-alpine3.24@sha256:2699b90f4d562a22e2dd076c82f964032f64814204bff36d271a54ba4cc2c7e2 AS builder

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

FROM python:3.15.0-alpine3.24@sha256:2699b90f4d562a22e2dd076c82f964032f64814204bff36d271a54ba4cc2c7e2 AS runtime

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
