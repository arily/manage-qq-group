import os

import dotenv
from loguru import logger
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot as OnebotV11Bot
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

bind = on_command(
    "bind",
    rule=Rule(is_sender_admin),
)


@bind.handle()
def _(matcher: Matcher, state: T_State, args: Message = CommandArg()) -> None:
    state['parsed'] = {}
    v = as_result(Exception)(lambda: args.extract_plain_text().split(" "))().unwrap_or([])
    v = [i.strip() for i in v]
    sb_id = as_result(IndexError, ValueError)(lambda: int(v[0]))().ok()
    qq_id = as_result(IndexError, ValueError)(lambda: int(v[1]))().ok()

    if sb_id is not None:
        state['parsed']['sb_id'] = sb_id
        matcher.set_arg('sb_id', Message(str(sb_id)))

    if qq_id is not None:
        state['parsed']['qq_id'] = qq_id
        matcher.set_arg('qq_id', Message(str(qq_id)))


@bind.got('sb_id', 'sb-id')
async def read_sb_id(state: T_State, sb_id: str = Arg()) -> None:
    s_id = as_result(ValueError)(lambda: int(sb_id))().ok()

    if s_id is None:
        await bind.finish('invalid sb id')

    state['parsed']['sb_id'] = s_id


@bind.got('qq_id', 'qq')
async def read_qq_id(bot: OnebotV11Bot, state: T_State, qq_id: str = Arg()) -> None:
    s_id = as_result(ValueError)(lambda: int(qq_id))().ok()

    if s_id is None:
        await bind.finish('invalid qq id')

    state['parsed']['qq_id'] = s_id


@bind.handle()
async def fin(bot: OnebotV11Bot, state: T_State):
    parsed = state['parsed']
    if parsed['qq_id'] is None or parsed['sb_id'] is None:
        await bind.finish('missing args')

    try:
        qq_user = await bot.get_group_member_info(group_id=SB_GROUP_ID, user_id=int(parsed['qq_id']))
        db_user = await Accounts.get_or_none(group_id=SB_GROUP_ID, qq_id=parsed['qq_id'])

        merged_view = merge_onebot_data_with_db_result(qq_user, db_user)
        merged_view['sb_id'] = parsed['sb_id'] or merged_view['sb_id']

        write_data = J_G_M_to_saveable(merged_view)

        if db_user is None:
            await Accounts.create(**write_data, status=MemberStatus.InGroup)
        else:
            await Accounts.filter(id=db_user.id).update(**write_data, status=MemberStatus.InGroup)

        await bind.send(fmt_user(merged_view))
    except Exception as e:
        logger.opt(exception=True).error(e)
        await bind.send('error occurred')

