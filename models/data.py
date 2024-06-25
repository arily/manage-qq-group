from typing import Optional

import pydantic


class GroupUser(pydantic.BaseModel):
    group_id: int
    user_id: int
    nickname: str
    card: Optional[str]
    sex: Optional[str]
    age: Optional[int]
    area: Optional[str]
    join_time: Optional[int]
    last_sent_time: Optional[int]
    level: Optional[str]
    role: Optional[str]
    title: Optional[str]
    title_expire_time: Optional[int]
    card_changeable: Optional[bool]
