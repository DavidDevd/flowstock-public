from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from flowstock_api.modules.identity.models import Permission, Role, User
from flowstock_api.modules.identity.service import PermissionDeniedError
from flowstock_api.modules.master_data.models import (
    Category,
    Customer,
    Product,
    UnitOfMeasure,
)
from flowstock_api.modules.master_data.repository import RepositoryPage, SqlAlchemyRepository
from flowstock_api.modules.master_data.schemas import (
    CategoryInput,
    CustomerInput,
    ProductInput,
    UnitInput,
)
from flowstock_api.modules.master_data.security import (
    DocumentCipher,
    document_type,
    mask_document,
    normalize_document,
)
from flowstock_api.modules.master_data.service import MasterDataService

SECRET_KEY = "test-only-secret-hash-key-at-least-32-characters"
ENCRYPTION_KEY = "test-only-data-encryption-key-at-least-32-characters"


def make_user(*permissions: str) -> User:
    now = datetime.now(UTC)
    role = Role(
        id=uuid.uuid4(),
        code="manager",
        name="Gerente",
        permissions=[
            Permission(id=uuid.uuid4(), code=code, description=code) for code in permissions
        ],
    )
    return User(
        id=uuid.uuid4(),
        email="manager@example.com",
        name="Manager",
        password_hash="unused",
        active=True,
        must_change_password=False,
        role=role,
        role_id=role.id,
        created_at=now,
        updated_at=now,
    )


def make_service(database: Mock | None = None) -> MasterDataService:
    service = MasterDataService(
        database or Mock(),
        secret_hash_key=SECRET_KEY,
        data_encryption_key=ENCRYPTION_KEY,
    )
    service.categories = Mock()
    service.units = Mock()
    service.products = Mock()
    service.customers = Mock()
    return service


def assign_id(entity: object) -> object:
    entity.id = uuid.uuid4()  # type: ignore[attr-defined]
    return entity


def test_document_validation_masking_and_encryption() -> None:
    assert normalize_document("529.982.247-25") == "52998224725"
    assert document_type("529.982.247-25") == "cpf"
    assert document_type("04.252.011/0001-10") == "cnpj"
    assert mask_document("52998224725") == "***.***.***-25"
    cipher = DocumentCipher(ENCRYPTION_KEY)
    encrypted = cipher.encrypt("52998224725")
    assert encrypted != "52998224725"
    assert cipher.decrypt(encrypted) == "52998224725"
    with pytest.raises(ValueError):
        document_type("111.111.111-11")


def test_repository_paginates_results() -> None:
    database = Mock()
    database.scalar.return_value = 2
    database.scalars.return_value.unique.return_value.all.return_value = [Mock(), Mock()]
    repository = SqlAlchemyRepository(database, Category)
    result = repository.page(
        select(Category),
        page=1,
        size=10,
        sort_column=Category.name,
        descending=False,
    )
    assert result.total == 2
    assert result.pages == 1
    assert len(result.items) == 2


def test_category_and_unit_lifecycle_is_audited() -> None:
    database = Mock()
    service = make_service(database)
    user = make_user("catalog.manage")
    service.categories.add.side_effect = assign_id
    service.units.add.side_effect = assign_id

    category = service.create_category(
        CategoryInput(name="Bebidas", description="Catálogo", parent_id=None),
        user,
        "request-1",
    )
    unit = service.create_unit(UnitInput(code="un", name="Unidade"), user, "request-2")
    assert category.name == "Bebidas"
    assert unit.code == "UN"
    assert database.commit.call_count == 2

    service.categories.get.return_value = category
    service.units.get.return_value = unit
    assert service.get_category(category.id, user) is category
    assert service.get_unit(unit.id, user) is unit
    service.update_category(category.id, {"active": False}, user, "request-3")
    service.update_unit(unit.id, {"name": "Unidades"}, user, "request-4")
    assert not category.active
    assert unit.name == "Unidades"


