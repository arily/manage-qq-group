import os
from typing import Generic, TypeVar

import sqlalchemy.dialects.mysql as mysql
from sqlalchemy.orm import Session
from db import Base

T = TypeVar("T", bound=Base)


def create_upsert_strategy():
    if os.environ.get("DB", "mysql") == "mysql":
        return _mysql_upsert_strategy
    else:
        raise NotImplementedError


def _mysql_upsert_strategy(
    session: Session,
    model: Generic[T],
    values: list[dict],
    on_duplicate_key_update: list[str],
) -> bool:
    upsert_statement = mysql.insert(model).values(values)

    update_dict = {
        field: upsert_statement.inserted[field] for field in on_duplicate_key_update
    }

    on_duplicate_key_statement = upsert_statement.on_duplicate_key_update(**update_dict)

    session.execute(on_duplicate_key_statement)
    session.commit()

    return True
