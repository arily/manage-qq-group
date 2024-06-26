from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot as OnebotV11Bot

from models.db import Caches
from utils.qq_helper import is_admin


async def checker_is_sender_bot_admin(bot: OnebotV11Bot, event: GroupMessageEvent) -> bool:
    return str(event.sender.user_id) in bot.config.superusers


async def checker_is_bot_group_admin(bot: OnebotV11Bot, event: GroupMessageEvent):
    return await is_admin(bot, event.group_id)


async def checker_is_plugin_idle() -> bool:
    cache, _ = await Caches.get_or_create(
        key="is_sb_kicker_kicking",
        defaults={
            "value": 0
        }
    )
    return cache.value == 0
