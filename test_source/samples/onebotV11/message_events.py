from datetime import datetime

from nonebot.adapters.onebot.v11 import PrivateMessageEvent, Message
from nonebot.adapters.onebot.v11.event import Sender

from .user import normal_sender


def private_message_event_normal(
        msg: str,
        user_id: int = normal_sender.user_id,
        nickname: str = normal_sender.nickname,
        msg_id: int = 100000,
        self_id: int = 10000,
) -> PrivateMessageEvent:
    return PrivateMessageEvent(
        time=int(datetime.now().timestamp()),
        self_id=self_id,
        message=Message(msg),
        raw_message=msg,
        message_id=msg_id,
        user_id=user_id,
        message_type="private",
        sender=Sender(
            user_id=user_id,
            nickname=nickname,
            age=18,
            area=None,
            card=None,
            level=None,
            role=None,
            sex="unknown",
            title=None,
        ),
        to_me=True,
        post_type="message",
        sub_type="friend",
        font=0,
    )
