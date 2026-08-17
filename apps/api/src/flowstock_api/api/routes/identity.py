from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from flowstock_api.api.dependencies import (
    authenticated_session,
    csrf_authenticated_session,
    identity_service,
)
from flowstock_api.modules.identity.models import User
from flowstock_api.modules.identity.schemas import (
    ChangePasswordRequest,
    CompleteRecoveryRequest,
    LoginRequest,
    SessionResponse,
    UserResponse,
)
from flowstock_api.modules.identity.service import (
    AuthenticatedSession,
    AuthenticationFailedError,
    IdentityService,
    user_permissions,
)

router = APIRouter()


def _user_response(session_user: User) -> UserResponse:
    user = session_user
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.code,
        permissions=user_permissions(user),
        must_change_password=user.must_change_password,
        active=user.active,
    )


@router.post("/login", response_model=SessionResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: Annotated[IdentityService, Depends(identity_service)],
) -> SessionResponse:
    try:
        token, csrf, user = service.login(
            payload.email,
            payload.password,
            str(request.state.correlation_id),
        )
    except AuthenticationFailedError as exc:
        raise HTTPException(status_code=401, detail="Invalid credentials.") from exc
    response.set_cookie(
        "flowstock_session",
        token,
        httponly=True,
        secure=request.app.state.settings.session_cookie_secure,
        samesite="strict",
        max_age=request.app.state.settings.session_absolute_hours * 3600,
        path="/",
    )
    return SessionResponse(user=_user_response(user), csrf_token=csrf)


@router.get("/session", response_model=SessionResponse)
def session(
    authentication: Annotated[AuthenticatedSession, Depends(authenticated_session)],
    service: Annotated[IdentityService, Depends(identity_service)],
) -> SessionResponse:
    return SessionResponse(
        user=_user_response(authentication.user),
        csrf_token=service.rotate_csrf(authentication.session),
    )


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    authentication: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[IdentityService, Depends(identity_service)],
) -> None:
    service.logout(authentication.session, str(request.state.correlation_id))
    response.delete_cookie("flowstock_session", path="/")


@router.post("/password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    authentication: Annotated[AuthenticatedSession, Depends(csrf_authenticated_session)],
    service: Annotated[IdentityService, Depends(identity_service)],
) -> None:
    try:
        service.change_password(
            authentication.session,
            payload.current_password,
            payload.new_password,
            str(request.state.correlation_id),
        )
    except AuthenticationFailedError as exc:
        raise HTTPException(status_code=401, detail="Current password is invalid.") from exc


@router.post("/recovery/complete", status_code=204)
def complete_recovery(
    payload: CompleteRecoveryRequest,
    request: Request,
    service: Annotated[IdentityService, Depends(identity_service)],
) -> None:
    try:
        service.complete_recovery(
            email=payload.email,
            credential=payload.credential,
            new_password=payload.new_password,
            correlation_id=str(request.state.correlation_id),
        )
    except AuthenticationFailedError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid or expired recovery credential."
        ) from exc
