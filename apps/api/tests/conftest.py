from __future__ import annotations

import os

os.environ.setdefault(
    "FLOWSTOCK_DATABASE_URL",
    "postgresql+psycopg://flowstock:test-only@localhost:5432/flowstock_test",
)
os.environ.setdefault(
    "FLOWSTOCK_SECRET_HASH_KEY",
    "test-only-secret-hash-key-at-least-32-characters",
)
os.environ.setdefault(
    "FLOWSTOCK_DATA_ENCRYPTION_KEY",
    "test-only-data-encryption-key-at-least-32-characters",
)
