import asyncio
from enum import Enum
from typing import TypedDict

from loguru import logger
from models.db import Admins
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import Bot as OnebotV11Bot
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11.message import Message
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Arg
from nonebot.message import run_postprocessor, run_preprocessor
from nonebot.rule import Rule
from nonebot.typing import T_State
from utils.qq_helper import is_admin

from .enum import PluginStatus
from .utils import *

SB_GROUP_ID = int(os.getenv("SB_GROUP_ID") or "-1")


class Action(str, Enum):
    Notify = "N"
    Kick = "K"


actions = set(item for item in Action)


# class State(TypedDict):
#     trigger_time: float
#     sorted: List[JoinedGroupMemberInfo]
#     action: Action


async def checker_common(event: MessageEvent) -> bool:
    return await Admins.exists(qq_id=event.sender.user_id)


async def checker_is_admin(bot: OnebotV11Bot):
    return await is_admin(bot, SB_GROUP_ID)


async def checker_is_plugin_idle() -> bool:
    cache, _ = await Caches.get_or_create(
        key="sb_kicker_status", defaults={"value": PluginStatus.Idle.value}
    )
    return cache.value == PluginStatus.Idle.value


sb_kicker = on_fullmatch(
    "sb服送人",
    rule=Rule(checker_common, checker_is_admin, checker_is_plugin_idle),
)

sb_kicker_force = on_fullmatch("sb服送人 --force")


@run_preprocessor
async def _(matcher: Matcher):
    if isinstance(matcher, sb_kicker):
        await Caches.filter(key="sb_kicker_status").update(
            value=PluginStatus.Running.value
        )


@run_postprocessor
async def _(matcher: Matcher):
    if isinstance(matcher, sb_kicker):
        await Caches.filter(key="sb_kicker_status").update(
            value=PluginStatus.Idle.value
        )


@sb_kicker_force.handle()
@sb_kicker.handle()
async def _(bot: OnebotV11Bot, state: T_State):
    await sb_kicker.send("稍等...")

    resp = await bot.get_group_member_list(group_id=SB_GROUP_ID)
    members = await get_accounts_with_db_data(resp)

    current_time = datetime.now().timestamp()
    state["trigger_time"] = current_time

    for item in members:
        item["weight"] = calculate_kick_weight(current_time, item)

    state["sorted"]: list[JoinedGroupMemberInfo] = members.copy()
    state["sorted"].sort(key=lambda x: x["weight"], reverse=True)

    state['sorted'] = state["sorted"][:30]

    msg = await gen_kick_query_msg(state["sorted"])

    await sb_kicker.send(msg)


@sb_kicker_force.got("action", prompt="工作内容？通知 = N, 移除 = K")
@sb_kicker.got("action", prompt="工作内容？通知 = N, 移除 = K")
async def select_operation(bot: OnebotV11Bot, state: T_State, action: Message = Arg()):
    maybe_action = action.extract_plain_text().strip()

    if maybe_action in actions:
        state["action"] = action = Action(maybe_action)
        await sb_kicker.send(action.name)
    else:
        await sb_kicker.finish("没有这个操作。")


@sb_kicker_force.got(
    "pending_count", prompt="选择几个(从上到下)？\n输入任意非正整数取消"
)
@sb_kicker.got("pending_count", prompt="选择几个(从上到下)？\n输入任意非正整数取消")
async def _(bot: OnebotV11Bot, state: T_State, pending_count: Message = Arg()):
    if datetime.now().timestamp() - state["trigger_time"] >= 60:
        await sb_kicker.finish("操作超时，取消上一次待输入的sb群kick操作")

    try:
        int(pending_count.extract_plain_text())
    except ValueError:
        await sb_kicker.finish("取消本次操作")

    pending_count = int(pending_count.extract_plain_text())
    if pending_count <= 0:
        await sb_kicker.finish("取消本次操作, 长度不能为负")
    if pending_count > len(state["sorted"]):
        await sb_kicker.finish("取消本次操作, 尝试踢出太多群友")

    try:
        for i in range(pending_count):
            member = state["sorted"][i]
            match state["action"]:
                case Action.Notify:
                    pass
                case Action.Kick:
                    await bot.set_group_kick(
                        group_id=SB_GROUP_ID,
                        user_id=member["qq_id"],
                        reject_add_request=False,
                    )
                    await sb_kicker.send(
                        f"已选择 {member['card'] if member['card'] is not None else member['nickname']}"
                        f" （{member['qq_id']}) [{i + 1} / {pending_count}]"
                    )
                case _:
                    await sb_kicker.send('Unexpected Action')
            await asyncio.sleep(1)
        await sb_kicker.send("完了")
    except Exception as e:
        logger.trace(e)
        await sb_kicker.finish("操作失败，请查看日志")
