from typing import List

from models.db import Accounts
from models.enums import MemberStatus
from models.types import JoinedGroupMemberInfo


async def sync_in_group(members: List[JoinedGroupMemberInfo]):
    await (
        Accounts
        .filter(
            id__in=[members['id'] for members in members],
            status=MemberStatus.Removed
        )
        .update(
            status=MemberStatus.InGroup
        )
    )
    for member in members:
        member['status'] = MemberStatus.InGroup \
            if member['status'] == MemberStatus.Removed \
            else member['status']
