from datetime import datetime

import pytest
import nonebot

# 导入适配器
from nonebot.adapters.onebot.v11 import (
    Adapter as OnebotV11Adapter,
    Bot as OnebotV11Bot,
)
from tortoise import Tortoise
from nonebug import App

from models.db import *
from test_source import config
from test_source.samples.onebotV11.message_events import *
from test_source.samples.onebotV11.user import *


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotV11Adapter)

    nonebot.load_plugins("plugins")


class TestPluginSbKicker:

    @pytest.mark.asyncio
    async def test_normal(self, app: App):
        from plugins.sb_kicker import sb_kicker

        await self.init_db()

        try:
            async with app.test_matcher(sb_kicker) as ctx:
                bot = ctx.create_bot(base=OnebotV11Bot)

                # admin test
                event = private_message_event_normal(
                    "sb服送人",
                    user_id=admin_sender.user_id,
                    nickname=admin_sender.nickname,
                )

                ctx.receive_event(bot, event)

                ctx.should_pass_rule()
                ctx.should_pass_permission()
                ctx.should_call_send(event, "稍等...", result=None)
                ctx.should_finished()
        finally:
            try:
                await Tortoise.close_connections()
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_not_admin_error(self, app: App):
        from plugins.sb_kicker import sb_kicker

        await self.init_db()

        try:
            async with app.test_matcher(sb_kicker) as ctx:
                bot = ctx.create_bot(base=OnebotV11Bot)

                # admin test
                event = private_message_event_normal(
                    "sb服送人",
                    user_id=normal_sender.user_id,
                    nickname=normal_sender.nickname,
                )

                ctx.receive_event(bot, event)

                ctx.should_not_pass_rule()
                ctx.should_finished()
        finally:
            try:
                await Tortoise.close_connections()
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_previous_instance_running_error(self, app: App):
        from plugins.sb_kicker import sb_kicker, PluginStatus

        await self.init_db()

        try:
            async with app.test_matcher(sb_kicker) as ctx:
                _, _ = await Caches.get_or_create(
                    key="sb_kicker_status",
                    defaults={
                        "value": PluginStatus.Running.value
                    }
                )

                bot = ctx.create_bot(base=OnebotV11Bot)

                # admin test
                event = private_message_event_normal(
                    "sb服送人",
                    user_id=admin_sender.user_id,
                    nickname=admin_sender.nickname,
                )

                ctx.receive_event(bot, event)

                ctx.should_pass_rule()
                ctx.should_pass_permission()
                ctx.should_rejected()
        finally:
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

        if not await Admins.exists(qq_id=admin_sender.user_id):
            await Admins.create(
                qq_id=admin_sender.user_id
            )



