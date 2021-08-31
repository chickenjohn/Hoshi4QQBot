from logging import Manager
from nonebot import on_command
from nonebot import rule
from nonebot.plugin import on
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import utils
from nonebot.config import Config

import os, os.path
import aiosqlite as sql
from itertools import product

def check_if_admin(event: Event) -> bool:
    event_name = event.get_event_name()
    admin_names = Config(".env").admin_id
    grp_ids = [Config(".env").cap_grp_id, Config(".env").adm_grp_id, Config(".env").grp_id]
    if event_name == "message.private.friend":
        sess_id = event.get_session_id()
        
        for admin_id in admin_names:
            if str(admin_id) == sess_id:
                return True
    elif event_name == "message.group.normal":
        _, gid, uid = event.get_session_id().split("_")
        for grp_id, admin_id in product(grp_ids, admin_names):
            if str(grp_id) == gid and str(admin_id) == uid:
                return True

    return False

add_music_resp = on("message", rule.keyword("加歌") & rule.to_me(), priority=1, block=True)
del_music_resp = on("message", rule.keyword("删歌") & rule.to_me(), priority=1, block=True)
search_resp = on("message", rule.keyword("找歌") & rule.to_me(), priority=2)
check_music_resp = on("message", rule.keyword("查歌名") & rule.to_me(), priority=2)
random_resp = on("message", rule.keyword("随机一首") & rule.to_me(), priority=2)

def parse_search_keys(arg_list: list) -> dict:
    cmd_lut = {"歌手": "artist", "歌名字数": "name_size", "语言": "name_lang"}
    res = {}
    for arg in arg_list:
        search_args = arg.split("-")
        if len(search_args) == 2:
            state_key = cmd_lut.get(search_args[0], None)
            if state_key is None:
                return {}
            else:
                if type(search_args[1]) is str:
                    res[state_key] = search_args[1].replace("&amp;", "&")
                else:
                    res[state_key] = search_args[1]
        else:
            return {}

    return res

def parse_add_music_keys(arg_list: list) -> dict:
    cmd_lut = {"歌名": "name", "歌手": "artist", "语言": "name_lang", "歌名字数": "name_size"}
    res = {}
    finished_keys = 0
    for arg in arg_list:
        search_args = arg.split("-")
        print(search_args)
        if len(search_args) == 2:
            state_key = cmd_lut.get(search_args[0], None)
            if state_key is None:
                return {}
            else:
                if type(search_args[1]) is str:
                    res[state_key] = search_args[1].replace("&amp;", "&")
                else:
                    res[state_key] = search_args[1]
                finished_keys += 1
        else:
            return {}

    if res.get('name_size', 0) == 0:
        res['name_size'] = len(res['name'])
        finished_keys += 1

    if finished_keys < 4:
        return {}
    
    return res

async def search_db_by_search_args(search_args: dict) -> list:
    sql_conn = await sql.connect("music_list.db")
    sql_cmd = "SELECT name, artist FROM music_list WHERE"
    for i, (k, v) in enumerate(search_args.items()):
        if k == "name_size":
            sql_cmd += f" {k}=:name_size"
        else:
            sql_cmd += f" {k} LIKE :{k}"
            search_args[k] = "%" + search_args[k] + "%"

        if (i+1) < len(search_args):
            sql_cmd += " AND"
        elif (i+1) == len(search_args):
            sql_cmd += " ORDER BY name_size ASC;"

    print(sql_cmd)

    sql_cursor = await sql_conn.execute(sql_cmd, search_args)
    rows = await sql_cursor.fetchall()

    await sql_cursor.close()
    await sql_conn.close()
    return rows

async def add_music_by_keys(keys: dict):
    sql_conn = await sql.connect("music_list.db")
    sql_cmd_insert = "INSERT INTO music_list (name, name_size, artist, name_lang) VALUES(:name, :name_size, :artist, :name_lang);"

    cursor = await sql_conn.execute(sql_cmd_insert, keys)
    await sql_conn.commit()
    await cursor.close()
    await sql_conn.close()

