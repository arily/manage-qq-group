from nonebot import require

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import on_alconna, AlconnaMatches, Match, AlconnaMatch, CommandResult, AlconnaResult
from .alconna import alc
from arclet.alconna import Arparma
from nonebot.adapters.onebot.v11 import Bot as OnebotV11Bot
from nonebot.rule import Rule
from .checker import checker_is_sender_bot_admin, checker_is_bot_group_admin, checker_is_plugin_idle
from arclet.alconna import *
from .enums import TableShowType


alc_matcher = on_alconna(
    alc, auto_send_output=True  # , rule=Rule(checker_is_sender_bot_admin, checker_is_bot_group_admin)
)


@alc_matcher.assign("help")
async def _():
    await alc_matcher.finish(alc.get_help())


@alc_matcher.assign("show")
async def _(arp: CommandResult = AlconnaResult()):
    match arp.result.subcommands["show"].args["content"]:
        case TableShowType.Weight:
            pass
    await alc_matcher.finish()


@alc_matcher.assign("mark.available")
async def _():
    await alc_matcher.finish(alc.get_help())


@alc_matcher.assign("mark")
async def _():
    await alc_matcher.finish(alc.get_help())
