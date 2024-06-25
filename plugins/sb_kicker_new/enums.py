from enum import Enum


class PluginStatus(Enum):
    Idle = "idle"
    Running = "running"


class TableShowType(Enum):
    Weight = "weight"
    T2 = "t2"