async def del_music_by_id(id: int):
    sql_conn = await sql.connect("music_list.db")
    # get music name
    sql_cmd = f"SELECT name, artist FROM music_list WHERE id={id}"
    cursor = await sql_conn.execute(sql_cmd)
    rows = await cursor.fetchall()
    res = "删除了"
    if len(rows) > 0:    
        for name, art in rows:
            res += f" {name}-{art}"
    else:
        res = "没找到要删除的歌！"

    sql_cmd = f"DELETE FROM music_list WHERE id={id};"
    try:
        cursor = await sql_conn.execute(sql_cmd)
    except Exception as e:
        res = str(e)

    await sql_conn.commit()
    await cursor.close()
    await sql_conn.close()
    
    return res

@del_music_resp.handle()
async def del_music_first_receive(bot: Bot, event: Event, state: T_State):
    is_admin = check_if_admin(event)
    if is_admin:
        args = str(event.get_message())
        args_list = args.split(" ")
        if len(args_list) > 1:
            music_id = int(args_list[-1])
            res = await del_music_by_id(music_id)
            cmd = res
            await del_music_resp.finish(cmd)
        else:
            cmd = "删歌必须提供歌曲id，比如：\n" + \
                "删歌 44"
            await del_music_resp.finish(cmd)
    else:
        cmd = "你不是管理员，不许兜兜删歌！"
        await add_music_resp.finish(cmd)


@add_music_resp.handle()
async def add_music_first_receive(bot: Bot, event: Event, state: T_State):
    is_admin = check_if_admin(event)
    if is_admin:
        args = str(event.get_message())
        args_list = args.split("#")
        if len(args_list) > 1:
            parsed_add_music_keys = parse_add_music_keys(args_list[1:])
            if len(parsed_add_music_keys) > 0:
                await add_music_by_keys(parsed_add_music_keys)
                cmd = "新歌添加成功！小火又学会新歌啦，真厉害！"
                await add_music_resp.finish(cmd)
            else:
                cmd = "检查到了无效的新歌信息！新歌信息必须包含：歌名 歌手 语言\n" + \
                        "有笨蛋！"
                await add_music_resp.finish(cmd)
        else:
            cmd = "请接着输入新歌信息，比如：\n" + \
                "歌名-shower#歌手-都心线#语言-中"
            await bot.send(message=cmd, event=event)
    else:
        cmd = "你不是管理员，不许兜兜加歌！"
        await add_music_resp.finish(cmd)
    
@add_music_resp.receive()
async def add_music_second_receive(bot: Bot, event: Event, state: T_State):
    is_admin = check_if_admin(event)
    if is_admin:
        sql_keys = state.get("sql_keys", None)
        if sql_keys is None:
            args = str(event.get_message())
            args_list = args.split("#")
            sql_keys = parse_add_music_keys(args_list)
        
        if len(sql_keys) > 0:
            await add_music_by_keys(sql_keys)
            cmd = "新歌添加成功！小火又学会新歌啦，真厉害！"
            await bot.send(message=cmd, event=event)
        else:
            cmd = "检查到了无效的新歌信息！新歌信息必须包含：歌名 歌手 语言\n" + \
                    "有笨蛋！"
            await add_music_resp.finish(cmd)

    else:
        cmd = "你不是管理员，不许兜兜加歌！"
        await add_music_resp.finish(cmd)

