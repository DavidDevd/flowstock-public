from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from flowstock_api.modules.identity.models import Base


@dataclass(frozen=True)
class RepositoryPage[ModelT]:
    items: list[ModelT]
    page: int
    size: int
    total: int
    pages: int


class SqlAlchemyRepository[ModelT: Base]:
    def __init__(self, database: Session, model: type[ModelT]) -> None:
        self.database = database
        self.model = model

    def get(self, entity_id: object) -> ModelT | None:
        return self.database.get(self.model, entity_id)

    def add(self, entity: ModelT) -> ModelT:
        self.database.add(entity)
        self.database.flush()
        return entity

    def page(
        self,
        statement: Select[tuple[ModelT]],
        *,
        page: int,
        size: int,
        sort_column: object,
        descending: bool,
    ) -> RepositoryPage[ModelT]:
        count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
        total = int(self.database.scalar(count_statement) or 0)
        order = sort_column.desc() if descending else sort_column.asc()  # type: ignore[attr-defined]
        items = list(
            self.database.scalars(statement.order_by(order).offset((page - 1) * size).limit(size))
            .unique()
            .all()
        )
        return RepositoryPage[ModelT](
            items=items,
            page=page,
            size=size,
            total=total,
            pages=max(1, math.ceil(total / size)),
        )
