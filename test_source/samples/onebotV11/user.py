from nonebot.adapters.onebot.v11.event import Sender

from test_source.config import admin_user

admin_sender = Sender(
    user_id=admin_user["user_id"],
    nickname=admin_user["nickname"],
    age=18,
    area=None,
    card=None,
    level=None,
    role=None,
    sex="unknown",
    title=None,
)

normal_sender = Sender(
    user_id=1000000012,
    nickname="Test Normal User",
    age=16,
    area=None,
    card=None,
    level=None,
    role=None,
    sex="unknown",
    title=None,
)