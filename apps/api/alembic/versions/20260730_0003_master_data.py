"""Create Sprint 2 catalog and customer master data.

Revision ID: 20260730_0003
Revises: 20260728_0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260730_0003"
down_revision: str | None = "20260728_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flowstock.categories.id"),
        ),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "parent_id IS NULL OR parent_id <> id", name="ck_category_not_self_parent"
        ),
        schema="flowstock",
    )
    op.create_index(
        "uq_categories_name_lower",
        "categories",
        [sa.text("lower(name)")],
        unique=True,
        schema="flowstock",
    )
    op.create_table(
        "units_of_measure",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(12), nullable=False, unique=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema="flowstock",
    )
    op.create_index(
        "uq_units_name_lower",
        "units_of_measure",
        [sa.text("lower(name)")],
        unique=True,
        schema="flowstock",
    )
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(140), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("sku", sa.String(60), nullable=False, unique=True),
        sa.Column("barcode", sa.String(32), unique=True),
        sa.Column("brand", sa.String(80)),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flowstock.categories.id"),
            nullable=False,
        ),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flowstock.units_of_measure.id"),
            nullable=False,
        ),
        sa.Column("sale_price_minor", sa.Integer(), nullable=False),
        sa.Column("cost_price_minor", sa.Integer(), nullable=False),
        sa.Column("minimum_stock", sa.Numeric(18, 3), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("sale_price_minor >= 0", name="ck_product_sale_price_nonnegative"),
        sa.CheckConstraint("cost_price_minor >= 0", name="ck_product_cost_price_nonnegative"),
        sa.CheckConstraint("minimum_stock >= 0", name="ck_product_minimum_stock_nonnegative"),
        schema="flowstock",
    )
    op.create_index("ix_products_name", "products", ["name"], schema="flowstock")
    op.create_index("ix_products_category_id", "products", ["category_id"], schema="flowstock")
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("name", sa.String(140), nullable=False),
        sa.Column("legal_name", sa.String(180)),
        sa.Column("phone", sa.String(30)),
        sa.Column("email", sa.String(254)),
        sa.Column("address", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('individual', 'company')", name="ck_customer_kind"),
        schema="flowstock",
    )
    op.create_index("ix_customers_name", "customers", ["name"], schema="flowstock")
    op.create_table(
        "customer_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flowstock.customers.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("document_type", sa.String(10), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("document_hash", sa.String(64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("document_type IN ('cpf', 'cnpj')", name="ck_customer_document_type"),
        schema="flowstock",
    )
    op.create_index(
        "uq_customer_document_hash_active",
        "customer_documents",
        ["document_hash"],
        unique=True,
        schema="flowstock",
        postgresql_where=sa.text("active"),
    )
    _seed_permissions_and_units()


def _seed_permissions_and_units() -> None:
    op.execute(
        """
        INSERT INTO flowstock.permissions (id, code, description) VALUES
          ('00000000-0000-4000-8000-000000000006', 'catalog.manage', 'Manage catalog'),
          ('00000000-0000-4000-8000-000000000007', 'customers.manage', 'Manage customers')
        """
    )
    op.execute(
        """
        INSERT INTO flowstock.role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM flowstock.roles r
        JOIN flowstock.permissions p ON
          (p.code = 'catalog.manage' AND r.code IN ('administrator', 'manager'))
          OR (p.code = 'customers.manage' AND r.code IN ('administrator', 'manager', 'cashier'))
        """
    )
    op.execute(
        """
        INSERT INTO flowstock.units_of_measure (id, code, name, active, created_at, updated_at)
        VALUES
          ('20000000-0000-4000-8000-000000000001', 'UN', 'Unidade', true, now(), now()),
          ('20000000-0000-4000-8000-000000000002', 'KG', 'Quilograma', true, now(), now()),
          ('20000000-0000-4000-8000-000000000003', 'CX', 'Caixa', true, now(), now()),
          ('20000000-0000-4000-8000-000000000004', 'LT', 'Litro', true, now(), now()),
          ('20000000-0000-4000-8000-000000000005', 'M', 'Metro', true, now(), now()),
          ('20000000-0000-4000-8000-000000000006', 'PCT', 'Pacote', true, now(), now())
        """
    )


def downgrade() -> None:
    op.drop_table("customer_documents", schema="flowstock")
    op.drop_table("customers", schema="flowstock")
    op.drop_table("products", schema="flowstock")
    op.drop_table("units_of_measure", schema="flowstock")
    op.drop_table("categories", schema="flowstock")
    op.execute(
        """
        DELETE FROM flowstock.role_permissions
        WHERE permission_id IN (
          SELECT id
          FROM flowstock.permissions
          WHERE code IN ('catalog.manage', 'customers.manage')
        )
        """
    )
    op.execute(
        """
        DELETE FROM flowstock.permissions
        WHERE code IN ('catalog.manage', 'customers.manage')
        """
    )
