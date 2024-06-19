import asyncio
import base64
from datetime import datetime, timezone
from typing import List, TypedDict, Any

import mistune
from alicebot import Plugin
from alicebot.adapter.cqhttp import CQHTTPAdapter
from alicebot.adapter.cqhttp.event import PrivateMessageEvent
from alicebot.adapter.cqhttp.message import CQHTTPMessageSegment
from alicebot.exceptions import GetEventTimeout
from playwright.async_api import async_playwright
from .db import Accounts, Admins
from .html import HTML as h

from tortoise.expressions import F


class GetGroupMemberList(TypedDict):
    user_id: int
    card: Any
    nickname: str
    last_sent_time: float
    level: int


class SBKicker(Plugin):
    priority: int = 0
    block: bool = False
    trigger = "sb群送人"
    group = 792778662
    _cached_head = ""

    @property
    def cached_head(self):
        return self._set_head() if self._cached_head == "" else self._cached_head

    def _set_head(self) -> str:
        self._cached_head = h.head(
            h.style(open("libs/markdown/github-markdown.css").read())
        )
        return self._cached_head

    def __init_state__(self):
        return {"status": 0}

    async def handle(self) -> None:
        event: PrivateMessageEvent = self.event
        adapter: CQHTTPAdapter = event.adapter

        if self.state["status"] == 1:
            await event.reply("上次的还在T啊，要不等会?")
            return

        await event.reply("稍等...")

        resp: List[GetGroupMemberList] = await adapter.call_api(
            "get_group_member_list", group_id=self.group
        )

        current_time = datetime.now(timezone.utc).timestamp()
        member_weights = [
            (member["user_id"], self.calculate_weight(current_time, member))
            for member in resp
        ]
        member_weights = sorted(member_weights, key=lambda x: x[1], reverse=True)

        members_dict = {
            member["user_id"]: member for member in resp
        }  # 将成员列表转换为以 user_id 为键的字典 提性能
        reply_msg = (
            "# 最应该送走的用户，权重越大越该送  \n\n"
            "| ID | qq号 | 昵称 | 等级 | 最后发言时间 | 计算的权重 |  \n"
            "| --- | --- | --- | --- | --- | --- |  \n"
        )
        for i in range(30):
            member = members_dict[member_weights[i][0]]
            reply_msg += (
                f"| {i} "
                f"| {member['user_id']} "
                f"| {member['card'] if member['card'] is not None else member['nickname']} "
                f"| {member['level']} "
                f"| {datetime.fromtimestamp(member['last_sent_time']).isoformat()} "
                f"| {round(member_weights[i][1])} "
                f"|  \n"
            )
        reply_msg += "  \n"

        b64content = base64.b64encode(
            await self.screenshot(
                h.html(
                    self.cached_head,
                    h.body(
                        h.tag(
                            "article",
                            mistune.html(reply_msg),
                            class_name="markdown-body",
                        ),
                        style="padding: 30px",
                    ),
                )
            )
        ).decode("utf-8")

        await event.reply(CQHTTPMessageSegment.image(f"base64://{b64content}"))
        await self.sync_members(resp)

        while True:
            try:
                ask_answer = await event.ask(
                    "送走几个(从上到下)？\n输入no取消(180s后自动取消)", timeout=180
                )
            except GetEventTimeout:
                return
            else:
                if ask_answer.get_plain_text() == "no":
                    await event.reply("取消送人")
                    return
                try:
                    int(ask_answer.get_plain_text())
                except ValueError:
                    await event.reply("再试一次，能不能输个数字？")
                    await asyncio.sleep(1)
                else:
                    break

        try:
            self.state["status"] = 1
            for i in range(int(ask_answer.get_plain_text())):
                await adapter.call_api(
                    "set_group_kick",
                    group_id=self.group,
                    user_id=member_weights[i][0],
                    reject_add_request=False,
                )  # noqa
                await event.reply(
                    f"已送走{members_dict[member_weights[i][0]]['card']}({member_weights[i][0]}) [{i + 1}/{int(ask_answer.get_plain_text())}]"
                    # noqa
                )
                await asyncio.sleep(3)
            await event.reply("送完了")
        finally:
            self.state["status"] = 0

    async def rule(self) -> bool:
        if not isinstance(self.event, PrivateMessageEvent):
            return False

        event: PrivateMessageEvent = self.event

        if not await self.is_admin(event.sender.user_id):
            return False

        if event.message.get_plain_text().strip() != self.trigger:
            return False

        return True

    async def sync_members(self, members: List[GetGroupMemberList] = None):
        if members is None:
            members = await self.event.adapter.call_api(
                "get_group_member_list", group_id=self.group
            )

        existing_accounts = Accounts.filter(
            F(Accounts.group_id == self.group),
            F(Accounts.qq_id).contains([member["user_id"] for member in members]),
        )

        existing_ids = [acc.qq_id for acc in existing_accounts]

        await Accounts.bulk_create(
            Accounts(group_id=self.group, qq_id=member["user_id"])
            for member in members
            if member["user_id"] not in existing_ids
        )

    @staticmethod
    def calculate_weight(current_time: float, member):
        if member is None:
            return 0

        inactive_days = (current_time - member["last_sent_time"]) / (60 * 60 * 24)

        weight = inactive_days * (101 - int(member["level"]))
        return weight

    @staticmethod
    async def is_admin(qq_id: int):
        return await Admins.exists(qq_id=qq_id)

    @staticmethod
    async def screenshot(content: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("about:blank")
            await page.set_content(content)
            return await page.screenshot(full_page=True)
