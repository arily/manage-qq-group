from enum import Enum, IntEnum


class MemberStatus(IntEnum):
    InGroup = 0
    PendingRemoval = 90
    Removed = 99


class OpType(Enum):
    SetWhitelist = "set-whitelist"
    UnsetWhitelist = "unset-whitelist"
    Notify = "notify"
    Kick = "kick"
