import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
from init.database import init as database_init, disconnect as database_disconnect

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

driver.on_startup(database_init)
driver.on_shutdown(database_disconnect)

nonebot.load_builtin_plugins("echo")  # 内置插件
nonebot.load_plugins("plugins")

if __name__ == "__main__":
    nonebot.run()
