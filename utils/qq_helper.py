import os

from nonebot.adapters.onebot.v11 import Bot as OnebotV11Bot, MessageEvent

from models.db import Admins
from models.types import JoinedGroupMemberInfo

import dotenv

dotenv.load_dotenv()
SB_GROUP_ID = int(os.getenv("SB_GROUP_ID") or "-1")


async def is_admin(bot: OnebotV11Bot, group_id: int):
    try:
        self_info = await bot.get_group_member_info(group_id=group_id, user_id=int(bot.self_id))
        if self_info["role"] in ["owner", "admin"]:
            return True
        return False
    except Exception as e:
        return False


def fmt_user(member: JoinedGroupMemberInfo):
    return f"{member['nickname']}(qq = {member['qq_id']}, sb = {member['sb_id']})"


async def is_sender_admin(event: MessageEvent) -> bool:
    return await Admins.exists(qq_id=event.sender.user_id)


async def is_bot_group_admin(bot: OnebotV11Bot):
    return await is_admin(bot, SB_GROUP_ID)
