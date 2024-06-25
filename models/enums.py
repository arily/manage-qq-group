from enum import IntEnum


class OperationEnum(IntEnum):
    AddToWhiteList = 0
    KickOutGroup = 1


class BotOperationPrivilegeEnum(IntEnum):
    All = 0
    Zero = 1


class SbKickerMarkEnum(IntEnum):
    Whitelist = 0
    KickExemptionLevelPromotion = 1
    KickExemptionLevelDemotion = 2
    HaveNotified = 3