@search_resp.handle()
async def search_first_receive(bot: Bot, event: Event, state: T_State):
    # input: /找歌 歌手-歌手名 
    args = str(event.get_message())
    args_list = args.split("#")
    if len(args_list) > 1:
        parsed_search_keys = parse_search_keys(args_list[1:])
        if len(parsed_search_keys) > 0:
            search_res = await search_db_by_search_args(parsed_search_keys)
            cmd = f"找到：\n"
            if len(search_res) > 0:
                for r in search_res:
                    cmd += "{0} - {1}\n".format(r[0], r[1])
            else:
                cmd += "0个类似的火西肆会的歌"

            await search_resp.finish(cmd)
        else:
            cmd = "检查到了无效的搜索项！搜索项仅支持：歌手、歌名字数、语言\n" + \
                    "笨蛋！重新搜索吧！"
            await search_resp.finish(cmd)
    else:
        cmd = "请接着输入一些检索词，比如：\n" + \
                "歌手-火西肆#语言-中"
        await bot.send(message=cmd, event=event) 
    
@search_resp.receive()
async def search_second_receive(bot: Bot, event: Event, state: T_State):
    # input: 歌手-歌手名 
    args = str(event.get_message())
    arg_list = args.split("#")
    parsed_search_keys = parse_search_keys(arg_list)
    if len(parsed_search_keys) > 0:
        search_res = await search_db_by_search_args(parsed_search_keys)
        cmd = f"找到：\n"
        if len(search_res) > 0:
            for r in search_res:
                cmd += "{0} - {1}\n".format(r[0], r[1])
        else:
            cmd += "0个类似的火西肆会的歌"

        await bot.send(message=cmd, event=event)
    else:
        cmd = "检查到了无效的搜索项！搜索项仅支持：歌手、歌名字数、语言\n" + \
                "笨蛋！重新搜索吧！"
        await search_resp.finish(cmd)


@check_music_resp.handle()
async def check_music_first_receive(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    arg_list = args.split(" ")
    if len(arg_list) > 1:    
        if len(arg_list) > 2:
            state['name'] = ' '.join(arg_list[1:])
        else:
            state['name'] = arg_list[-1]
        
        state["name"] = state["name"].replace("&amp;", "&")
        print("prompt from matcher", state['name'])
            
@check_music_resp.got(key="name", prompt="请输入歌名")
async def check_music_handle_name(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if state.get("name", None) is None:
        state["name"] = args.replace("&amp;", "&")
        print("prompt from handler", state["name"])

    sql_conn = await sql.connect("music_list.db")
    sql_cursor = await sql_conn.execute("SELECT id, name, artist FROM music_list WHERE name LIKE :name ORDER BY name_size ASC;", \
             {"name": "%" + state["name"] + "%"})
    rows = await sql_cursor.fetchall()
    
    cmd = f"找到：\n"
    if len(rows) > 0:
        for r in rows:
            cmd += "{0}. {1} - {2}\n".format(r[0], r[1], r[2])
    else:
        cmd += "0个类似的火西肆会的歌"

    event_name = event.get_event_name().split(".")
    if event_name[1] == "group": 
        _, gid, uid = event.get_session_id().split("_")
        await bot.call_api("send_msg", message=cmd, group_id=gid)
    elif event_name[1] == "private":
        uid = event.get_session_id()
        await bot.call_api("send_msg", message=cmd, user_id=uid)

    await sql_cursor.close()
    await sql_conn.close()
    

@random_resp.handle()
async def music_random_choice(bot: Bot, event: Event):
    sql_conn = await sql.connect("music_list.db")

    sql_cursor = await sql_conn.execute("SELECT name, artist FROM music_list ORDER BY RANDOM() LIMIT 1;")
    rows = await sql_cursor.fetchone()
    print(rows)
    event_name = event.get_event_name().split(".")
    cmd = f"不如听听肆宝唱：{rows[0]} - {rows[1]}"
    if event_name[1] == "group": 
        _, gid, uid = event.get_session_id().split("_")
        await bot.call_api("send_msg", message=cmd, group_id=gid)
    elif event_name[1] == "private":
        uid = event.get_session_id()
        await bot.call_api("send_msg", message=cmd, user_id=uid)

    await sql_cursor.close()
    await sql_conn.close()
