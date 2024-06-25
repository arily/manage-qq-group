from models.data import GroupUser
from models.db import Caches
from .enums import PluginStatus


def calculate_kick_weight(current_time: float, user: GroupUser):
    if user is None:
        return 0

    inactive_seconds = current_time - user.last_sent_time

    # 用户每增加一个level 权重降低1%，同时减去30天的潜水时长

    weight = (
            inactive_seconds * ((100 - int(user.level)) / 100)
            - int(user.level) * 30 * 24 * 60 * 60
    )

    if user["whitelisted"]:  # TODO: 改
        weight *= 0.2

    if user["sb_id"]:  # TODO: 改
        weight *= 0.5

    # match user['status']:
    #     case MemberStatus.InGroup:
    #         pass
    #     case MemberStatus.PendingRemoval:
    #         weight *= 2
    #     case MemberStatus.Removed:
    #         weight *= 0.01

    return weight / 10000


async def check_plugin_running() -> bool:
    cache, _ = await Caches.get_or_create(
        key="sb_kicker_status", defaults={"value": PluginStatus.Idle.value}
    )
    if cache.value == PluginStatus.Running.value:
        return True
    return False

