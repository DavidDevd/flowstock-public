from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    role: str
    permissions: list[str]
    must_change_password: bool
    active: bool


class SessionResponse(BaseModel):
    user: UserResponse
    csrf_token: str


class CreateUserRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    name: str = Field(min_length=2, max_length=120)
    role: str
    temporary_password: str = Field(min_length=12, max_length=128)
    current_password: str = Field(min_length=1, max_length=128)


class UpdateUserRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    role: str | None = None
    active: bool | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class InitiateRecoveryRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)


class RecoveryCredentialResponse(BaseModel):
    credential: str
    expires_in_seconds: int = 1800


class CompleteRecoveryRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    credential: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)
