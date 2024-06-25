from typing import Literal

from arclet.alconna import *


alc = Alconna(
    "sb-kicker",
    Subcommand(
        "show",
        Args["content", str],
        help_text="显示自定义查询表"
    ),
    Subcommand(
        "help",
        help_text="显示帮助文本",
    ),
    Subcommand(
        "mark",
        Subcommand(
            "a|available",
            help_text="显示可用的标记类型"
        ),
        Args[
            Arg("mark_type", str, flags=[ArgFlag.OPTIONAL])
        ],
        help_text="显示自定义查询表"
    ),
    meta=CommandMeta(
        description="超级无敌sb群t人cheater",
        usage="sb-kicker [command] [args]",
        example="sb-kicker show",
    )
)
