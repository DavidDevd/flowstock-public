from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, TypeVar

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from flowstock_api.modules.identity.models import AuditEvent, User
from flowstock_api.modules.identity.security import hash_secret
from flowstock_api.modules.identity.service import IdentityService
from flowstock_api.modules.master_data.models import (
    Category,
    Customer,
    CustomerDocument,
    Product,
    UnitOfMeasure,
)
from flowstock_api.modules.master_data.repository import SqlAlchemyRepository
from flowstock_api.modules.master_data.schemas import (
    CategoryInput,
    CategoryResponse,
    CustomerInput,
    CustomerResponse,
    Page,
    ProductInput,
    ProductResponse,
    UnitInput,
    UnitResponse,
)
from flowstock_api.modules.master_data.security import (
    DocumentCipher,
    document_type,
    mask_document,
    normalize_document,
)

T = TypeVar("T")


class MasterDataService:
    def __init__(
        self,
        database: Session,
        *,
        secret_hash_key: str,
        data_encryption_key: str,
    ) -> None:
        self.database = database
        self.categories = SqlAlchemyRepository(database, Category)
        self.units = SqlAlchemyRepository(database, UnitOfMeasure)
        self.products = SqlAlchemyRepository(database, Product)
        self.customers = SqlAlchemyRepository(database, Customer)
        self.cipher = DocumentCipher(data_encryption_key)
        self.secret_hash_key = secret_hash_key

    def list_categories(
        self,
        *,
        user: User,
        page: int,
        size: int,
        search: str,
        active: bool | None,
        sort: str,
        descending: bool,
    ) -> Page[CategoryResponse]:
        self._require_catalog(user)
        statement = select(Category)
        if search:
            statement = statement.where(
                or_(Category.name.ilike(f"%{search}%"), Category.description.ilike(f"%{search}%"))
            )
        if active is not None:
            statement = statement.where(Category.active == active)
        columns = {"name": Category.name, "created_at": Category.created_at}
        result = self.categories.page(
            statement,
            page=page,
            size=size,
            sort_column=columns.get(sort, Category.name),
            descending=descending,
        )
        return Page[CategoryResponse](
            items=[CategoryResponse.model_validate(item) for item in result.items],
            page=result.page,
            size=result.size,
            total=result.total,
            pages=result.pages,
        )

    def create_category(self, payload: CategoryInput, user: User, correlation_id: str) -> Category:
        self._require_catalog(user)
        self._validate_parent(payload.parent_id)
        now = datetime.now(UTC)
        category = self.categories.add(
            Category(
                name=payload.name.strip(),
                description=_clean(payload.description),
                parent_id=payload.parent_id,
                active=True,
                created_at=now,
                updated_at=now,
            )
        )
        self._audit("categories.create", category.id, user, correlation_id)
        self.database.commit()
        return category

    def get_category(self, category_id: uuid.UUID, user: User) -> Category:
        self._require_catalog(user)
        return self._required(self.categories.get(category_id), "Categoria não encontrada.")

    def update_category(
        self,
        category_id: uuid.UUID,
        changes: dict[str, Any],
        user: User,
        correlation_id: str,
    ) -> Category:
        self._require_catalog(user)
        category = self._required(self.categories.get(category_id), "Categoria não encontrada.")
        if "parent_id" in changes:
            self._validate_parent(changes["parent_id"], category_id)
        self._apply(category, changes, {"name", "description", "parent_id", "active"})
        category.updated_at = datetime.now(UTC)
        self._audit("categories.update", category.id, user, correlation_id)
        self.database.commit()
        return category

    def list_units(
        self,
        *,
        user: User,
        page: int,
        size: int,
        search: str,
        active: bool | None,
        sort: str,
        descending: bool,
    ) -> Page[UnitResponse]:
        self._require_catalog(user)
        statement = select(UnitOfMeasure)
        if search:
            statement = statement.where(
                or_(
                    UnitOfMeasure.code.ilike(f"%{search}%"),
                    UnitOfMeasure.name.ilike(f"%{search}%"),
                )
            )
        if active is not None:
            statement = statement.where(UnitOfMeasure.active == active)
        columns = {"code": UnitOfMeasure.code, "name": UnitOfMeasure.name}
        result = self.units.page(
            statement,
            page=page,
            size=size,
            sort_column=columns.get(sort, UnitOfMeasure.code),
            descending=descending,
        )
        return Page[UnitResponse](
            items=[UnitResponse.model_validate(item) for item in result.items],
            page=result.page,
            size=result.size,
            total=result.total,
            pages=result.pages,
        )

    def create_unit(self, payload: UnitInput, user: User, correlation_id: str) -> UnitOfMeasure:
        self._require_catalog(user)
        now = datetime.now(UTC)
        unit = self.units.add(
            UnitOfMeasure(
                code=payload.code.strip().upper(),
                name=payload.name.strip(),
                active=True,
                created_at=now,
                updated_at=now,
            )
        )
        self._audit("units.create", unit.id, user, correlation_id)
        self.database.commit()
        return unit

    def get_unit(self, unit_id: uuid.UUID, user: User) -> UnitOfMeasure:
        self._require_catalog(user)
        return self._required(self.units.get(unit_id), "Unidade não encontrada.")

    def update_unit(
        self,
        unit_id: uuid.UUID,
        changes: dict[str, Any],
        user: User,
        correlation_id: str,
    ) -> UnitOfMeasure:
        self._require_catalog(user)
        unit = self._required(self.units.get(unit_id), "Unidade não encontrada.")
        self._apply(unit, changes, {"code", "name", "active"})
        unit.code = unit.code.upper()
        unit.updated_at = datetime.now(UTC)
        self._audit("units.update", unit.id, user, correlation_id)
        self.database.commit()
        return unit

    def list_products(
        self,
        *,
        user: User,
        page: int,
        size: int,
        search: str,
        active: bool | None,
        category_id: uuid.UUID | None,
        unit_id: uuid.UUID | None,
        sort: str,
        descending: bool,
    ) -> Page[ProductResponse]:
        self._require_catalog(user)
        statement = select(Product)
        if search:
            statement = statement.where(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%"),
                    Product.barcode.ilike(f"%{search}%"),
                )
            )
        if active is not None:
            statement = statement.where(Product.active == active)
        if category_id is not None:
            statement = statement.where(Product.category_id == category_id)
        if unit_id is not None:
            statement = statement.where(Product.unit_id == unit_id)
        columns = {"name": Product.name, "sku": Product.sku, "created_at": Product.created_at}
        result = self.products.page(
            statement,
            page=page,
            size=size,
            sort_column=columns.get(sort, Product.name),
            descending=descending,
        )
        return Page[ProductResponse](
            items=[self.product_response(item) for item in result.items],
            page=result.page,
            size=result.size,
            total=result.total,
            pages=result.pages,
        )

    def create_product(self, payload: ProductInput, user: User, correlation_id: str) -> Product:
        self._require_catalog(user)
        category, unit = self._validate_product_references(payload.category_id, payload.unit_id)
        now = datetime.now(UTC)
        values = payload.model_dump()
        values.update(
            name=payload.name.strip(),
            sku=payload.sku.strip().upper(),
            barcode=_clean(payload.barcode),
            brand=_clean(payload.brand),
        )
        product = self.products.add(
            Product(
                **values,
                category=category,
                unit=unit,
                active=True,
                created_at=now,
                updated_at=now,
            )
        )
        self._audit("products.create", product.id, user, correlation_id)
        self.database.commit()
        return product

    def get_product(self, product_id: uuid.UUID, user: User) -> ProductResponse:
        self._require_catalog(user)
        return self.product_response(
            self._required(self.products.get(product_id), "Produto não encontrado.")
        )

    def update_product(
        self,
        product_id: uuid.UUID,
        changes: dict[str, Any],
        user: User,
        correlation_id: str,
    ) -> Product:
        self._require_catalog(user)
        product = self._required(self.products.get(product_id), "Produto não encontrado.")
        category_id = changes.get("category_id", product.category_id)
        unit_id = changes.get("unit_id", product.unit_id)
        category, unit = self._validate_product_references(category_id, unit_id)
        self._apply(
            product,
            changes,
            {
                "name",
                "description",
                "sku",
                "barcode",
                "brand",
                "category_id",
                "unit_id",
                "sale_price_minor",
                "cost_price_minor",
                "minimum_stock",
                "active",
            },
        )
        product.category = category
        product.unit = unit
        product.sku = product.sku.upper()
        product.updated_at = datetime.now(UTC)
        self._audit("products.update", product.id, user, correlation_id)
        self.database.commit()
        return product

    def list_customers(
        self,
        *,
        user: User,
        page: int,
        size: int,
        search: str,
        active: bool | None,
        sort: str,
        descending: bool,
    ) -> Page[CustomerResponse]:
        IdentityService.require_permission(user, "customers.manage")
        statement = select(Customer)
        if search:
            statement = statement.where(
                or_(
                    Customer.name.ilike(f"%{search}%"),
                    Customer.legal_name.ilike(f"%{search}%"),
                    Customer.email.ilike(f"%{search}%"),
                )
            )
        if active is not None:
            statement = statement.where(Customer.active == active)
        columns = {"name": Customer.name, "created_at": Customer.created_at}
        result = self.customers.page(
            statement,
            page=page,
            size=size,
            sort_column=columns.get(sort, Customer.name),
            descending=descending,
        )
        return Page[CustomerResponse](
            items=[self.customer_response(item) for item in result.items],
            page=result.page,
            size=result.size,
            total=result.total,
            pages=result.pages,
        )

    def create_customer(self, payload: CustomerInput, user: User, correlation_id: str) -> Customer:
        IdentityService.require_permission(user, "customers.manage")
        self._validate_customer_names(payload.kind, payload.legal_name)
        now = datetime.now(UTC)
        customer = self.customers.add(
            Customer(
                kind=payload.kind,
                name=payload.name.strip(),
                legal_name=_clean(payload.legal_name),
                phone=_clean(payload.phone),
                email=_clean(payload.email),
                address=_clean(payload.address),
                notes=_clean(payload.notes),
                active=True,
                created_at=now,
                updated_at=now,
            )
        )
        if payload.document:
            customer.document = self._new_document(customer.id, payload.kind, payload.document)
        self._audit("customers.create", customer.id, user, correlation_id)
        self.database.commit()
        return customer

    def get_customer(self, customer_id: uuid.UUID, user: User) -> CustomerResponse:
        IdentityService.require_permission(user, "customers.manage")
        return self.customer_response(
            self._required(self.customers.get(customer_id), "Cliente não encontrado.")
        )

    def update_customer(
        self,
        customer_id: uuid.UUID,
        changes: dict[str, Any],
        user: User,
        correlation_id: str,
    ) -> Customer:
        IdentityService.require_permission(user, "customers.manage")
        customer = self._required(self.customers.get(customer_id), "Cliente não encontrado.")
        new_kind = changes.get("kind", customer.kind)
        self._validate_customer_names(new_kind, changes.get("legal_name", customer.legal_name))
        document_supplied = "document" in changes
        new_document = changes.pop("document", None)
        if new_kind != customer.kind and customer.document is not None and not document_supplied:
            raise ValueError("Informe um documento compatível ao alterar o tipo de cliente.")
        self._apply(
            customer,
            changes,
            {"kind", "name", "legal_name", "phone", "email", "address", "notes", "active"},
        )
        customer.updated_at = datetime.now(UTC)
        if document_supplied:
            self._replace_document(customer, new_document)
        if customer.document is not None:
            customer.document.active = customer.active
        self._audit("customers.update", customer.id, user, correlation_id)
        self.database.commit()
        return customer

    def product_response(self, product: Product) -> ProductResponse:
        return ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            sku=product.sku,
            barcode=product.barcode,
            brand=product.brand,
            category_id=product.category_id,
            category_name=product.category.name,
            unit_id=product.unit_id,
            unit_code=product.unit.code,
            sale_price_minor=product.sale_price_minor,
            cost_price_minor=product.cost_price_minor,
            minimum_stock=product.minimum_stock,
            active=product.active,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def customer_response(self, customer: Customer) -> CustomerResponse:
        masked = None
        if customer.document is not None:
            masked = mask_document(self.cipher.decrypt(customer.document.encrypted_value))
        return CustomerResponse(
            id=customer.id,
            kind=customer.kind,
            name=customer.name,
            legal_name=customer.legal_name,
            masked_document=masked,
            phone=customer.phone,
            email=customer.email,
            address=customer.address,
            notes=customer.notes,
            active=customer.active,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )

    def _new_document(self, customer_id: uuid.UUID, kind: str, value: str) -> CustomerDocument:
        normalized = normalize_document(value)
        kind_for_document = document_type(normalized)
        expected = "cpf" if kind == "individual" else "cnpj"
        if kind_for_document != expected:
            raise ValueError("O documento não corresponde ao tipo de cliente.")
        return CustomerDocument(
            customer_id=customer_id,
            document_type=kind_for_document,
            encrypted_value=self.cipher.encrypt(normalized),
            document_hash=hash_secret(normalized, self.secret_hash_key),
            active=True,
        )

    def _replace_document(self, customer: Customer, value: str | None) -> None:
        if not value:
            if customer.document is not None:
                self.database.delete(customer.document)
                customer.document = None
            return
        replacement = self._new_document(customer.id, customer.kind, value)
        if customer.document is None:
            customer.document = replacement
        else:
            customer.document.document_type = replacement.document_type
            customer.document.encrypted_value = replacement.encrypted_value
            customer.document.document_hash = replacement.document_hash

    def _validate_parent(
        self, parent_id: uuid.UUID | None, category_id: uuid.UUID | None = None
    ) -> None:
        if parent_id is None:
            return
        if parent_id == category_id:
            raise ValueError("Uma categoria não pode ser pai de si mesma.")
        parent = self._required(self.categories.get(parent_id), "Categoria pai não encontrada.")
        if not parent.active or parent.parent_id is not None:
            raise ValueError("A categoria pai deve estar ativa e no primeiro nível.")

    def _validate_product_references(
        self, category_id: uuid.UUID, unit_id: uuid.UUID
    ) -> tuple[Category, UnitOfMeasure]:
        category = self._required(self.categories.get(category_id), "Categoria não encontrada.")
        unit = self._required(self.units.get(unit_id), "Unidade não encontrada.")
        if not category.active or not unit.active:
            raise ValueError("Categoria e unidade devem estar ativas.")
        return category, unit

    @staticmethod
    def _validate_customer_names(kind: str, legal_name: str | None) -> None:
        if kind == "company" and not legal_name:
            raise ValueError("Razão social é obrigatória para pessoa jurídica.")

    @staticmethod
    def _require_catalog(user: User) -> None:
        IdentityService.require_permission(user, "catalog.manage")

    @staticmethod
    def _required(value: T | None, message: str) -> T:
        if value is None:
            raise ValueError(message)
        return value

    @staticmethod
    def _apply(entity: Any, changes: dict[str, Any], allowed: set[str]) -> None:
        for field, value in changes.items():
            if field in allowed:
                if isinstance(value, str):
                    value = value.strip()
                setattr(entity, field, value)

    def _audit(self, action: str, resource_id: uuid.UUID, user: User, correlation_id: str) -> None:
        self.database.add(
            AuditEvent(
                occurred_at=datetime.now(UTC),
                actor_user_id=user.id,
                action=action,
                resource_type=action.split(".", maxsplit=1)[0],
                resource_id=str(resource_id),
                outcome="success",
                correlation_id=correlation_id,
                details={},
            )
        )


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
