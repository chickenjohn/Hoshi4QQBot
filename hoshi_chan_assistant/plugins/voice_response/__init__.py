from nonebot import on_command
from nonebot import rule
from nonebot.plugin import on, on_regex
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import utils
from nonebot.config import Config
from nonebot.log import logger
from ..libs.file_reader import encode_f_to_cq

import os, os.path
import random
import re

GRP_IDS = [str(Config(".env").cap_grp_id), str(Config(".env").adm_grp_id), str(Config(".env").grp_id)]
GACHI_GRP_ID = [str(Config(".env").adm_grp_id), str(Config(".env").grp_id)]
vocal_lib_path = Config(".env").vocal_lib


async def patpat_rule(bot: Bot, event: Event, state: T_State) -> bool:
    '''
    detect poke notice("戳一戳")
    '''
    event_desc = eval(event.get_event_description())
    if event_desc['post_type'] == "notice" and \
        event_desc['notice_type'] == "notify" and \
        event_desc['sub_type'] == "poke" and \
        str(event_desc['group_id']) in GRP_IDS:
        return True
    else:
        return False

# various responser detectors with different rules
m_responser = on("message", rule.keyword("骂") & rule.to_me(), priority=3, block=True)
eating_responser = on("message", rule.keyword("吃掉") & rule.to_me(), priority=4)
gachi_responser = on("message", rule.keyword("gachi") & rule.to_me(), priority=4)
oyasumi_responser = on("message", rule.keyword("晚安") & rule.to_me(), priority=4)
dog_responser = on("message", rule.keyword("遛狗") & rule.to_me(), priority=4)
kuakua_responser = on("message", rule.keyword("可爱") & rule.to_me(), priority=4)
suki_responser = on("message", rule.keyword("喜欢") & rule.to_me(), priority=4)
hiccup_responser = on("message", rule.keyword("打嗝") & rule.to_me(), priority=4)
sq_grass_responser = on_regex(r"^挤挤草草$", flags=re.UNICODE, rule=rule.to_me(), priority=4)
instru_responser = on_regex(r"肆乐器", flags=re.UNICODE, rule=rule.to_me(), priority=4)
box_responser = on("message", rule.keyword("盒皇语录") & rule.to_me(), priority=4)
ohayo_responser = on_regex(r"^(早上好|早安|早)$", flags=re.UNICODE, rule=rule.to_me(), priority=4)
nya_responser = on_regex(r"^(喵*)$", flags=re.UNICODE, rule=rule.to_me(), priority=4)
self_recog_responser = on_regex(r"(?!.*是你的.*狗).*我.*是你的.{1,}", flags=re.UNICODE, rule=rule.to_me(), priority=4)
patpat_responser = on("notice", rule.Rule(patpat_rule) & rule.to_me(), priority=5)
call_responser = on("message", rule.to_me(), priority=5)

async def check_friends(qid: str, bot: Bot):
    fri_list = await bot.call_api("get_friend_list")
    for f in fri_list:
        if str(f['user_id']) == qid: 
            return True

    return False

async def send_voice(bot: Bot, event: Event, cmd: str):
    event_name = event.get_event_name().split(".")
    print(event_name)
    if event_name[1] == "group": 
        _, gid, uid = event.get_session_id().split("_")
        print(gid, uid)
        await bot.call_api("send_msg", message=cmd, group_id=gid)
    elif event_name[1] == "private":
        uid = event.get_session_id()
        if await check_friends(uid, bot):
            await bot.call_api("send_msg", message=cmd, user_id=uid)
        else:
            await bot.call_api("send_msg", message="我不认识你，你谁啊！", user_id=uid)
    elif event_name[0] == "notice" and event_name[-1] == "poke":
        event_desc = eval(event.get_event_description())
        if event_desc["group_id"] is not None:
            await bot.call_api("send_msg", message=cmd, group_id=event_desc["group_id"])

@m_responser.handle()
async def m_send_response(bot: Bot, event: Event):
    vocal_path = vocal_lib_path + "dirt_words"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path+f"/{wave_id}.wav", "record")
    await send_voice(bot, event, cmd)

@eating_responser.handle()
async def eating_send_response(bot: Bot, event: Event):
    vocal_path = vocal_lib_path + "eating"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path+f"/{wave_id}.wav", "record")
    await send_voice(bot, event, cmd)

