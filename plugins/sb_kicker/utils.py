import base64
from copy import deepcopy
from datetime import datetime
import os
from typing import Callable, List, Optional, TypeVar

import dotenv
from nonebot.adapters.onebot.v11 import MessageSegment

from models.db import Caches, Accounts
from utils.web import screenshot_local_html, trans_md_to_html
from . import PluginStatus


from models.types import GroupMemberInfo, JoinedGroupMemberInfo


dotenv.load_dotenv()
SB_GROUP_ID = int(os.getenv("SB_GROUP_ID"))


def calculate_kick_weight(current_time: float, member: JoinedGroupMemberInfo):
    if member is None:
        return 0

    inactive_seconds = current_time - member["last_sent_time"]

    # 用户每增加一个level 权重降低1%，同时减去30天的潜水时长

    weight = (
        inactive_seconds * ((100 - int(member["level"])) / 100)
        - int(member["level"]) * 30 * 24 * 60 * 60
    )

    if member["whitelisted"]:
        weight = weight * 0.2

    if member["sb_id"]:
        weight = weight * 0.5

    return weight / 10000


async def check_plugin_running() -> bool:
    cache, _ = await Caches.get_or_create(
        key="sb_kicker_status", defaults={"value": PluginStatus.Idle.value}
    )
    if cache.value == PluginStatus.Running.value:
        return True
    return False


async def gen_kick_query_msg(members: List[JoinedGroupMemberInfo]):
    reply_msg = (
        "# 潜水榜 \n\n"
        "| ID | 昵称 | QQ号 | SB服绑定的ID | 备注 | 白名单 | QQ等级 | 最后发言时间 | 计算的权重 |  \n"
        "|---:| --- | ----:| -----------:| --- | :---: | ----: | ---------- | ---------:|  \n"
    )
    for i in range(30):
        member = members[i]
        reply_msg += (
            f"| {i} "
            f"| {member['card'] if member['card'] is not None else member['nickname']} "
            f"| {member['qq_id']} "
            f"| {member['sb_id']} "
            f"| {member['comment']} "
            f"| {'☑️' if member['whitelisted'] else ''} "
            f"| {member['level']} "
            f"| {datetime.fromtimestamp(member['last_sent_time']).isoformat()} "
            f"| {member['weight']:9.2f} "
            f"|  \n"
        )
    reply_msg += "  \n"

    html = trans_md_to_html(reply_msg)
    img_bin = await screenshot_local_html(html)
    return MessageSegment.image(
        file="base64://" + base64.b64encode(img_bin).decode(encoding="utf-8")
    )


def merge_onebot_data_with_db_result(
    onebot_data: GroupMemberInfo, db_data: Optional[Accounts]
) -> JoinedGroupMemberInfo:
    maybe_onebot = deepcopy(onebot_data)
    qq_id = maybe_onebot.pop("user_id")
    db_data = db_data or Accounts()
    return_value = JoinedGroupMemberInfo(
        **maybe_onebot,
        qq_id=db_data.qq_id or qq_id,
        whitelisted=db_data.whitelisted or False,
        sb_id=db_data.sb_id or None,
        comment=db_data.comment or "",
    )
    return return_value


async def get_accounts_with_db_data(onebot_data: List[GroupMemberInfo]):
    return [
        merge_onebot_data_with_db_result(
            member,
            find_in(
                await Accounts.filter(
                    group_id=SB_GROUP_ID,
                    qq_id__in=[member["user_id"] for member in onebot_data],
                ),
                lambda x, m=member: x.qq_id == m["user_id"],
            ),
        )
        for member in onebot_data
    ]


T = TypeVar("T")


def find_in(_list: List[T], matcher: Callable[[T], bool]):
    for item in _list:
        if matcher(item):
            return item
