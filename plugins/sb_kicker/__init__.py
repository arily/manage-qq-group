from enum import Enum

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
    SyncEntries = "S"
    MarkPendingRemoval = "M"
    Kick = "K"


cn_names = {
    Action.SyncEntries: '同步数据库',
    Action.MarkPendingRemoval: '通知并标记',
    Action.Kick: '移除',
}

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


action_prompt = "工作内容? " + ", ".join([f"{cn_names[Action(v)]} = {Action(v).value}" for v in Action])


@sb_kicker_force.got("action", prompt=action_prompt)
@sb_kicker.got("action", prompt=action_prompt)
async def select_operation(bot: OnebotV11Bot, state: T_State, action: Message = Arg()):
    maybe_action = action.extract_plain_text().strip()

    if maybe_action in actions:
        state["action"] = action = Action(maybe_action)
        await sb_kicker.send(action.name)
    else:
        await sb_kicker.finish("没有这个操作。")


pending_prompt = "选择用户，输入id，可以输入 1,2,3; 3-10; 4-"


@sb_kicker_force.got(
    "pending_range", prompt=pending_prompt
)
@sb_kicker.got("pending_range", prompt=pending_prompt)
async def _(bot: OnebotV11Bot, state: T_State, pending_range: Message = Arg()):
    members: list[JoinedGroupMemberInfo] = state['sorted']
    if datetime.now().timestamp() - state["trigger_time"] >= 60:
        await sb_kicker.finish("操作超时，取消上一次待输入的sb群kick操作")

    try:
        picked_ids = parse_ranges(pending_range.extract_plain_text(), 0, len(members) - 1)
        if min(*picked_ids) < 0:
            await sb_kicker.finish("取消本次操作, 长度不能为负")
        if max(*picked_ids) > len(members):
            await sb_kicker.finish("取消本次操作, 尝试踢出太多群友")

        picked = find_all(members, lambda m, i: i in picked_ids)

        match state["action"]:
            case Action.SyncEntries:
                for member in picked:
                    member['status'] = MemberStatus.PendingRemoval
                    await Accounts.update_or_create(**{k: v for k, v in member.items() if
                                                       v is not None and k in ['created_at', 'group_id', 'id', 'qq_id',
                                                                               'remark', 'sb_id', 'status',
                                                                               'updated_at', 'whitelisted']})
            case Action.MarkPendingRemoval:
                try:
                    await (
                        Accounts
                        .filter(
                            id__in=[member['id'] for member in picked if member['id'] is not None]
                        )
                        .update(
                            status=MemberStatus.PendingRemoval
                        )
                    )

                    not_in_db = [member for member in picked if member['id'] is None]
                    for member in not_in_db:
                        member['status'] = MemberStatus.PendingRemoval
                        await Accounts.create(**{k: v for k, v in member.items() if v is not None})

                    msg = "\n".join(
                        [f"{member['nickname']}(qq = {member['qq_id']}, sb = {member['sb_id']})" for member in picked]
                    )

                    await sb_kicker.send(
                        "通知以下用户（手动操作）：\n"
                        + msg
                    )
                except Exception as e:
                    logger.opt(exception=True).error(e)
                    await sb_kicker.finish("操作失败，请查看日志")
            case Action.Kick:
                try:
                    for member in picked:
                        await bot.set_group_kick(
                            group_id=SB_GROUP_ID,
                            user_id=member["qq_id"],
                            reject_add_request=False,
                        )
                        await sb_kicker.send(
                            f"已选择 {member['card'] if member['card'] is not None else member['nickname']}"
                            f" （{member['qq_id']})"
                        )

                except Exception as e:
                    logger.opt(exception=True).error(e)
                    await sb_kicker.finish("操作失败，请查看日志")
            case _:
                await sb_kicker.send('Unexpected Action')

        await sb_kicker.send("完了")
    except Exception as e:
        logger.opt(exception=True).error(e)
        await sb_kicker.finish("取消本次操作")


def parse_ranges(input_str: str, min_range: int, max_range: int):
    # Split the input string by commas
    parts = input_str.split(',')
    result = set()

    # Process each part
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            start = int(start) if start else min_range
            end = int(end) if end else max_range

            if start is not None and end is not None:
                result.update([*range(start, end)])
            elif start is not None:
                result.add(start)
        else:
            if part:
                result.add(int(part))

    # Convert the set to a sorted list
    return sorted(result)
