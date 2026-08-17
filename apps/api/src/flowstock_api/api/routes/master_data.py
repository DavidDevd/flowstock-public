from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError

from flowstock_api.api.dependencies import (
    csrf_authenticated_session,
    current_user,
    master_data_service,
)
from flowstock_api.modules.identity.models import User
from flowstock_api.modules.identity.service import AuthenticatedSession, PermissionDeniedError
from flowstock_api.modules.master_data.schemas import (
    CategoryInput,
    CategoryResponse,
    CategoryUpdate,
    CustomerInput,
    CustomerResponse,
    CustomerUpdate,
    Page,
    ProductInput,
    ProductResponse,
    ProductUpdate,
    UnitInput,
    UnitResponse,
    UnitUpdate,
)
from flowstock_api.modules.master_data.service import MasterDataService

router = APIRouter()
Direction = Literal["asc", "desc"]


@router.get("/categories", response_model=Page[CategoryResponse])
def list_categories(
    user: Annotated[User, Depends(current_user)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str, Query(max_length=100)] = "",
    active: bool | None = None,
    sort: str = "name",
    direction: Direction = "asc",
) -> Page[CategoryResponse]:
    return _call(
        service.list_categories,
        user=user,
        page=page,
        size=size,
        search=search,
        active=active,
        sort=sort,
        descending=direction == "desc",
    )


@router.get("/categories/{entity_id}", response_model=CategoryResponse)
def get_category(
    entity_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> CategoryResponse:
    return cast(CategoryResponse, _call(service.get_category, entity_id, user))


@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(
    payload: CategoryInput,
    request: Request,
    auth: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> CategoryResponse:
    return cast(CategoryResponse, _mutate(service.create_category, payload, auth.user, request))


@router.patch("/categories/{entity_id}", response_model=CategoryResponse)
def update_category(
    entity_id: uuid.UUID,
    payload: CategoryUpdate,
    request: Request,
    auth: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> CategoryResponse:
    return cast(
        CategoryResponse,
        _mutate(
            service.update_category,
            entity_id,
            payload.model_dump(exclude_unset=True),
            auth.user,
            request,
        ),
    )


@router.get("/units", response_model=Page[UnitResponse])
def list_units(
    user: Annotated[User, Depends(current_user)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str, Query(max_length=100)] = "",
    active: bool | None = None,
    sort: str = "code",
    direction: Direction = "asc",
) -> Page[UnitResponse]:
    return _call(
        service.list_units,
        user=user,
        page=page,
        size=size,
        search=search,
        active=active,
        sort=sort,
        descending=direction == "desc",
    )


@router.get("/units/{entity_id}", response_model=UnitResponse)
def get_unit(
    entity_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> UnitResponse:
    return cast(UnitResponse, _call(service.get_unit, entity_id, user))


@router.post("/units", response_model=UnitResponse, status_code=201)
def create_unit(
    payload: UnitInput,
    request: Request,
    auth: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> UnitResponse:
    return cast(UnitResponse, _mutate(service.create_unit, payload, auth.user, request))


@router.patch("/units/{entity_id}", response_model=UnitResponse)
def update_unit(
    entity_id: uuid.UUID,
    payload: UnitUpdate,
    request: Request,
    auth: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> UnitResponse:
    return cast(
        UnitResponse,
        _mutate(
            service.update_unit,
            entity_id,
            payload.model_dump(exclude_unset=True),
            auth.user,
            request,
        ),
    )


@router.get("/products", response_model=Page[ProductResponse])
def list_products(
    user: Annotated[User, Depends(current_user)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str, Query(max_length=100)] = "",
    active: bool | None = None,
    category_id: uuid.UUID | None = None,
    unit_id: uuid.UUID | None = None,
    sort: str = "name",
    direction: Direction = "asc",
) -> Page[ProductResponse]:
    return _call(
        service.list_products,
        user=user,
        page=page,
        size=size,
        search=search,
        active=active,
        category_id=category_id,
        unit_id=unit_id,
        sort=sort,
        descending=direction == "desc",
    )


@router.get("/products/{entity_id}", response_model=ProductResponse)
def get_product(
    entity_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> ProductResponse:
    return _call(service.get_product, entity_id, user)


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    payload: ProductInput,
    request: Request,
    auth: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> ProductResponse:
    product = _mutate(service.create_product, payload, auth.user, request)
    return service.product_response(product)


@router.patch("/products/{entity_id}", response_model=ProductResponse)
def update_product(
    entity_id: uuid.UUID,
    payload: ProductUpdate,
    request: Request,
    auth: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> ProductResponse:
    product = _mutate(
        service.update_product,
        entity_id,
        payload.model_dump(exclude_unset=True),
        auth.user,
        request,
    )
    return service.product_response(product)


@router.get("/customers", response_model=Page[CustomerResponse])
def list_customers(
    user: Annotated[User, Depends(current_user)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str, Query(max_length=100)] = "",
    active: bool | None = None,
    sort: str = "name",
    direction: Direction = "asc",
) -> Page[CustomerResponse]:
    return _call(
        service.list_customers,
        user=user,
        page=page,
        size=size,
        search=search,
        active=active,
        sort=sort,
        descending=direction == "desc",
    )


@router.get("/customers/{entity_id}", response_model=CustomerResponse)
def get_customer(
    entity_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> CustomerResponse:
    return _call(service.get_customer, entity_id, user)


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(
    payload: CustomerInput,
    request: Request,
    auth: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> CustomerResponse:
    customer = _mutate(service.create_customer, payload, auth.user, request)
    return service.customer_response(customer)


@router.patch("/customers/{entity_id}", response_model=CustomerResponse)
def update_customer(
    entity_id: uuid.UUID,
    payload: CustomerUpdate,
    request: Request,
    auth: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[MasterDataService, Depends(master_data_service)],
) -> CustomerResponse:
    customer = _mutate(
        service.update_customer,
        entity_id,
        payload.model_dump(exclude_unset=True),
        auth.user,
        request,
    )
    return service.customer_response(customer)


def _call[ResultT](function: Callable[..., ResultT], *args: object, **kwargs: object) -> ResultT:
    try:
        return function(*args, **kwargs)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail="Permission denied.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _mutate[ResultT](function: Callable[..., ResultT], *args: object) -> ResultT:
    request = args[-1]
    forwarded = (*args[:-1], str(request.state.correlation_id))  # type: ignore[attr-defined]
    try:
        return function(*forwarded)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail="Permission denied.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Cadastro duplicado ou em uso.") from exc
