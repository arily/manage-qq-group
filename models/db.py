from tortoise.models import Model
from tortoise import fields
from .enums import *


class Accounts(Model):
    class Meta:
        table = "accounts"

    id = fields.IntField(pk=True)
    group_id = fields.IntField(index=True)
    qq_id = fields.IntField(index=True)
    sb_id = fields.IntField(null=True, index=True)
    remark = fields.TextField(default="")
    whitelisted = fields.BooleanField(default=False)


class Admins(Model):
    class Meta:
        table = "admins"

    id = fields.IntField(pk=True)
    qq_id = fields.IntField(index=True)


class Logs(Model):
    class Meta:
        table = "logs"

    id = fields.IntField(pk=True)
    time = fields.DatetimeField()
    account_id = fields.IntField(index=True)
    admin_id = fields.IntField(index=True)
    op = fields.CharEnumField(OpType)


class Caches(Model):
    class Meta:
        table = "caches"

    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=255, index=True)
    value = fields.TextField()
