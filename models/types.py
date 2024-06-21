from typing import Optional, TypedDict
from models.db import Accounts


class GroupMemberInfo(TypedDict):
    group_id: int  # 	number (int64)	群号
    user_id: int  # 	number (int64)	QQ 号
    nickname: str  # 	string	昵称
    card: str  # 	string	群名片／备注
    sex: str  # 	string	性别，male 或 female 或 unknown
    age: int  # 	number (int32)	年龄
    # area: str  # 	string	地区
    join_time: int  # 	number (int32)	加群时间戳
    last_sent_time: int  # 	number (int32)	最后发言时间戳
    level: str  # 	string	成员等级
    role: str  # 	string	角色，owner 或 admin 或 member
    unfriendly: str  # 	boolean	是否不良记录成员
    # title: str  # 	string	专属头衔
    title_expire_time: int  # 	number (int32)	专属头衔过期时间戳
    # card_changeable: Any  #


class JoinedGroupMemberInfo(GroupMemberInfo):
    user_id: None
    qq_id: int
    remark: str
    sb_id: Optional[int]
    whitelisted: Optional[bool]
    weight: int
