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
from tortoise.expressions import Q

from models.model import *
from test_source import config
from test_source.samples.onebotV11.message_events import *


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotV11Adapter)

    nonebot.load_plugins("plugins")


class TestPluginSbKicker:

    @pytest.mark.asyncio
    async def test_sb_kicker(self, app: App):
        from plugins.sb_kicker import sb_kicker

        await self.init_db()

        async with app.test_matcher(sb_kicker) as ctx:
            bot = ctx.create_bot(base=OnebotV11Bot)

            event = private_message_event_normal("test")

            ctx.receive_event(bot, event)

            ctx.should_pass_rule()
            ctx.should_pass_permission()
            ctx.should_call_send(event, "稍等...", result=None)
            ctx.should_finished()

        try:
            await Tortoise.close_connections()
        except Exception:
            pass

    @staticmethod
    async def init_db():
        await Tortoise.init(
            db_url=config.database["url"],
            modules=config.database["modules"],
        )
        await Tortoise.generate_schemas()

        if not await Admins.exists(qq_id=config.admin_user["user_id"]):
            await Admins.create(
                qq_id=config.admin_user["user_id"]
            )



