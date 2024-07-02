import asyncio

from loguru import logger

from models import sync_in_group
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import Bot as OnebotV11Bot
from nonebot.adapters.onebot.v11.message import Message
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Arg
from nonebot.message import run_postprocessor, run_preprocessor
from nonebot.rule import Rule
from nonebot.typing import T_State

from utils import parse_ranges, J_G_M_to_saveable
from utils.qq_helper import fmt_user, is_sender_admin, is_bot_group_admin
from .enum import PluginStatus, Action, cn_names, actions
from .utils import *

dotenv.load_dotenv()
SB_GROUP_ID = int(os.getenv("SB_GROUP_ID") or "-1")


async def is_plugin_idle() -> bool:
    cache, _ = await Caches.get_or_create(
        key="sb_kicker_status", defaults={"value": PluginStatus.Idle.value}
    )
    return cache.value == PluginStatus.Idle.value


sb_kicker = on_fullmatch(
    "sb rank",
    rule=Rule(is_sender_admin, is_bot_group_admin, is_plugin_idle),
)

sb_kicker_force = on_fullmatch("sbrank --force")


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
    await sync_in_group(members)

    current_time = datetime.now().timestamp()
    state["trigger_time"] = current_time

    for item in members:
        item["weight"] = calculate_kick_weight(current_time, item)

    state["sorted"]: list[JoinedGroupMemberInfo] = members.copy()
    state["sorted"].sort(key=lambda x: x["weight"], reverse=True)

    state["sorted"] = state["sorted"][:30]

    msg = await gen_kick_query_img(title="潜水榜", members=state["sorted"])

    await sb_kicker.send(msg)


pending_prompt = "选择用户，输入id，可以输入 1,2,3; 3-10; 4-"


@sb_kicker_force.got("pending_range", prompt=pending_prompt)
@sb_kicker.got("pending_range", prompt=pending_prompt)
async def prompt_range(
    bot: OnebotV11Bot, state: T_State, pending_range: Message = Arg()
):
    members: list[JoinedGroupMemberInfo] = state["sorted"]
    if datetime.now().timestamp() - state["trigger_time"] >= 60:
        await sb_kicker.finish("操作超时，取消上一次待输入的sb群kick操作")

    try:
        picked_ids = parse_ranges(
            pending_range.extract_plain_text(), 0, len(members) - 1
        )
        if min(*picked_ids, 0) < 0:
            await sb_kicker.finish("取消本次操作, 长度不能为负")
        if max(*picked_ids, len(members)) > len(members):
            await sb_kicker.finish("取消本次操作, 尝试踢出太多群友")

        picked = filter_in(members, lambda m, i: i in picked_ids)
        state["marked"] = picked
    except Exception as e:
        logger.opt(exception=True).error(e)
        await sb_kicker.finish("取消本次操作")


action_prompt = "工作内容? " + ", ".join(
    [f"{cn_names[Action(v)]} = {Action(v).value}" for v in Action]
)


@sb_kicker_force.got("action", prompt=action_prompt)
@sb_kicker.got("action", prompt=action_prompt)
async def select_operation(bot: OnebotV11Bot, state: T_State, action: Message = Arg()):
    maybe_action = action.extract_plain_text().strip().upper()
    members: list[JoinedGroupMemberInfo] = state["marked"]

    if maybe_action in actions:
        state["action"] = action = Action(maybe_action)
        img2 = await gen_kick_query_img(title=cn_names[action], members=members)
        await sb_kicker.send(img2)
    else:
        await sb_kicker.finish("没有这个操作。")


confirm_prompt = "confirm? ok = ok, anything else = cancel"


@sb_kicker_force.got("confirm", prompt=confirm_prompt)
@sb_kicker.got("confirm", prompt=confirm_prompt)
async def work(bot: OnebotV11Bot, state: T_State, confirm: Message = Arg()):
    (
        await sb_kicker.finish("canceled")
        if confirm.extract_plain_text().strip().lower() != "ok"
        else None
    )
    picked: List[JoinedGroupMemberInfo] = state["marked"]
    try:
        match state["action"]:
            case Action.SyncEntries:
                for member in picked:
                    member["status"] = MemberStatus.InGroup
                    await Accounts.update_or_create(**J_G_M_to_saveable(member))
            case Action.UndoMarkPendingRemoval:
                await Accounts.filter(
                    id__in=[
                        member["id"] for member in picked if member["id"] is not None
                    ],
                    status=MemberStatus.PendingRemoval,
                ).update(status=MemberStatus.InGroup)
            case Action.MarkPendingRemoval:
                try:
                    await Accounts.filter(
                        id__in=[
                            member["id"]
                            for member in picked
                            if member["id"] is not None
                        ]
                    ).update(status=MemberStatus.PendingRemoval)

                    not_in_db = [member for member in picked if member["id"] is None]

                    accounts = [
                        Accounts(
                            **{
                                k: v
                                for k, v in member.items()
                                if v is not None and k != "status"
                            },
                            status=MemberStatus.PendingRemoval,
                        )
                        for member in not_in_db
                    ]

                    await Accounts.bulk_create(accounts)

                    msg = "\n".join([fmt_user(member) for member in picked])

                    await sb_kicker.send("通知以下用户（手动操作）：\n" + msg)
                except Exception as e:
                    logger.opt(exception=True).error(e)
                    await sb_kicker.finish("操作失败，请查看日志")
            case Action.Kick:
                try:
                    succeed: List[JoinedGroupMemberInfo] = []
                    for member in picked:
                        await sb_kicker.send(cn_names[Action.Kick] + fmt_user(member))
                        await bot.set_group_kick(
                            group_id=SB_GROUP_ID,
                            user_id=member["qq_id"],
                            reject_add_request=False,
                        )
                        await asyncio.sleep(3)
                        succeed.append(member)

                    await Accounts.filter(
                        id__in=[member["id"] for member in succeed]
                    ).update(status=MemberStatus.Removed)

                except Exception as e:
                    logger.opt(exception=True).error(e)
                    await sb_kicker.finish("操作失败，请查看日志。")
            case _:
                await sb_kicker.send("Unknown action")

        await sb_kicker.send("完了。")
    except Exception as e:
        logger.opt(exception=True).error(e)
        await sb_kicker.finish("出现未知错误，请查看日志。")
