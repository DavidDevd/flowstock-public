from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from flowstock_api.modules.identity.models import (
    AuthenticationSession,
    PasswordRecovery,
    Permission,
    Role,
    User,
)
from flowstock_api.modules.identity.security import (
    hash_password,
    hash_secret,
    new_secret,
    secrets_match,
    verify_password,
)
from flowstock_api.modules.identity.service import (
    AuthenticationFailedError,
    IdentityService,
    PermissionDeniedError,
    SessionInvalidError,
    user_permissions,
)

SECRET_HASH_KEY = "test-only-secret-hash-key-at-least-32-characters"


def make_user(password: str = "correct horse battery") -> User:
    now = datetime.now(UTC)
    role = Role(
        id=uuid.uuid4(),
        code="administrator",
        name="Administrador",
        permissions=[Permission(id=uuid.uuid4(), code="users.manage", description="Manage users")],
    )
    return User(
        id=uuid.uuid4(),
        email="admin@flowstock.local",
        name="Admin",
        password_hash=hash_password(password),
        active=True,
        must_change_password=False,
        role=role,
        role_id=role.id,
        created_at=now,
        updated_at=now,
    )


def make_service(database: Mock) -> IdentityService:
    return IdentityService(
        database,
        idle_timeout=timedelta(minutes=15),
        absolute_timeout=timedelta(hours=12),
        secret_hash_key=SECRET_HASH_KEY,
    )


def test_password_and_secret_security() -> None:
    password_hash = hash_password("a long secure password")
    assert verify_password(password_hash, "a long secure password")
    assert not verify_password(password_hash, "wrong password")
    assert not verify_password("invalid", "wrong password")
    with pytest.raises(ValueError):
        hash_password("short")
    secret = new_secret()
    assert secrets_match(hash_secret(secret, SECRET_HASH_KEY), secret, SECRET_HASH_KEY)
    assert not secrets_match(hash_secret(secret, SECRET_HASH_KEY), "other", SECRET_HASH_KEY)


def test_login_creates_session_and_audit() -> None:
    database = Mock()
    user = make_user()
    database.scalar.return_value = user

    token, csrf, authenticated_user = make_service(database).login(
        user.email, "correct horse battery", "request-1"
    )

    assert authenticated_user is user
    assert token and csrf
    assert database.add.call_count == 2
    database.commit.assert_called_once()


def test_login_rejects_invalid_or_inactive_user() -> None:
    database = Mock()
    database.scalar.return_value = None
    with pytest.raises(AuthenticationFailedError):
        make_service(database).login("missing@example.com", "invalid", "request-2")
    database.commit.assert_called_once()


def test_authenticate_enforces_session_expiry_csrf_and_activity() -> None:
    database = Mock()
    user = make_user()
    now = datetime.now(UTC)
    session = AuthenticationSession(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_secret("token", SECRET_HASH_KEY),
        csrf_hash=hash_secret("csrf", SECRET_HASH_KEY),
        created_at=now - timedelta(minutes=2),
        last_activity_at=now - timedelta(minutes=2),
        expires_at=now + timedelta(hours=1),
        revoked_at=None,
        user=user,
    )
    database.scalar.return_value = session
    service = make_service(database)

    assert service.authenticate("token", "csrf").user is user
    database.commit.assert_called_once()
    with pytest.raises(PermissionDeniedError):
        service.authenticate("token", "wrong")

    session.expires_at = now - timedelta(seconds=1)
    with pytest.raises(SessionInvalidError):
        service.authenticate("token")
    with pytest.raises(SessionInvalidError):
        service.authenticate(None)


