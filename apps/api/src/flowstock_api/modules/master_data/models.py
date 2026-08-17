from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flowstock_api.modules.identity.models import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("parent_id IS NULL OR parent_id <> id", name="ck_category_not_self_parent"),
        {"schema": "flowstock"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flowstock.categories.id")
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    parent: Mapped[Category | None] = relationship(remote_side="Category.id", lazy="joined")


class UnitOfMeasure(Base):
    __tablename__ = "units_of_measure"
    __table_args__ = ({"schema": "flowstock"},)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(12), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("sale_price_minor >= 0", name="ck_product_sale_price_nonnegative"),
        CheckConstraint("cost_price_minor >= 0", name="ck_product_cost_price_nonnegative"),
        CheckConstraint("minimum_stock >= 0", name="ck_product_minimum_stock_nonnegative"),
        {"schema": "flowstock"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(140))
    description: Mapped[str | None] = mapped_column(Text)
    sku: Mapped[str] = mapped_column(String(60), unique=True)
    barcode: Mapped[str | None] = mapped_column(String(32), unique=True)
    brand: Mapped[str | None] = mapped_column(String(80))
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flowstock.categories.id")
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flowstock.units_of_measure.id")
    )
    sale_price_minor: Mapped[int] = mapped_column(Integer, default=0)
    cost_price_minor: Mapped[int] = mapped_column(Integer, default=0)
    minimum_stock: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=Decimal("0"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    category: Mapped[Category] = relationship(lazy="joined")
    unit: Mapped[UnitOfMeasure] = relationship(lazy="joined")


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("kind IN ('individual', 'company')", name="ck_customer_kind"),
        {"schema": "flowstock"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(140))
    legal_name: Mapped[str | None] = mapped_column(String(180))
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(254))
    address: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    document: Mapped[CustomerDocument | None] = relationship(
        back_populates="customer", lazy="joined", uselist=False
    )


class CustomerDocument(Base):
    __tablename__ = "customer_documents"
    __table_args__ = (
        CheckConstraint("document_type IN ('cpf', 'cnpj')", name="ck_customer_document_type"),
        Index(
            "uq_customer_document_hash_active",
            "document_hash",
            unique=True,
            postgresql_where=text("active"),
        ),
        {"schema": "flowstock"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flowstock.customers.id"), unique=True
    )
    document_type: Mapped[str] = mapped_column(String(10))
    encrypted_value: Mapped[str] = mapped_column(Text)
    document_hash: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    customer: Mapped[Customer] = relationship(back_populates="document")
