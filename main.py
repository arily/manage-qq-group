from tortoise import Tortoise, run_async

from alicebot import Bot
import plugins.sb_kicker.db as db

bot = Bot()


async def init():
    # Here we create a SQLite DB using file "db.sqlite3"
    #  also specify the app name of "models"
    #  which contain models from "app.models"
    await Tortoise.init(
        modules={'model': 'plugins.sb_kicker.db'},
        # config={
        #     'apps': {
        #         'models': {
        #             'models': db,
        #             'default_connection': 'default'
        #         },
        #     },
        #     'connections': {
        #         'default': "sqlite://db.sqlite3"
        #     }
        # }
    )
    # Generate the schema
    # await Tortoise.generate_schemas()


# @bot.bot_run_hook
# async def hook_func(_bot: Bot):
#     await init()


if __name__ == "__main__":
    run_async(init())
    bot.run()
