FROM python:3.14.7-alpine3.24@sha256:05b2b8b732ecd268fee8727a369f936f022d1321b59befd13c30ede22769dcdc AS builder

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

FROM python:3.14.7-alpine3.24@sha256:05b2b8b732ecd268fee8727a369f936f022d1321b59befd13c30ede22769dcdc AS runtime

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
