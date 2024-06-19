from alicebot import Bot
from tortoise import Tortoise

bot = Bot()


async def init():
    # Here we create a SQLite DB using file "db.sqlite3"
    #  also specify the app name of "models"
    #  which contain models from "app.models"
    await Tortoise.init(
        db_url="sqlite://db.sqlite3", modules={"models": ["plugins.sb_kicker.db"]}
    )
    # Generate the schema
    await Tortoise.generate_schemas()


@bot.bot_run_hook
async def hook_func(_bot: Bot):
    await init()


if __name__ == "__main__":
    bot.run()
