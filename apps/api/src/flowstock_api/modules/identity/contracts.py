from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SessionPolicy:
    idle_timeout: timedelta = timedelta(minutes=15)
    absolute_lifetime: timedelta = timedelta(hours=12)
    critical_operation_freshness: timedelta = timedelta(minutes=5)


class AuthenticationChallengeProvider(Protocol):
    """Extension boundary for a future MFA provider; no MVP provider exists."""

    def is_available(self) -> bool: ...
