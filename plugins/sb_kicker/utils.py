import base64
from copy import deepcopy
from datetime import datetime
import os
from typing import Callable, List, Optional, TypeVar

import dotenv
from nonebot.adapters.onebot.v11 import MessageSegment

from models.db import Caches, Accounts
from models.enums import MemberStatus
from utils.web import render_html_as_image, render_md_to_html
from . import PluginStatus

from models.types import GroupMemberInfo, JoinedGroupMemberInfo
from inspect import signature

T = TypeVar("T")

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
        weight *= 0.2

    if member["sb_id"]:
        weight *= 0.5

    match member['status']:
        case MemberStatus.InGroup:
            pass
        case MemberStatus.PendingRemoval:
            weight *= 2
        case MemberStatus.Removed:
            weight *= 0.01

    return weight / 10000


async def check_plugin_running() -> bool:
    cache, _ = await Caches.get_or_create(
        key="sb_kicker_status", defaults={"value": PluginStatus.Idle.value}
    )
    if cache.value == PluginStatus.Running.value:
        return True
    return False


async def gen_kick_query_img(title: str, members: List[JoinedGroupMemberInfo]):
    header = (
        f"# {title} \n\n"
        "| ID | 白名单 | 昵称 | SB服ID | QQ | QQ等级 | 状态 | 备注 | 最后发言时间 | 计算的权重 |  \n"
        "|---:| :---: | --- | ------:| --:| -----:| ---- | --- | ---------- | --------:|  \n"
    )

    items = (
        (
            f"| {i} "
            f"| {'☑️' if member['whitelisted'] else ''} "
            f"| {member['card'] if member['card'] is not None else member['nickname']} "
            f"| `{member['sb_id']}` "
            f"| `{member['qq_id']}` "
            f"| `{member['level']}` "
            f"| {MemberStatus(member['status']).name if member['status'] is not None and member['status'] in MemberStatus else '-'} "
            f"| {member['remark']} "
            f"| `{datetime.fromtimestamp(member['last_sent_time'])}` "
            f"| `{member['weight']:9.2f}` "
            f"|"
        ) for i, member in enumerate(members)
    )

    html = render_md_to_html(header + "\n".join(items) + '\n')
    img_bin = await render_html_as_image(html)
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
        id=db_data.id,
        updated_at=db_data.updated_at,
        created_at=db_data.created_at,
        status=db_data.status,
        qq_id=db_data.qq_id or qq_id,
        whitelisted=db_data.whitelisted or False,
        sb_id=db_data.sb_id or None,
        remark=db_data.remark or "",
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
                lambda x: x.qq_id == member["user_id"],
            ),
        )
        for member in onebot_data
    ]


def find_in(
        _list: List[T],
        matcher: Callable[[], bool] | Callable[[T], bool] | Callable[[T, int], bool] | Callable[[T, int, List[T]], bool]
) -> T:
    func = overload_filter_func(matcher)
    for idx, item in enumerate(_list):
        if func(item, idx, _list):
            return item


def filter_in(
        _list: List[T],
        matcher: Callable[[], bool] | Callable[[T], bool] | Callable[[T, int], bool] | Callable[[T, int, List[T]], bool]
) -> List[T]:
    func = overload_filter_func(matcher)
    return [item for idx, item in enumerate(_list) if func(item, idx, _list)]


def overload_filter_func(
        matcher: Callable[[], bool] | Callable[[T], bool] | Callable[[T, int], bool] | Callable[[T, int, List[T]], bool]
):
    sig = signature(matcher)
    params = sig.parameters
    p_len = len(params)
    fun1 = lambda i, x, l: matcher(i)
    fun2 = lambda i, x, l: matcher(i, x)
    fun3 = lambda i, x, l: matcher(i, x, l)

    return fun1 if p_len == 1 else fun2 if p_len == 2 else fun3
