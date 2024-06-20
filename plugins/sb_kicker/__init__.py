import asyncio

from loguru import logger
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, MessageEvent, Bot as OnebotV11Bot
from nonebot.rule import Rule
from models.model import Admins, Caches
from nonebot import on_message
from .enum import PluginStatus
from tortoise import filters


async def checker_common(event: PrivateMessageEvent) -> bool:
    return (
        await Admins.exists(qq_id=event.sender.user_id)
    )


async def checker_plugin_status() -> bool:
    cache, _ = await Caches.get_or_create(
        key="sb_kicker_status",
        defaults={
            "value": PluginStatus.Idle.value
        }
    )
    if cache.value == PluginStatus.Idle.value:
        return True
    return False


sb_kicker = on_message(
    rule=Rule(checker_common, checker_plugin_status)
)


@sb_kicker.handle()
async def handle_function():
    await Caches.filter(key="sb_kicker_status").update(value=PluginStatus.Running.value)

    await sb_kicker.send("稍等...")

    # TODO:contents

    await Caches.filter(key="sb_kicker_status").update(value=PluginStatus.Idle.value)
