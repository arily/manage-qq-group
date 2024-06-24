from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.internal.rule import Rule
import base64

from utils.web import trans_md_to_html, screenshot_local_html


async def checker_is_group_message(event: GroupMessageEvent) -> bool:
    return isinstance(event, GroupMessageEvent)


help_matcher = on_fullmatch("!help", rule=Rule(checker_is_group_message))
admin_help_matcher = on_fullmatch("!helpadmin", rule=Rule(checker_is_group_message))


@help_matcher.handle()
async def _():
    html = trans_md_to_html(open("resources/docs/help/NormalHelp.md", encoding="utf-8").read())
    img_bin = await screenshot_local_html(html)
    await help_matcher.finish(MessageSegment.image(file="base64://" + base64.b64encode(img_bin).decode(encoding="utf-8")))


@admin_help_matcher.handle()
async def _():
    html = trans_md_to_html(open("resources/docs/help/AdminHelp.md", encoding="utf-8").read())
    img_bin = await screenshot_local_html(html)
    await admin_help_matcher.finish(MessageSegment.image(file="base64://" + base64.b64encode(img_bin).decode(encoding="utf-8")))
