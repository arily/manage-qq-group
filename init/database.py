from typing import List

from tortoise import Tortoise


async def init():
    # Here we create a SQLite DB using file "db.sqlite3"
    #  also specify the app name of "models"
    #  which contain models from "app.models"
    await Tortoise.init(
        db_url="sqlite://data/db.sqlite3",
        modules={"models": ["models.db"]},
    )
    # Generate the schema
    await Tortoise.generate_schemas()


async def disconnect():
    await Tortoise.close_connections()
