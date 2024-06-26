from enum import Enum


class PluginStatus(str, Enum):
    Idle = "idle"
    Running = "running"


class Action(str, Enum):
    SyncEntries = "S"
    MarkPendingRemoval = "M"
    Kick = "K"


cn_names = {
    Action.SyncEntries: '同步数据库',
    Action.MarkPendingRemoval: '通知并标记',
    Action.Kick: '移除',
}

actions = set(item for item in Action)
