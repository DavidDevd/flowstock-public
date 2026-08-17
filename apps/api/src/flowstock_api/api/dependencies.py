from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from flowstock_api.modules.identity.models import User
from flowstock_api.modules.identity.service import (
    AuthenticatedSession,
    IdentityService,
    PermissionDeniedError,
    SessionInvalidError,
)
from flowstock_api.modules.master_data.service import MasterDataService


def database_session(request: Request) -> Iterator[Session]:
    yield from request.app.state.database.sessions()


def identity_service(
    request: Request, database: Annotated[Session, Depends(database_session)]
) -> IdentityService:
    settings = request.app.state.settings
    return IdentityService(
        database,
        idle_timeout=timedelta(minutes=settings.session_idle_minutes),
        absolute_timeout=timedelta(hours=settings.session_absolute_hours),
        secret_hash_key=settings.secret_hash_key,
    )


def authenticated_session(
    service: Annotated[IdentityService, Depends(identity_service)],
    flowstock_session: Annotated[str | None, Cookie()] = None,
) -> AuthenticatedSession:
    try:
        return service.authenticate(flowstock_session)
    except SessionInvalidError as exc:
        raise HTTPException(status_code=401, detail="Authentication required.") from exc


def csrf_authenticated_session(
    service: Annotated[IdentityService, Depends(identity_service)],
    flowstock_session: Annotated[str | None, Cookie()] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> AuthenticatedSession:
    try:
        return service.authenticate(flowstock_session, x_csrf_token)
    except SessionInvalidError as exc:
        raise HTTPException(status_code=401, detail="Authentication required.") from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail="Invalid CSRF token.") from exc


def current_user(
    session: Annotated[AuthenticatedSession, Depends(authenticated_session)],
) -> User:
    return session.user


def master_data_service(
    request: Request, database: Annotated[Session, Depends(database_session)]
) -> MasterDataService:
    settings = request.app.state.settings
    return MasterDataService(
        database,
        secret_hash_key=settings.secret_hash_key,
        data_encryption_key=settings.data_encryption_key,
    )
