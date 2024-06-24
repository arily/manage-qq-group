from tortoise.models import Model
from tortoise import fields
from .enums import *


class Users(Model):
    class Meta:
        table = "users"

    id = fields.IntField(pk=True)
    group_id = fields.IntField(index=True)
    qq_id = fields.IntField(index=True)
    sb_id = fields.IntField(null=True, index=True)
    comment = fields.TextField(null=True)


class BotOperationPrivileges(Model):
    class Meta:
        table = "bot_operation_privileges"

    id = fields.IntField(pk=True)
    qq_id = fields.IntField(index=True)
    group_id = fields.IntField(index=True)
    privilege = fields.IntEnumField(BotOperationPrivilegeEnum, index=True)
    comment = fields.TextField(null=True)


class UserPrivileges(Model):
    class Meta:
        table = "user_privileges"

    id = fields.IntField(pk=True)
    qq_id = fields.IntField(index=True)
    group_id = fields.IntField(index=True)
    privilege = fields.IntEnumField(UserPrivilegeEnum, index=True)


class Logs(Model):
    class Meta:
        table = "logs"

    id = fields.IntField(pk=True)
    time = fields.IntField()
    admin = fields.IntField(index=True)
    operation = fields.IntEnumField(OperationEnum)
    operated_object = fields.IntField(null=True, index=True)
    comment = fields.TextField(null=True)


class Caches(Model):
    class Meta:
        table = "caches"

    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=255, index=True)
    value = fields.TextField()
