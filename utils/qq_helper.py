from typing import List

from nonebot.adapters.onebot.v11 import Bot as OnebotV11Bot
import nonebot


async def is_admin(bot: OnebotV11Bot, group_id: int):
    self_info = await bot.get_group_member_info(group_id=group_id, user_id=int(bot.self_id))
    if self_info["role"] in ["owner", "admin"]:
        return True
    return False


async def get_multi_group_member_list(bot: OnebotV11Bot, group_ids: List[int]):
    resp = []
    for group in group_ids:
        for i in (await bot.get_group_member_list(group_id=group)):
            i["group_id"] = group
            resp.append(i)
    return resp
