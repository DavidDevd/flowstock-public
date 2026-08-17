from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError

from flowstock_api.api.dependencies import (
    csrf_authenticated_session,
    current_user,
    identity_service,
)
from flowstock_api.modules.identity.models import User
from flowstock_api.modules.identity.schemas import (
    CreateUserRequest,
    InitiateRecoveryRequest,
    RecoveryCredentialResponse,
    UpdateUserRequest,
    UserResponse,
)
from flowstock_api.modules.identity.service import (
    AuthenticatedSession,
    AuthenticationFailedError,
    IdentityService,
    PermissionDeniedError,
    user_permissions,
)

router = APIRouter()


def _response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.code,
        permissions=user_permissions(user),
        must_change_password=user.must_change_password,
        active=user.active,
    )


@router.get("", response_model=list[UserResponse])
def list_users(
    actor: Annotated[User, Depends(current_user)],
    service: Annotated[IdentityService, Depends(identity_service)],
) -> list[UserResponse]:
    try:
        return [_response(user) for user in service.list_users(actor)]
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail="Permission denied.") from exc


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    payload: CreateUserRequest,
    request: Request,
    authentication: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[IdentityService, Depends(identity_service)],
) -> UserResponse:
    actor = authentication.user
    try:
        user = service.create_user(
            email=payload.email,
            name=payload.name,
            role_code=payload.role,
            temporary_password=payload.temporary_password,
            actor=actor,
            current_password=payload.current_password,
            correlation_id=str(request.state.correlation_id),
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail="Permission denied.") from exc
    except AuthenticationFailedError as exc:
        raise HTTPException(status_code=401, detail="Reauthentication failed.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Email already registered.") from exc
    return _response(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    request: Request,
    authentication: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[IdentityService, Depends(identity_service)],
) -> UserResponse:
    try:
        user = service.update_user(
            user_id=uuid.UUID(user_id),
            name=payload.name,
            role_code=payload.role,
            active=payload.active,
            actor=authentication.user,
            current_password=payload.current_password,
            correlation_id=str(request.state.correlation_id),
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail="Permission denied.") from exc
    except AuthenticationFailedError as exc:
        raise HTTPException(status_code=401, detail="Reauthentication failed.") from exc
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _response(user)


@router.post("/{user_id}/recovery", response_model=RecoveryCredentialResponse)
def initiate_recovery(
    user_id: str,
    payload: InitiateRecoveryRequest,
    request: Request,
    authentication: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[IdentityService, Depends(identity_service)],
) -> RecoveryCredentialResponse:
    try:
        credential = service.initiate_recovery(
            user_id=uuid.UUID(user_id),
            actor=authentication.user,
            current_password=payload.current_password,
            correlation_id=str(request.state.correlation_id),
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail="Permission denied.") from exc
    except AuthenticationFailedError as exc:
        raise HTTPException(status_code=401, detail="Reauthentication failed.") from exc
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RecoveryCredentialResponse(credential=credential)
