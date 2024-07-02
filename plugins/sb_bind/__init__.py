import os
from typing import Optional

import dotenv
from loguru import logger
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot as OnebotV11Bot
from nonebot.adapters.onebot.v11.event import MessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import Message
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Arg
from nonebot.params import CommandArg
from nonebot.rule import Rule
from nonebot.typing import T_State
from result import as_result

from models import Accounts, MemberStatus
from plugins.sb_kicker import merge_onebot_data_with_db_result
from utils import J_G_M_to_saveable
from utils.qq_helper import fmt_user, is_sender_admin

dotenv.load_dotenv()
SB_GROUP_ID = int(os.getenv("SB_GROUP_ID") or "-1")

bind = on_command("sb bind", rule=Rule(is_sender_admin))
remark = on_command("sb remark", rule=Rule(is_sender_admin))
protect = on_command("sb protect", rule=Rule(is_sender_admin))


@bind.handle()
def _bind(matcher: Matcher, state: T_State, args: Message = CommandArg()) -> None:
    state["parsed"] = {}
    v = as_result(Exception)(lambda: args.extract_plain_text().split(" "))().unwrap_or(
        []
    )
    v = [i.strip() for i in v]
    sb_id = as_result(IndexError, ValueError)(lambda: int(v[0]))().ok()
    qq_id = as_result(IndexError, ValueError)(lambda: int(v[1]))().ok()
    remark = as_result(IndexError, ValueError)(lambda: " ".join(v[2:]))().ok()

    if sb_id is not None:
        state["parsed"]["sb_id"] = sb_id
        matcher.set_arg("sb_id", Message(str(sb_id)))

    if qq_id is not None:
        state["parsed"]["qq_id"] = qq_id
        matcher.set_arg("qq_id", Message(str(qq_id)))

    if remark is not None:
        state["parsed"]['data'] = remark
        matcher.set_arg('data', Message(remark))


@remark.handle()
@protect.handle()
def _remark(matcher: Matcher, state: T_State, args: Message = CommandArg()) -> None:
    state["parsed"] = {}
    v = as_result(Exception)(lambda: args.extract_plain_text().split(" "))().unwrap_or(
        []
    )
    v = [i.strip() for i in v]
    qq_id = as_result(IndexError, ValueError)(lambda: int(v[0]))().ok()
    data = as_result(IndexError, ValueError)(lambda: " ".join(v[1:]))().ok()

    if qq_id is not None:
        state["parsed"]["qq_id"] = qq_id
        matcher.set_arg("qq_id", Message(str(qq_id)))

    if data is not None and data != '':
        state["parsed"]["data"] = data
        matcher.set_arg("data", Message(data))


@bind.got("sb_id", "sb-id")
async def read_sb_id(state: T_State, sb_id: Message = Arg()) -> None:
    s_id = as_result(ValueError)(lambda: int(sb_id.extract_plain_text()))().ok()

    if s_id is None:
        await bind.finish("invalid sb id")

    state["parsed"]["sb_id"] = s_id


@bind.got("qq_id", "qq")
@remark.got("qq_id", "qq")
@protect.got("qq_id", "qq")
async def read_qq_id(bot: OnebotV11Bot, state: T_State, qq_id: Message = Arg()) -> None:
    s_id = as_result(ValueError)(lambda: int(qq_id.extract_plain_text()))().ok()

    if s_id is None:
        await bind.finish("invalid qq id")

    state["parsed"]["qq_id"] = s_id


@remark.got("data", "data")
async def read_remark(bot: OnebotV11Bot, state: T_State, data: Message = Arg()) -> None:
    state["parsed"]["data"] = data.extract_plain_text()


@bind.handle()
async def do_bind(bot: OnebotV11Bot, state: T_State, event: MessageEvent):
    parsed = state["parsed"]
    if parsed["qq_id"] is None or parsed["sb_id"] is None:
        await bind.finish("missing args")

    try:
        merged_view, db_user, *_ = await pack_data(bot, qq_id=parsed['qq_id'])

        merged_view["sb_id"] = parsed["sb_id"] or merged_view["sb_id"]
        match parsed["data"].strip():
            case "-":
                merged_view["remark"] = ""

            case "":
                pass

            case str(a):
                merged_view["remark"] = a

        write_data = J_G_M_to_saveable(merged_view)
        write_data["status"] = MemberStatus.InGroup

        if db_user is None:
            await Accounts.create(**write_data)
        else:
            await (
                Accounts
                .filter(id=db_user.id)
                .update(
                    **{k: v for k, v in write_data.items() if v is not None and k != "id"}
                )
            )

        await bind.send(
            fmt_user(merged_view, private=isinstance(event, PrivateMessageEvent))
        )
    except Exception as e:
        logger.opt(exception=True).error(e)
        await bind.send("error occurred")


@remark.handle()
async def do_remark(bot: OnebotV11Bot, state: T_State, event: MessageEvent):
    parsed = state["parsed"]
    if parsed["qq_id"] is None:
        await bind.finish("missing args")

    try:
        merged_view, db_user, *_ = await pack_data(bot, qq_id=parsed['qq_id'])

        match parsed["data"].strip():
            case "-":
                merged_view["remark"] = ""

            case "":
                pass

            case str(a):
                merged_view["remark"] = a

        write_data = J_G_M_to_saveable(merged_view)

        if db_user is None:
            await Accounts.create(**write_data)
        else:
            await (
                Accounts.
                filter(id=db_user.id)
                .update(
                    **{k: v for k, v in write_data.items() if v is not None and k != "id"}
                )
            )

        await bind.send(
            fmt_user(merged_view, private=isinstance(event, PrivateMessageEvent))
        )
    except Exception as e:
        logger.opt(exception=True).error(e)
        await bind.send("error occurred")


@protect.handle()
async def do_whitelist(bot: OnebotV11Bot, state: T_State, event: MessageEvent):
    parsed = state["parsed"]
    if parsed["qq_id"] is None:
        await bind.finish("missing args")

    try:
        merged_view, db_user, *_ = await pack_data(bot, qq_id=parsed['qq_id'])
        merged_view["whitelisted"] = 'data' in parsed and parsed["data"].strip() != ""

        write_data = J_G_M_to_saveable(merged_view)

        if db_user is None:
            await Accounts.create(**write_data)
        else:
            await (
                Accounts
                .filter(id=db_user.id)
                .update(
                    **{k: v for k, v in write_data.items() if v is not None and k != "id"}
                )
            )

        await bind.send(
            fmt_user(merged_view, private=isinstance(event, PrivateMessageEvent))
        )
    except Exception as e:
        logger.opt(exception=True).error(e)
        await bind.send("error occurred")


async def pack_data(bot: OnebotV11Bot, qq_id: int, sb_id: Optional[int] = None):
    qq_user = await bot.get_group_member_info(
        group_id=SB_GROUP_ID,
        user_id=qq_id,
    )
    db_user = await Accounts.get_or_none(
        group_id=SB_GROUP_ID,
        qq_id=qq_id,
    )

    merged_view = merge_onebot_data_with_db_result(qq_user, db_user)

    return merged_view, db_user, qq_user
