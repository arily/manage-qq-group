from datetime import datetime

import pytest
import nonebot

# 导入适配器
from nonebot.adapters.onebot.v11 import (
    Adapter as OnebotV11Adapter,
    PrivateMessageEvent,
    Message,
    Bot as OnebotV11Bot,
)
from nonebot.adapters.onebot.v11.event import Sender
import os
from tortoise import Tortoise
from nonebug import App


async def db_init():
    # Here we create a SQLite DB using file "db.sqlite3"
    #  also specify the app name of "models"
    #  which contain models from "app.models"
    await Tortoise.init(
        db_url="sqlite://data/db.sqlite3",
        modules={"models": ["models.model"]},
    )
    # Generate the schema
    await Tortoise.generate_schemas()


async def db_disconnect():
    await Tortoise.close_connections()


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotV11Adapter)

    nonebot.load_plugins("plugins")


@pytest.mark.asyncio
async def test_sb_kicker(app: App):
    from plugins.sb_kicker import sb_kicker

    await Tortoise.init(
        db_url="sqlite://data/db.sqlite3",
        modules={"models": ["models.model"]},
    )
    await Tortoise.generate_schemas()

    async with app.test_matcher(sb_kicker) as ctx:
        bot = ctx.create_bot(base=OnebotV11Bot)

        event = gen_private_message_event()

        ctx.receive_event(bot, event)

        ctx.should_pass_rule()
        ctx.should_pass_permission()
        ctx.should_call_send(event, "稍等...", result=None)
        ctx.should_finished()

    await Tortoise.close_connections()


def gen_private_message_event():
    return PrivateMessageEvent(
        time=int(datetime.now().timestamp()),
        self_id=10000,
        message=Message("1123"),
        raw_message="1123",
        message_id=100000,
        user_id=1000000000,
        message_type="private",
        sender=Sender(
            user_id=1000000000,
            nickname="nonebot_test",
            age=18,
            area=None,
            card=None,
            level=None,
            role=None,
            sex="unknown",
            title=None,
        ),
        to_me=True,
        post_type="message",
        sub_type="friend",
        font=0,
    )