@gachi_responser.handle()
async def gachi_send_response(bot: Bot, event: Event):
    global GACHI_GRP_ID
    vocal_path = vocal_lib_path + "gachi"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path + f"/{wave_id}.wav", "record")
    sender = event.get_session_id().split("_")
    gid = sender[1] if len(sender) > 1 else '0'
    uid = sender[-1]
    # only send gachi response in the admiral group
    if len(sender) > 1:
        for permitted_g_ids in GACHI_GRP_ID:
            if gid == permitted_g_ids:
                await send_voice(bot, event, cmd)
                break

@nya_responser.handle()
async def nya_send_response(bot: Bot, event: Event):
    vocal_path = vocal_lib_path + "nya"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path + f"/{wave_id}.wav", "record")
    await send_voice(bot, event, cmd)


@oyasumi_responser.handle()
async def oyasumi_send_response(bot: Bot, event: Event):
    vocal_path = vocal_lib_path + "sleeping"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path + f"/{wave_id}.wav", "record")
    await send_voice(bot, event, cmd)

@dog_responser.handle()
async def dog_send_response(bot: Bot, event: Event):
    vocal_path = vocal_lib_path + "puppy"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path + f"/{wave_id}.wav", "record")
    await send_voice(bot, event, cmd)

@sq_grass_responser.handle()
async def sq_grass_send_response(bot: Bot, event: Event):
    cmd = await encode_f_to_cq(vocal_lib_path + "sq_grass.wav", "record")
    await send_voice(bot, event, cmd)

@box_responser.handle()
async def box_send_response(bot: Bot, event: Event):
    vocal_path = vocal_lib_path + "essential_box"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path + f"/{wave_id}.wav", "record")
    await send_voice(bot, event, cmd)

@patpat_responser.handle()
async def patpat_send_response(bot: Bot, event: Event):
    vocal_path = vocal_lib_path + "achou"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path + f"/{wave_id}.wav", "record")
    await send_voice(bot, event, cmd)

@instru_responser.handle()
async def instru_send_response(bot: Bot, event: Event):
    vocal_path = vocal_lib_path + "instru"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path + f"/{wave_id}.wav", "record")
    await send_voice(bot, event, cmd)

@kuakua_responser.handle()
async def kuakua_send_response(bot: Bot, event: Event):
    cmd = await encode_f_to_cq(vocal_lib_path + "nya.wav", "record")
    await send_voice(bot, event, cmd)

@hiccup_responser.handle()
async def hiccup_send_response(bot: Bot, event: Event):
    cmd = await encode_f_to_cq(vocal_lib_path + "hiccup.wav", "record")
    await send_voice(bot, event, cmd)

@suki_responser.handle()
async def suki_send_response(bot: Bot, event: Event):
    cmd = await encode_f_to_cq(vocal_lib_path + "suki.wav", "record")
    await send_voice(bot, event, cmd)

@self_recog_responser.handle()
async def self_recog_response(bot: Bot, event: Event):
    cmd = await encode_f_to_cq(vocal_lib_path + "arent_you_dog.wav", "record")
    await send_voice(bot, event, cmd)

@ohayo_responser.handle()
async def ohayo_response(bot: Bot, event: Event):
    vocal_path = vocal_lib_path + "morning"
    num_wavs = len([name for name in os.listdir(vocal_path)])
    wave_id = random.randint(1, num_wavs)
    cmd = await encode_f_to_cq(vocal_path + f"/{wave_id}.wav", "record")
    await send_voice(bot, event, cmd)

@call_responser.handle()
async def call_send_response(bot: Bot, event: Event):
    if_resp = random.randint(0,1)
    desc = event.get_event_description()
    print(desc)
    event_name = event.get_event_name().split(".")
    if "\"\"" in desc and event_name[1] == "group":
        print("ready to shuffle if response")
        if if_resp == 1:  
            vocal_path = vocal_lib_path + "why_call_me"
            num_wavs = len([name for name in os.listdir(vocal_path)])
            wave_id = random.randint(1, num_wavs)
            cmd = await encode_f_to_cq(vocal_path + f"/{wave_id}.wav", "record")
            await send_voice(bot, event, cmd)
