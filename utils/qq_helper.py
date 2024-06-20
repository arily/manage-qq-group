from nonebot.adapters.onebot.v11 import Bot as OnebotV11Bot
import nonebot


async def is_admin(bot: OnebotV11Bot, group_id: int):
    self_info = await bot.get_group_member_info(group_id=group_id, user_id=int(bot.self_id))
    if self_info["role"] in ["owner", "admin"]:
        return True
    return False
