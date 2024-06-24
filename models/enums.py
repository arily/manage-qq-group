from enum import IntEnum


class OperationEnum(IntEnum):
    AddToWhiteList = 0
    KickOutGroup = 1


class UserPrivilegeEnum(IntEnum):
    KickWhitelist = 0


class BotOperationPrivilegeEnum(IntEnum):
    All = 0
    Zero = 1
