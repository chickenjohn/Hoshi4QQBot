from nonebot import on_command
from nonebot import rule
from nonebot.plugin import on
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import utils
from nonebot.config import Config
from ..libs.file_reader import encode_f_to_cq
from ..libs.asoul_cnki import asoul_cnki_mod

search_compo = on("message", rule.keyword("查重") & rule.to_me(), priority=4)

@search_compo.handle()
async def search_compo_fisrt_rec(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    arg_list = args.split(" ")
    if len(arg_list) > 1:    
        if len(arg_list) > 2:
            state['compo'] = ' '.join(arg_list[1:])
        else:
            state['compo'] = arg_list[-1]
        
        state["compo"] = state["compo"].replace("&amp;", "&")
            
@search_compo.got(key="compo", prompt="请输入小作文（10~1000个字）")
async def check_music_handle_name(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if state.get("compo", None) is None:
        state["compo"] = args.replace("&amp;", "&")

    if 10 <= len(state["compo"]) < 1000:
        test_res = await asoul_cnki_mod(state["compo"])
    else:
        test_res = "小作文应该不少于10个字，不多于1000字"

    if test_res is not None:
        await search_compo.finish(test_res)