from nonebot import on_command
from nonebot import rule
from nonebot.plugin import on
from nonebot.typing import T_State
from nonebot.config import Config
from nonebot.adapters import Bot, Event

printer_responser = on("message", rule.keyword("打印"), priority=5)

@printer_responser.handle()
async def send_printer_response(bot: Bot, event: Event):
    print(event.get_session_id().split('_'))
    print(event.get_message())