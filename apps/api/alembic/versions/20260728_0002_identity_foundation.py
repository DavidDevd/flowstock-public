"""Create Sprint 1 identity, session, RBAC and audit tables.

Revision ID: 20260728_0002
Revises: 20260726_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260728_0002"
down_revision: str | None = "20260726_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(180), nullable=False),
        schema="flowstock",
    )
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(80), nullable=False),
        schema="flowstock",
    )
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flowstock.roles.id"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flowstock.permissions.id"),
            primary_key=True,
        ),
        schema="flowstock",
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flowstock.roles.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema="flowstock",
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True, schema="flowstock")
    op.create_table(
        "authentication_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flowstock.users.id"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("csrf_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        schema="flowstock",
    )
    op.create_index(
        "ix_authentication_sessions_token_hash",
        "authentication_sessions",
        ["token_hash"],
        unique=True,
        schema="flowstock",
    )
    op.create_index(
        "ix_authentication_sessions_user_id",
        "authentication_sessions",
        ["user_id"],
        schema="flowstock",
    )
    op.create_table(
        "password_recoveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flowstock.users.id"),
            nullable=False,
        ),
        sa.Column("credential_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        schema="flowstock",
    )
    op.create_index(
        "ix_password_recoveries_credential_hash",
        "password_recoveries",
        ["credential_hash"],
        unique=True,
        schema="flowstock",
    )
    op.create_index(
        "ix_password_recoveries_user_id",
        "password_recoveries",
        ["user_id"],
        schema="flowstock",
    )
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(80)),
        sa.Column("outcome", sa.String(30), nullable=False),
        sa.Column("correlation_id", sa.String(100), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default="{}"),
        schema="flowstock",
    )
    op.create_index("ix_audit_events_action", "audit_events", ["action"], schema="flowstock")
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
        schema="flowstock",
    )
    roles = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        schema="flowstock",
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
        schema="flowstock",
    )
    permission_rows = [
        ("00000000-0000-4000-8000-000000000001", "users.manage", "Manage users and roles"),
        ("00000000-0000-4000-8000-000000000002", "audit.read", "Read audit events"),
        ("00000000-0000-4000-8000-000000000003", "operations.manage", "Manage operations"),
        ("00000000-0000-4000-8000-000000000004", "operations.execute", "Execute operations"),
        ("00000000-0000-4000-8000-000000000005", "dashboards.read", "Read dashboards"),
    ]
    role_rows = [
        ("10000000-0000-4000-8000-000000000001", "administrator", "Administrador"),
        ("10000000-0000-4000-8000-000000000002", "manager", "Gerente"),
        ("10000000-0000-4000-8000-000000000003", "cashier", "Operador"),
    ]
    op.bulk_insert(
        permissions,
        [{"id": item[0], "code": item[1], "description": item[2]} for item in permission_rows],
    )
    op.bulk_insert(
        roles,
        [{"id": item[0], "code": item[1], "name": item[2]} for item in role_rows],
    )
    grants = {
        role_rows[0][0]: [item[0] for item in permission_rows],
        role_rows[1][0]: [item[0] for item in permission_rows[2:]],
        role_rows[2][0]: [permission_rows[3][0]],
    }
    op.bulk_insert(
        role_permissions,
        [
            {"role_id": role_id, "permission_id": permission_id}
            for role_id, permission_ids in grants.items()
            for permission_id in permission_ids
        ],
    )


def downgrade() -> None:
    op.drop_table("audit_events", schema="flowstock")
    op.drop_table("password_recoveries", schema="flowstock")
    op.drop_table("authentication_sessions", schema="flowstock")
    op.drop_table("users", schema="flowstock")
    op.drop_table("role_permissions", schema="flowstock")
    op.drop_table("roles", schema="flowstock")
    op.drop_table("permissions", schema="flowstock")
