"""Create the non-business application schema.

Revision ID: 20260726_0001
Revises:
Create Date: 2026-07-26
"""

from collections.abc import Sequence

revision: str = "20260726_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """The Alembic environment creates the flowstock schema and version table."""


def downgrade() -> None:
    """Keep the empty schema; destructive schema removal is an operational act."""
