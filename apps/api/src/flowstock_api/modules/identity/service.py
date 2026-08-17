from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from flowstock_api.modules.identity.models import (
    AuditEvent,
    AuthenticationSession,
    PasswordRecovery,
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


class AuthenticationFailedError(Exception):
    pass


class SessionInvalidError(Exception):
    pass


class PermissionDeniedError(Exception):
    pass


@dataclass(frozen=True)
class AuthenticatedSession:
    session: AuthenticationSession
    csrf_token: str | None = None

    @property
    def user(self) -> User:
        return self.session.user


class IdentityService:
    def __init__(
        self,
        database: Session,
        *,
        idle_timeout: timedelta,
        absolute_timeout: timedelta,
        secret_hash_key: str,
    ) -> None:
        self._database = database
        self._idle_timeout = idle_timeout
        self._absolute_timeout = absolute_timeout
        self._secret_hash_key = secret_hash_key

    def login(self, email: str, password: str, correlation_id: str) -> tuple[str, str, User]:
        user = self._database.scalar(select(User).where(User.email == email.strip().lower()))
        if user is None or not user.active or not verify_password(user.password_hash, password):
            self.audit("identity.login", "user", None, "denied", correlation_id)
            self._database.commit()
            raise AuthenticationFailedError

        now = datetime.now(UTC)
        token = new_secret()
        csrf = new_secret()
        authentication_session = AuthenticationSession(
            user_id=user.id,
            token_hash=hash_secret(token, self._secret_hash_key),
            csrf_hash=hash_secret(csrf, self._secret_hash_key),
            created_at=now,
            last_activity_at=now,
            expires_at=now + self._absolute_timeout,
            revoked_at=None,
        )
        self._database.add(authentication_session)
        self.audit("identity.login", "user", str(user.id), "success", correlation_id, user.id)
        self._database.commit()
        return token, csrf, user

    def authenticate(self, token: str | None, csrf: str | None = None) -> AuthenticatedSession:
        if not token:
            raise SessionInvalidError
        authentication_session = self._database.scalar(
            select(AuthenticationSession).where(
                AuthenticationSession.token_hash == hash_secret(token, self._secret_hash_key)
            )
        )
        now = datetime.now(UTC)
        if (
            authentication_session is None
            or authentication_session.revoked_at is not None
            or authentication_session.expires_at <= now
            or authentication_session.last_activity_at + self._idle_timeout <= now
            or not authentication_session.user.active
        ):
            raise SessionInvalidError
        if csrf is not None and not secrets_match(
            authentication_session.csrf_hash, csrf, self._secret_hash_key
        ):
            raise PermissionDeniedError
        if authentication_session.last_activity_at + timedelta(minutes=1) <= now:
            authentication_session.last_activity_at = now
            self._database.commit()
        return AuthenticatedSession(authentication_session)

    def logout(self, authentication_session: AuthenticationSession, correlation_id: str) -> None:
        authentication_session.revoked_at = datetime.now(UTC)
        self.audit(
            "identity.logout",
            "authentication_session",
            str(authentication_session.id),
            "success",
            correlation_id,
            authentication_session.user_id,
        )
        self._database.commit()

    def rotate_csrf(self, authentication_session: AuthenticationSession) -> str:
        csrf = new_secret()
        authentication_session.csrf_hash = hash_secret(csrf, self._secret_hash_key)
        self._database.commit()
        return csrf

    def change_password(
        self,
        authentication_session: AuthenticationSession,
        current_password: str,
        new_password: str,
        correlation_id: str,
    ) -> None:
        user = authentication_session.user
        if not verify_password(user.password_hash, current_password):
            raise AuthenticationFailedError
        now = datetime.now(UTC)
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        user.updated_at = now
        self._database.execute(
            update(AuthenticationSession)
            .where(
                AuthenticationSession.user_id == user.id,
                AuthenticationSession.id != authentication_session.id,
                AuthenticationSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        self.audit(
            "identity.password_change", "user", str(user.id), "success", correlation_id, user.id
        )
        self._database.commit()

    def create_user(
        self,
        *,
        email: str,
        name: str,
        role_code: str,
        temporary_password: str,
        actor: User,
        current_password: str,
        correlation_id: str,
    ) -> User:
        self.require_permission(actor, "users.manage")
        if not verify_password(actor.password_hash, current_password):
            raise AuthenticationFailedError
        role = self._database.scalar(select(Role).where(Role.code == role_code))
        if role is None:
            raise ValueError("Unknown role.")
        now = datetime.now(UTC)
        user = User(
            email=email.strip().lower(),
            name=name.strip(),
            password_hash=hash_password(temporary_password),
            active=True,
            must_change_password=True,
            role=role,
            created_at=now,
            updated_at=now,
        )
        self._database.add(user)
        self._database.flush()
        self.audit("users.create", "user", str(user.id), "success", correlation_id, actor.id)
        self._database.commit()
        return user

    def list_users(self, actor: User) -> list[User]:
        self.require_permission(actor, "users.manage")
        return list(self._database.scalars(select(User).order_by(User.name)).all())

    def update_user(
        self,
        *,
        user_id: uuid.UUID,
        name: str | None,
        role_code: str | None,
        active: bool | None,
        actor: User,
        current_password: str,
        correlation_id: str,
    ) -> User:
        self.require_permission(actor, "users.manage")
        if not verify_password(actor.password_hash, current_password):
            raise AuthenticationFailedError
        user = self._database.get(User, user_id)
        if user is None:
            raise ValueError("User not found.")
        if active is False and user.id == actor.id:
            raise ValueError("The current administrator cannot deactivate their own account.")
        now = datetime.now(UTC)
        privilege_changed = False
        if name is not None:
            user.name = name.strip()
        if role_code is not None and role_code != user.role.code:
            role = self._database.scalar(select(Role).where(Role.code == role_code))
            if role is None:
                raise ValueError("Unknown role.")
            user.role = role
            privilege_changed = True
        if active is not None and active != user.active:
            user.active = active
            privilege_changed = True
        user.updated_at = now
        if privilege_changed:
            self._revoke_user_sessions(user.id, now)
        self.audit("users.update", "user", str(user.id), "success", correlation_id, actor.id)
        self._database.commit()
        return user

    def initiate_recovery(
        self,
        *,
        user_id: uuid.UUID,
        actor: User,
        current_password: str,
        correlation_id: str,
    ) -> str:
        self.require_permission(actor, "users.manage")
        if not verify_password(actor.password_hash, current_password):
            raise AuthenticationFailedError
        user = self._database.get(User, user_id)
        if user is None or not user.active:
            raise ValueError("Active user not found.")
        now = datetime.now(UTC)
        credential = new_secret()
        self._database.add(
            PasswordRecovery(
                user_id=user.id,
                credential_hash=hash_secret(credential, self._secret_hash_key),
                created_by_user_id=actor.id,
                created_at=now,
                expires_at=now + timedelta(minutes=30),
                consumed_at=None,
            )
        )
        self.audit(
            "identity.recovery_initiate",
            "user",
            str(user.id),
            "success",
            correlation_id,
            actor.id,
        )
        self._database.commit()
        return credential

    def complete_recovery(
        self,
        *,
        email: str,
        credential: str,
        new_password: str,
        correlation_id: str,
    ) -> None:
        user = self._database.scalar(select(User).where(User.email == email.strip().lower()))
        recovery = self._database.scalar(
            select(PasswordRecovery).where(
                PasswordRecovery.credential_hash == hash_secret(credential, self._secret_hash_key)
            )
        )
        now = datetime.now(UTC)
        if (
            user is None
            or recovery is None
            or recovery.user_id != user.id
            or recovery.consumed_at is not None
            or recovery.expires_at <= now
            or not user.active
        ):
            self.audit("identity.recovery_complete", "user", None, "denied", correlation_id)
            self._database.commit()
            raise AuthenticationFailedError
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        user.updated_at = now
        recovery.consumed_at = now
        self._revoke_user_sessions(user.id, now)
        self.audit(
            "identity.recovery_complete",
            "user",
            str(user.id),
            "success",
            correlation_id,
            user.id,
        )
        self._database.commit()

    def set_user_active(self, user: User, active: bool, actor: User, correlation_id: str) -> None:
        self.require_permission(actor, "users.manage")
        user.active = active
        user.updated_at = datetime.now(UTC)
        if not active:
            self._database.execute(
                update(AuthenticationSession)
                .where(
                    AuthenticationSession.user_id == user.id,
                    AuthenticationSession.revoked_at.is_(None),
                )
                .values(revoked_at=datetime.now(UTC))
            )
        self.audit("users.active", "user", str(user.id), "success", correlation_id, actor.id)
        self._database.commit()

    def _revoke_user_sessions(self, user_id: uuid.UUID, revoked_at: datetime) -> None:
        self._database.execute(
            update(AuthenticationSession)
            .where(
                AuthenticationSession.user_id == user_id,
                AuthenticationSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )

    @staticmethod
    def require_permission(user: User, permission: str) -> None:
        if permission not in {item.code for item in user.role.permissions}:
            raise PermissionDeniedError

    def audit(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None,
        outcome: str,
        correlation_id: str,
        actor_user_id: uuid.UUID | None = None,
    ) -> None:
        self._database.add(
            AuditEvent(
                occurred_at=datetime.now(UTC),
                actor_user_id=actor_user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                correlation_id=correlation_id,
                details={},
            )
        )


def user_permissions(user: User) -> list[str]:
    return sorted(permission.code for permission in user.role.permissions)