def test_category_hierarchy_stays_simple() -> None:
    service = make_service()
    user = make_user("catalog.manage")
    parent = Category(
        id=uuid.uuid4(),
        name="Parent",
        description=None,
        parent_id=uuid.uuid4(),
        active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service.categories.get.return_value = parent
    with pytest.raises(ValueError):
        service.create_category(
            CategoryInput(name="Too deep", parent_id=parent.id),
            user,
            "request-5",
        )


def test_product_lifecycle_validates_references_and_builds_response() -> None:
    database = Mock()
    service = make_service(database)
    user = make_user("catalog.manage")
    category = Category(
        id=uuid.uuid4(),
        name="Bebidas",
        description=None,
        parent_id=None,
        active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    unit = UnitOfMeasure(
        id=uuid.uuid4(),
        code="UN",
        name="Unidade",
        active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service.categories.get.return_value = category
    service.units.get.return_value = unit

    def add_product(product: Product) -> Product:
        product.id = uuid.uuid4()
        product.category = category
        product.unit = unit
        return product

    service.products.add.side_effect = add_product
    payload = ProductInput(
        name="Água",
        description="Sem gás",
        sku="agua-1",
        barcode="7891234567890",
        brand="Flow",
        category_id=category.id,
        unit_id=unit.id,
        sale_price_minor=500,
        cost_price_minor=250,
        minimum_stock=Decimal("10"),
    )
    product = service.create_product(payload, user, "request-6")
    response = service.product_response(product)
    assert product.sku == "AGUA-1"
    assert response.category_name == "Bebidas"
    service.products.get.return_value = product
    service.update_product(product.id, {"active": False}, user, "request-7")
    assert not product.active
    assert service.get_product(product.id, user).unit_code == "UN"


def test_customer_document_is_protected_and_lifecycle_is_audited() -> None:
    database = Mock()
    service = make_service(database)
    user = make_user("customers.manage")
    service.customers.add.side_effect = assign_id
    customer = service.create_customer(
        CustomerInput(
            kind="individual",
            name="Maria",
            document="529.982.247-25",
            email="maria@example.com",
        ),
        user,
        "request-8",
    )
    assert customer.document is not None
    assert "52998224725" not in customer.document.encrypted_value
    response = service.customer_response(customer)
    assert response.masked_document == "***.***.***-25"
    service.customers.get.return_value = customer
    service.update_customer(customer.id, {"active": False}, user, "request-9")
    assert customer.document.active is False
    assert service.get_customer(customer.id, user).name == "Maria"

    with pytest.raises(ValueError, match="documento"):
        service.update_customer(
            customer.id,
            {"kind": "company", "legal_name": "Maria Ltda."},
            user,
            "request-10",
        )

    with pytest.raises(ValueError):
        service.create_customer(
            CustomerInput(kind="company", name="Company", document="529.982.247-25"),
            user,
            "request-11",
        )


def test_rbac_denies_catalog_to_cashier() -> None:
    service = make_service()
    user = make_user("customers.manage")
    with pytest.raises(PermissionDeniedError):
        service.list_units(
            user=user,
            page=1,
            size=20,
            search="",
            active=None,
            sort="code",
            descending=False,
        )


def test_search_pagination_paths_delegate_to_repositories() -> None:
    service = make_service()
    user = make_user("catalog.manage", "customers.manage")
    service.categories.page.return_value = RepositoryPage[Category](
        items=[], page=1, size=20, total=0, pages=1
    )
    service.units.page.return_value = RepositoryPage[UnitOfMeasure](
        items=[], page=1, size=20, total=0, pages=1
    )
    service.products.page.return_value = RepositoryPage[Product](
        items=[], page=1, size=20, total=0, pages=1
    )
    service.customers.page.return_value = RepositoryPage[Customer](
        items=[], page=1, size=20, total=0, pages=1
    )
    assert (
        service.list_categories(
            user=user,
            page=1,
            size=20,
            search="bebida",
            active=True,
            sort="created_at",
            descending=True,
        ).total
        == 0
    )
    assert (
        service.list_units(
            user=user,
            page=1,
            size=20,
            search="un",
            active=True,
            sort="name",
            descending=False,
        ).total
        == 0
    )
    assert (
        service.list_products(
            user=user,
            page=1,
            size=20,
            search="agua",
            active=True,
            category_id=uuid.uuid4(),
            unit_id=uuid.uuid4(),
            sort="sku",
            descending=False,
        ).total
        == 0
    )
    assert (
        service.list_customers(
            user=user,
            page=1,
            size=20,
            search="maria",
            active=True,
            sort="created_at",
            descending=True,
        ).total
        == 0
    )
