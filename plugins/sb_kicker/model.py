from datetime import datetime
from enum import Enum
from typing import Optional

from tortoise.models import Model
from tortoise import fields
from tortoise import Tortoise


class OpType(Enum):
    AddToWhiteList = "whitelist"
    Kick = "kick"


class Accounts(Model):
    id = fields.IntField(pk=True)
    group_id = fields.IntField(index=True)
    qq_id = fields.IntField(index=True)
    sb_id = fields.IntField(null=True, index=True)
    comment = fields.TextField(default="")
    whitelisted = fields.BooleanField(default=False)


class Admins(Model):
    id = fields.IntField(pk=True)
    qq_id = fields.IntField(index=True)


class Logs(Model):
    id = fields.IntField(pk=True)
    time = fields.DatetimeField()
    account_id = fields.IntField(index=True)
    admin_id = fields.IntField(index=True)
    op = fields.TextField()





















