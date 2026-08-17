from __future__ import annotations

import argparse
import getpass
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from flowstock_api.config import get_settings
from flowstock_api.infrastructure.database import Database
from flowstock_api.modules.identity.models import Role, User
from flowstock_api.modules.identity.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first FlowStock administrator.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    arguments = parser.parse_args()
    password = getpass.getpass("Temporary password (12-128 characters): ")

    database = Database(get_settings().database_url)
    with database.session_factory.begin() as session:
        if session.scalar(select(User.id).limit(1)) is not None:
            raise SystemExit("Bootstrap refused: at least one user already exists.")
        role = session.scalar(select(Role).where(Role.code == "administrator"))
        if role is None:
            raise SystemExit("Run Alembic migrations before administrator bootstrap.")
        now = datetime.now(UTC)
        session.add(
            User(
                id=uuid.uuid4(),
                email=arguments.email.strip().lower(),
                name=arguments.name.strip(),
                password_hash=hash_password(password),
                active=True,
                must_change_password=True,
                role=role,
                created_at=now,
                updated_at=now,
            )
        )
    database.close()
    print("Administrator created. A password change is required on first use.")


if __name__ == "__main__":
    main()
