from typing import TypedDict


class _AdminUser(TypedDict):
    user_id: int
    nickname: str


class _Database(TypedDict):
    url: str
    modules: dict


admin_user: _AdminUser = {
    "user_id": 1000000000,
    "nickname": "Test Admin User"
}

database: _Database = {
    "url": "sqlite://test_source/db/db.sqlite3",
    "modules": {"models": ["models.model"]},
}
