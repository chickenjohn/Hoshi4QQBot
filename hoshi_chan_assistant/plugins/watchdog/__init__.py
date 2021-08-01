from nonebot import on_command
from nonebot import rule
from nonebot.plugin import on
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import utils
from nonebot.config import Config

import os, os.path
from bilibili_api import live
import asyncio

GRP_IDS = [Config(".env").cap_grp_id]
ADMIN_ACC = Config(".env").admin_id

async def add_group_checker(bot: Bot, event: Event, state: T_State) -> bool:
    event_name = event.get_event_name()

    if event_name == "request.group.add":
        sess_ids = event.get_session_id()
        event_desc = eval(event.get_event_description())
        group_id = event_desc['group_id']
        if group_id in GRP_IDS:
            return True
    
    return False

# async def group_member_incr_rule(bot: Bot, event: Event, state: T_State) -> bool:
#     event_name = event.get_event_name()
#     event_desc = eval(event.get_event_description())
#     group_id = event_desc['group_id']

    
#     if event_name == "notice.group_increase.approve" and \
#             group_id == GRP_ID:
#         return True
#     else:
#         return False

group_add_resp = on("request", rule.Rule(add_group_checker), priority=1)
# group_mem_incr = on("notice", rule.Rule(group_member_incr_rule), priority=2)

def parse_captain_list(captain_list: dict):
    partial_captain_list = []
    for cap in captain_list['list']:
        partial_captain_list.append((cap['username'], cap['uid']))

    return partial_captain_list

async def check_captains(search_id):
    room = live.LiveRoom(room_display_id=924973)
    captain_list = await room.get_dahanghai(page=1)
    pg_size = captain_list['info']['page']
    captain_list_parsed = parse_captain_list(captain_list)

    for i in list(range(pg_size-1)):
        captain_list = await room.get_dahanghai(page=i+2)
        curr_cap_list_parsed = parse_captain_list(captain_list)
        captain_list_parsed += curr_cap_list_parsed

    for i in captain_list_parsed:
        if i[0] == search_id: return True
    
    return False

async def check_if_cap_exists(search_id: str, bot: Bot, group_id):
    grp_members = await bot.call_api("get_group_member_list", group_id=group_id)
    for mem in grp_members:
        if mem['card'] == search_id:
            return True

    return False

@group_add_resp.handle()
async def first_receive(bot: Bot, event: Event):
    event_desc = eval(event.get_event_description())
    ans = event_desc['comment'].split("\n")[-1]
    user_id = event_desc['user_id']
    group_id = event_desc['group_id']
    ans = ans[3:]
    print("group add request answer: ", ans)

    search_id_res = await check_captains(ans)
    if search_id_res:
        if_exists = await check_if_cap_exists(ans, bot, group_id)
        print("search cap res: ", if_exists)
        if not if_exists:
            await bot.call_api("set_group_add_request", flag=event_desc['flag'], sub_type=event_desc['sub_type'], approve="true")
        else:
            for admin in ADMIN_ACC:
                await bot.call_api("send_msg", message="加群验证失败，等待管理员手动同意（有冒用已存舰长id嫌疑）", user_id=admin)
    else:
        for admin in ADMIN_ACC:
            await bot.call_api("send_msg", message="加群验证失败，等待管理员手动同意...", user_id=admin)

# @group_add_resp.handle()
# async def post_add_process(bot: Bot, event: Event):
#     event_desc = eval(event.get_event_description())
#     ans = event_desc['comment'].split("\n")[-1]
#     user_id = event_desc['user_id']
#     ans = ans[3:]
#     print("group add request answer: ", ans)
#     flag = event_desc['flag']
#     sub_type = event_desc['sub_type']

#     if_exists = await check_if_cap_exists(ans, bot)
#     if if_exists:
#         await bot.call_api("set_group_card", group_id=GRP_ID, user_id=user_id, card=ans)
