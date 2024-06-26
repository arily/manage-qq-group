from nonebot import require

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import on_alconna, AlconnaMatches, Match, AlconnaMatch, CommandResult, AlconnaResult
from .alconna import alc
from arclet.alconna import Arparma
from nonebot.adapters.onebot.v11 import Bot as OnebotV11Bot, MessageEvent, PrivateMessageEvent, GroupMessageEvent
from nonebot.rule import Rule
from .checker import checker_is_sender_bot_admin, checker_is_bot_group_admin, checker_is_plugin_idle
from arclet.alconna import *
from .enums import TableShowType
from models.data import GroupUser


alc_matcher = on_alconna(
    alc, auto_send_output=True  # , rule=Rule(checker_is_sender_bot_admin, checker_is_bot_group_admin)
)


@alc_matcher.assign("help")
async def _():
    await alc_matcher.finish(alc.get_help())


@alc_matcher.assign("show")
async def _(bot: OnebotV11Bot, event: PrivateMessageEvent | GroupMessageEvent, arp: CommandResult = AlconnaResult()):
    arp_show = arp.result.subcommands["show"]
    match arp_show.args["content"]:
        case TableShowType.Weight.value:
            group_id = -1
            if "group_id" in arp_show.options:
                group_id = arp_show.options["group_id"].args["group_id"]
            elif isinstance(event, GroupMessageEvent):
                group_id = event.group_id
            else:
                alc_matcher.finish("请指定群号或在要指定的群内发送")

            resp = await bot.get_group_member_list(group_id=group_id)
            group_users = [GroupUser.parse_obj(i) for i in resp]
            print(resp[0])
    await alc_matcher.finish()


@alc_matcher.assign("mark.available")
async def _():
    await alc_matcher.finish(alc.get_help())


@alc_matcher.assign("mark")
async def _():
    await alc_matcher.finish(alc.get_help())
