import asyncio
import base64
from datetime import datetime, timezone

import mistune
from alicebot import Plugin
from alicebot.adapter.cqhttp import CQHTTPAdapter
from alicebot.adapter.cqhttp.event import PrivateMessageEvent
from alicebot.adapter.cqhttp.message import CQHTTPMessageSegment
from alicebot.exceptions import GetEventTimeout
from playwright.async_api import async_playwright


class SBKicker(Plugin):
    priority: int = 0
    block: bool = False

    def __init_state__(self):
        return {
            "status": 0
        }

    async def handle(self) -> None:
        adapter: CQHTTPAdapter = self.event.adapter
        event: PrivateMessageEvent = self.event

        sb_group_id = 792778662

        if self.state["status"] == 1:
            await event.reply("上次的还在T啊，要不等会?")
            return

        await event.reply("稍等...")

        resp = await adapter.call_api("get_group_member_list", group_id=sb_group_id)

        current_time = datetime.now(timezone.utc).timestamp()
        member_weights = [(member['user_id'], self.calculate_weight(current_time, member)) for member in resp]
        member_weights = sorted(member_weights, key=lambda x: x[1], reverse=True)

        members_dict = {member['user_id']: member for member in resp}  # 将成员列表转换为以 user_id 为键的字典 提性能
        reply_msg = (
            "# 最应该送走的用户，权重越大越该送  \n\n"
            "| ID | qq号 | 昵称 | 等级 | 最后发言时间 | 计算的权重 |  \n"
            "| --- | --- | --- | --- | --- | --- |  \n"
        )
        for i in range(30):
            member = members_dict[member_weights[i][0]]
            reply_msg += (f"| {i} "
                          f"| {member['user_id']} "
                          f"| {member['nickname'] if member['card'] is None else member['card']} "
                          f"| {member['level']} "
                          f"| {datetime.fromtimestamp(member['last_sent_time']).isoformat()} "
                          f"| {round(member_weights[i][1])} "
                          f"|  \n")
        reply_msg += "  \n"

        reply_msg = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                {open("libs/markdown/github-markdown.css").read()}
            </style>
        </head>
        <body style="padding: 30px">
            <article class="markdown-body">
                {mistune.html(reply_msg)}
            </article>
        </body>
        </html>
        """

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("about:blank")
            await page.set_content(reply_msg)
            screenshot_binary = await page.screenshot(full_page=True)

        await event.reply(CQHTTPMessageSegment.image(f"base64://{base64.b64encode(screenshot_binary).decode('utf-8')}"))

        while True:
            try:
                ask_answer = await event.ask("送走几个(从上到下)？\n输入no取消(180s后自动取消)", timeout=180)
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
                await adapter.call_api("set_group_kick", group_id=sb_group_id, user_id=member_weights[i][0], reject_add_request=False)  # noqa
                await event.reply(
                    f"已送走{members_dict[member_weights[i][0]]['card']}({member_weights[i][0]}) [{i + 1}/{int(ask_answer.get_plain_text())}]"  # noqa
                )
                await asyncio.sleep(3)
            await event.reply("送完了")
        finally:
            self.state["status"] = 0

    async def rule(self) -> bool:
        if not isinstance(self.event, PrivateMessageEvent):
            return False
        event: PrivateMessageEvent = self.event
        if event.sender.user_id != 1483492332:
            print(event.sender)
            return False

        if event.message.get_plain_text() == "sb群送人":
            return True
        return False

    @staticmethod
    def calculate_weight(current_time: float, member):
        if member is None:
            return 0

        inactive_days = (current_time - member['last_sent_time']) / (60 * 60 * 24)

        weight = inactive_days * (101 - int(member['level']))
        return weight
