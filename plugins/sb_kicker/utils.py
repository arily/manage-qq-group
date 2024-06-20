import base64
from datetime import datetime

from nonebot.adapters.onebot.v11 import MessageSegment

from models.db import Caches
from utils.web import screenshot_local_html, trans_md_to_html
from . import PluginStatus


def calculate_kick_weight(current_time: float, member):
    if member is None:
        return 0

    inactive_days = (current_time - member["last_sent_time"]) / (60 * 60 * 24)

    weight = inactive_days * (101 - int(member["level"]))
    return weight


async def check_plugin_running() -> bool:
    cache, _ = await Caches.get_or_create(
        key="sb_kicker_status",
        defaults={
            "value": PluginStatus.Idle.value
        }
    )
    if cache.value == PluginStatus.Running.value:
        return True
    return False


async def gen_kick_query_msg(members_dict, member_weights):
    reply_msg = (
        "# 最应该送走的用户，权重越大越该送  \n\n"
        "| ID | qq号 | 昵称 | 等级 | 最后发言时间 | 计算的权重 |  \n"
        "| --- | --- | --- | --- | --- | --- |  \n"
    )
    for i in range(30):
        member = members_dict[member_weights[i][0]]
        reply_msg += (
            f"| {i} "
            f"| {member['user_id']} "
            f"| {member['card'] if member['card'] is not None else member['nickname']} "
            f"| {member['level']} "
            f"| {datetime.fromtimestamp(member['last_sent_time']).isoformat()} "
            f"| {round(member_weights[i][1])} "
            f"|  \n"
        )
    reply_msg += "  \n"

    html = trans_md_to_html(reply_msg)
    img_bin = await screenshot_local_html(html)
    return MessageSegment.image(file="base64://" + base64.b64encode(img_bin).decode(encoding="utf-8"))