def test_permissions_logout_and_user_activation() -> None:
    database = Mock()
    actor = make_user()
    target = make_user()
    now = datetime.now(UTC)
    session = AuthenticationSession(
        id=uuid.uuid4(),
        user_id=actor.id,
        token_hash=hash_secret("token", SECRET_HASH_KEY),
        csrf_hash=hash_secret("csrf", SECRET_HASH_KEY),
        created_at=now,
        last_activity_at=now,
        expires_at=now + timedelta(hours=1),
        revoked_at=None,
        user=actor,
    )
    service = make_service(database)

    service.logout(session, "request-3")
    assert session.revoked_at is not None
    assert service.rotate_csrf(session)
    service.change_password(session, "correct horse battery", "a replacement password", "request-3")
    assert not actor.must_change_password
    with pytest.raises(AuthenticationFailedError):
        service.change_password(session, "wrong", "another replacement", "request-3")
    assert user_permissions(actor) == ["users.manage"]
    service.set_user_active(target, False, actor, "request-4")
    assert not target.active
    assert database.execute.called

    actor.role.permissions = []
    with pytest.raises(PermissionDeniedError):
        service.set_user_active(target, True, actor, "request-5")


def test_administrator_creates_and_lists_users() -> None:
    database = Mock()
    actor = make_user()
    manager_role = Role(
        id=uuid.uuid4(),
        code="manager",
        name="Gerente",
        permissions=[],
    )
    database.scalar.return_value = manager_role
    database.scalars.return_value.all.return_value = [actor]
    service = make_service(database)

    created = service.create_user(
        email=" Manager@Example.com ",
        name=" Manager ",
        role_code="manager",
        temporary_password="temporary password",
        actor=actor,
        current_password="correct horse battery",
        correlation_id="request-6",
    )

    assert created.email == "manager@example.com"
    assert created.must_change_password
    assert service.list_users(actor) == [actor]


def test_administrator_updates_user_and_issues_single_use_recovery() -> None:
    database = Mock()
    actor = make_user()
    target = make_user("target secure password")
    database.get.return_value = target
    service = make_service(database)

    updated = service.update_user(
        user_id=target.id,
        name="Updated User",
        role_code=None,
        active=False,
        actor=actor,
        current_password="correct horse battery",
        correlation_id="request-7",
    )
    assert updated.name == "Updated User"
    assert not updated.active

    target.active = True
    credential = service.initiate_recovery(
        user_id=target.id,
        actor=actor,
        current_password="correct horse battery",
        correlation_id="request-8",
    )
    recovery = PasswordRecovery(
        id=uuid.uuid4(),
        user_id=target.id,
        credential_hash=hash_secret(credential, SECRET_HASH_KEY),
        created_by_user_id=actor.id,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
        consumed_at=None,
        user=target,
    )
    database.scalar.side_effect = [target, recovery]
    service.complete_recovery(
        email=target.email,
        credential=credential,
        new_password="recovered secure password",
        correlation_id="request-9",
    )
    assert recovery.consumed_at is not None
    assert verify_password(target.password_hash, "recovered secure password")

    database.scalar.side_effect = [target, recovery]
    with pytest.raises(AuthenticationFailedError):
        service.complete_recovery(
            email=target.email,
            credential=credential,
            new_password="another secure password",
            correlation_id="request-10",
        )


def test_user_administration_rejects_unsafe_changes_and_supports_role_change() -> None:
    database = Mock()
    actor = make_user()
    target = make_user()
    manager_role = Role(id=uuid.uuid4(), code="manager", name="Gerente", permissions=[])
    database.get.return_value = target
    database.scalar.return_value = manager_role
    service = make_service(database)

    changed = service.update_user(
        user_id=target.id,
        name=None,
        role_code="manager",
        active=None,
        actor=actor,
        current_password="correct horse battery",
        correlation_id="request-11",
    )
    assert changed.role.code == "manager"

    database.get.return_value = actor
    with pytest.raises(ValueError):
        service.update_user(
            user_id=actor.id,
            name=None,
            role_code=None,
            active=False,
            actor=actor,
            current_password="correct horse battery",
            correlation_id="request-12",
        )
    with pytest.raises(AuthenticationFailedError):
        service.initiate_recovery(
            user_id=target.id,
            actor=actor,
            current_password="wrong",
            correlation_id="request-13",
        )
