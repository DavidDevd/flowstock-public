from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Page[T](BaseModel):
    items: list[T]
    page: int
    size: int
    total: int
    pages: int


class CategoryInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    parent_id: uuid.UUID | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    parent_id: uuid.UUID | None = None
    active: bool | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    parent_id: uuid.UUID | None
    active: bool
    created_at: datetime
    updated_at: datetime


class UnitInput(BaseModel):
    code: str = Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9]+$")
    name: str = Field(min_length=1, max_length=80)


class UnitUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=12, pattern=r"^[A-Za-z0-9]+$")
    name: str | None = Field(default=None, min_length=1, max_length=80)
    active: bool | None = None


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    name: str
    active: bool
    created_at: datetime
    updated_at: datetime


class ProductInput(BaseModel):
    name: str = Field(min_length=1, max_length=140)
    description: str | None = Field(default=None, max_length=4000)
    sku: str = Field(min_length=1, max_length=60)
    barcode: str | None = Field(default=None, max_length=32, pattern=r"^[0-9]+$")
    brand: str | None = Field(default=None, max_length=80)
    category_id: uuid.UUID
    unit_id: uuid.UUID
    sale_price_minor: int = Field(default=0, ge=0)
    cost_price_minor: int = Field(default=0, ge=0)
    minimum_stock: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=3)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=140)
    description: str | None = Field(default=None, max_length=4000)
    sku: str | None = Field(default=None, min_length=1, max_length=60)
    barcode: str | None = Field(default=None, max_length=32, pattern=r"^[0-9]+$")
    brand: str | None = Field(default=None, max_length=80)
    category_id: uuid.UUID | None = None
    unit_id: uuid.UUID | None = None
    sale_price_minor: int | None = Field(default=None, ge=0)
    cost_price_minor: int | None = Field(default=None, ge=0)
    minimum_stock: Decimal | None = Field(default=None, ge=0, decimal_places=3)
    active: bool | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    sku: str
    barcode: str | None
    brand: str | None
    category_id: uuid.UUID
    category_name: str
    unit_id: uuid.UUID
    unit_code: str
    sale_price_minor: int
    cost_price_minor: int
    minimum_stock: Decimal
    active: bool
    created_at: datetime
    updated_at: datetime


class CustomerInput(BaseModel):
    kind: Literal["individual", "company"]
    name: str = Field(min_length=1, max_length=140)
    legal_name: str | None = Field(default=None, max_length=180)
    document: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(
        default=None,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    address: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)


class CustomerUpdate(BaseModel):
    kind: Literal["individual", "company"] | None = None
    name: str | None = Field(default=None, min_length=1, max_length=140)
    legal_name: str | None = Field(default=None, max_length=180)
    document: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(
        default=None,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    address: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)
    active: bool | None = None


class CustomerResponse(BaseModel):
    id: uuid.UUID
    kind: str
    name: str
    legal_name: str | None
    masked_document: str | None
    phone: str | None
    email: str | None
    address: str | None
    notes: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
