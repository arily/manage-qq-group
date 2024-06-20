import asyncio
from datetime import datetime, timezone

from loguru import logger
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, MessageEvent, Bot as OnebotV11Bot, Message
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Arg
from nonebot.rule import Rule
from nonebot.message import run_postprocessor, run_preprocessor
from nonebot.typing import T_State

from models.db import Admins, Caches
from nonebot import on_message, on_fullmatch
from .enum import PluginStatus
from tortoise import filters

from .utils import *

SB_GROUP_ID = 792778662


async def checker_common(event: PrivateMessageEvent) -> bool:
    return (
        await Admins.exists(qq_id=event.sender.user_id)
    )


sb_kicker = on_fullmatch(
    "sb服送人",
    rule=Rule(checker_common)
)


@run_postprocessor
async def _(matcher: Matcher):
    if isinstance(matcher, sb_kicker):
        await Caches.filter(key="sb_kicker_status").update(value=PluginStatus.Idle.value)


@sb_kicker.handle()
async def _(bot: OnebotV11Bot, state: T_State):
    if await check_plugin_running():
        await sb_kicker.reject("上次插件还在运行中，终止本次操作...")
        return

    await Caches.filter(key="sb_kicker_status").update(value=PluginStatus.Running.value)

    await sb_kicker.send("稍等...")

    resp = await bot.get_group_member_list(group_id=SB_GROUP_ID)

    current_time = datetime.now().timestamp()

    state["trigger_time"] = current_time
    state["member_weights"] = sorted(
        [(m["user_id"], calculate_kick_weight(current_time, m)) for m in resp],
        key=lambda x: x[1],
        reverse=True
    )

    state["members_dict"] = {
        member["user_id"]: member for member in resp
    }  # 将成员列表转换为以 user_id 为键的字典 提性能，也方便查询

    g = await gen_kick_query_msg(state["members_dict"], state["member_weights"])

    await sb_kicker.send(g)


@sb_kicker.got("kick_count", prompt="送走几个(从上到下)？\n输入任意非正整数取消")
async def _(bot: OnebotV11Bot, state: T_State, kick_count: Message = Arg()):
    if datetime.now().timestamp() - state["trigger_time"] < 60:
        sb_kicker.finish("操作超时，取消上一次待输入的sb群kick操作")

    try:
        int(kick_count.extract_plain_text())
    except ValueError:
        sb_kicker.finish("取消本次操作")

    kick_count = int(kick_count.extract_plain_text())
    if kick_count < 0:
        sb_kicker.finish("取消本次操作")
    if kick_count > len(state["member_weights"]):
        sb_kicker.finish("取消本次操作")

    try:
        for i in range(kick_count):
            member = state["members_dict"][state["member_weights"][i][0]]
            # await bot.set_group_kick(
            #     group_id=SB_GROUP_ID,
            #     user_id=member["user_id"],
            #     reject_add_request=False
            # )
            await sb_kicker.send(
                f"已送走 {member['card'] if member['card'] is not None else member['nickname']}"
                f" （{member['user_id']}) [{i + 1} / {kick_count}]"
            )

            await asyncio.sleep(3)
        await sb_kicker.finish("送完了")
    except Exception as e:
        logger.error(e)
        sb_kicker.finish("操作失败，请查看日志")

    member_weights = state["member_weights"]
    members_dict = state["members_dict"]
