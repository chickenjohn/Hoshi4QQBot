import logging
from nonebot import on_command
from nonebot import rule
from nonebot.plugin import on, on_keyword, on_regex
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import utils
from nonebot.config import Config
from ..libs.customized_rules import group_member_incr_rule

import os, os.path
import aiosqlite as sql
import re
import datetime as dt


CHKIN_DAT_PATH = "data/checkin_dat.db"
GRP_ID = str(Config(".env").cap_grp_id)
TEST_GRP_ID = str(Config(".env").grp_id)

async def build_checkin_list(bot: Bot, group_id):
    print("开始刷新积分列表")
    db_conn = await sql.connect(CHKIN_DAT_PATH)
    grp_members = await bot.call_api("get_group_member_list", group_id=group_id)
    for mem in grp_members:
        db_cursor = await db_conn.execute("SELECT qid FROM checkin_table WHERE qid = ?;", (str(mem['user_id']), ))
        res = await db_cursor.fetchone()
        if res is None:
            sql_cmd = "INSERT INTO checkin_table (qid, credit, last_checkin, con_checkin_days, curr_con_checkin_days, bid, bililive_checkin, bililive_nticket) VALUES(:qid, :credit, :last_checkin, :con_checkin_days, :curr_con_checkin_days, :bid, :bililive_checkin, :bililive_nticket);"
            insert_vals = {"qid": str(mem['user_id']), "credit": 0, "last_checkin": None, "con_checkin_days":0, "curr_con_checkin_days":0, "bid": None, "bililive_checkin": None, "bililive_nticket": None}
            db_cursor = await db_conn.execute(sql_cmd, insert_vals)

    await db_conn.commit()
    await db_cursor.close()
    await db_conn.close()
    print("刷新积分列表成功")

def check_if_admin(event: Event) -> bool:
    event_name = event.get_event_name()
    admin_names = Config(".env").admin_id
    if event_name == "message.private.friend":
        sess_id = event.get_session_id()
        
        for admin_id in admin_names:
            if str(admin_id) == sess_id:
                return True

    return False

async def update_checkin_time_dist_mn(checkin_time: dt.datetime, qid: str):
    '''
    checkin function distinguishing morning and night.
    DEPRECATED. DO NOT USE THIS ONE!
    '''
    time_fmt = "%Y-%m-%d-%H-%M-%S"
    morning_region_start, morning_region_end = dt.time(6, 0), dt.time(12, 0)
    night_region_start, night_region_end = dt.time(21, 0), dt.time(4, 0)
    update_cmd = '''UPDATE checkin_table 
                    SET credit = ?, 
                        last_morn_checkin_time = ?,
                        last_night_checkin_time = ?,
                        checkin_days = ?, 
                        con_checkin_days = ?,
                        curr_con_checkin_days = ?
                    WHERE qid = ?;'''
    search_cmd = "SELECT * FROM checkin_table WHERE qid = ?;"

    # check if morning checkin or night checkin
    type = 'none'
    if morning_region_start <= checkin_time.time() <= morning_region_end: 
        type = "morning"
    elif (night_region_start <= checkin_time.time() <= dt.time(23, 59)) or \
            (dt.time(0, 0) <= checkin_time.time() <= night_region_end):
        type = "night"

    db_conn = await sql.connect(CHKIN_DAT_PATH)
    db_cursor = await db_conn.execute(search_cmd, (qid,))
    res = await db_cursor.fetchone()

    if not res is None:
        checkin_time_str = checkin_time.strftime(time_fmt)
        logging.info("detected checkin time: ", checkin_time_str)
        res_qid, res_credit, res_last_morn, res_last_night, \
            res_checkin_days, res_con_checkin_days, res_curr_con_checkin_days, _, _, _ = res
        to_update = False
        try:
            res_last_morn_time = dt.datetime.strptime(res_last_morn, time_fmt)
        except:
            res_last_morn_time = None
            logging.warn("Invalid last morning time")

        try:
            res_last_night_time = dt.datetime.strptime(res_last_night, time_fmt)
        except:
            res_last_night_time = None
            logging.warn("Invalid last night time")
        
        if type == 'morning':
            logging.info("morning checking")
            if res_last_morn is None:
                res_last_morn = checkin_time_str
                res_credit += 1
                to_update = True
            else:
                delta = (checkin_time.date() - res_last_morn_time.date()).days
                if delta > 0:
                    res_last_morn = checkin_time_str
                    res_credit += 1
                    to_update = True

                if delta > 1:
                    res_curr_con_checkin_days = 0
                    to_update = True
                    
        elif type == 'night':
            logging.info("night checkin")
            if res_last_night is None:
                res_last_night = checkin_time_str
                res_credit += 1
                to_update = True
                if res_last_morn_time is not None:
                    morn2night_delta = (checkin_time.date() - res_last_morn_time.date()).days
                    if (morn2night_delta == 0 and (night_region_start <= checkin_time.time() <= dt.time(23,59))) or \
                        (morn2night_delta == 1 and (dt.time(0, 0) <= checkin_time.time() <= night_region_end)) :
                        res_checkin_days += 1
                        res_curr_con_checkin_days = 1
                        res_con_checkin_days = 1
            else:
                print("night detect 1")
                night2night_delta = (checkin_time.date() - res_last_night_time.date()).days
                print("night2night: ", night2night_delta)
                print("res last night: ", res_last_night_time.time() <= dt.time(23, 59))
                print("res this night: ", checkin_time.time() >= dt.time(0, 0))
                if (not (night2night_delta == 1 and (res_last_night_time.time() <= dt.time(23, 59)) and (night_region_end >= checkin_time.time() >= dt.time(0, 0)))) \
                    and (night2night_delta > 0) :
                    print("night detect 2")
                    res_credit += 1
                    to_update = True
                    res_last_night = checkin_time_str
                    if res_last_morn_time is not None:
                        morn2night_delta = (checkin_time.date() - res_last_morn_time.date()).days
                        if (morn2night_delta == 0 and (night_region_start <= checkin_time.time() <= dt.time(23,59))) or \
                            (morn2night_delta == 1 and (dt.time(0, 0) <= checkin_time.time() <= night_region_end)) :
                            res_checkin_days += 1

                            is_cur_night_next_day = (night2night_delta == 2 and (res_last_night_time.time() <= dt.time(23, 59)) and (checkin_time.time() >= dt.time(0, 0)))
                            if (night2night_delta == 1) or is_cur_night_next_day: 
                                res_curr_con_checkin_days += 1
                                if res_curr_con_checkin_days > res_con_checkin_days:
                                    res_con_checkin_days = res_curr_con_checkin_days
                            else:
                                res_curr_con_checkin_days = 1
                        else:
                            res_curr_con_checkin_days = 0

        if to_update:
            await db_conn.execute(update_cmd, (res_credit, res_last_morn, res_last_night, \
                                                    res_checkin_days, res_con_checkin_days, res_curr_con_checkin_days, \
                                                    qid))
            await db_conn.commit()

    else:
        print("record not found!")

    await db_conn.close()
    return to_update

async def update_checkin_time(checkin_time: dt.datetime, qid: str):
    '''
    update checkin time and related data, one time per day
    '''
    time_fmt = "%Y-%m-%d-%H-%M-%S"
    update_cmd = '''UPDATE checkin_table 
                    SET credit = ?, 
                        last_checkin = ?,
                        con_checkin_days = ?,
                        curr_con_checkin_days = ?
                    WHERE qid = ?;'''
    search_cmd = "SELECT qid, credit, last_checkin, con_checkin_days, curr_con_checkin_days FROM checkin_table WHERE qid = ?;"

    db_conn = await sql.connect(CHKIN_DAT_PATH)
    db_cursor = await db_conn.execute(search_cmd, (qid,))
    res = await db_cursor.fetchone()

    to_update = False
    if not res is None:
        checkin_time_str = checkin_time.strftime(time_fmt)
        logging.info("detected checkin time: ", checkin_time_str)
        qid, res_credit, res_last_checkin_str, \
            res_con_checkin_days, res_curr_con_checkin_days = res

        try:
            res_last_checkin = dt.datetime.strptime(res_last_checkin_str, time_fmt)
        except:
            res_last_checkin = None
            logging.warn("Invalid last checkin time")
        
        if res_last_checkin is None:
            to_update = True
            res_last_checkin_str = checkin_time_str
            res_con_checkin_days = 1
            res_curr_con_checkin_days = 1
            res_credit = 1
        else:
            date_delta = (checkin_time.date() - res_last_checkin.date()).days
            if date_delta > 0:
                to_update = True
                res_last_checkin_str = checkin_time_str
                res_credit += 1
                if date_delta == 1:
                    res_curr_con_checkin_days += 1
                    if res_curr_con_checkin_days > res_con_checkin_days:
                        res_con_checkin_days = res_curr_con_checkin_days
                elif date_delta > 1:
                    res_curr_con_checkin_days = 1

    
        if to_update:
            await db_conn.execute(update_cmd, (res_credit, res_last_checkin_str, \
                                                    res_con_checkin_days, res_curr_con_checkin_days, qid))
            await db_conn.commit()
    else:
        logging.warn("record not found!")
    
    await db_conn.close()
    return to_update

async def check_credits(qid):
    search_cmd = "SELECT credit, con_checkin_days, curr_con_checkin_days FROM checkin_table WHERE qid = ?;"
    db_conn = await sql.connect(CHKIN_DAT_PATH)
    db_cursor = await db_conn.execute(search_cmd, (qid,))
    res = await db_cursor.fetchone()

    await db_cursor.close()
    await db_conn.close()
    return res

build_checkin_list_resp = on_command("刷新积分列表", rule=rule.to_me(), priority=3, block=True)
checkin_resp = on_regex(r"^(早上好|早安|早|脚向好|脚上好|晚上好|晚安)$", flags=re.UNICODE, priority=4)
check_credit_resp = on_regex(r"^查积分$", flags=re.UNICODE, rule=rule.to_me(), priority=4)
connect_bili_id_resp = on_regex(r"登记BID", flags=re.UNICODE, rule=rule.to_me(), priority=4)
group_member_incr_resp = on("notice", rule.Rule(group_member_incr_rule), priority=3)

@group_member_incr_resp.handle()
async def group_member_incr_refresh_list(bot: Bot, event: Event):
    print("开始刷新")
    await build_checkin_list(bot, GRP_ID)

@build_checkin_list_resp.handle()
async def build_checkin_list_reponse(bot: Bot, event: Event):
    print("开始刷新")
    # is_admin = check_if_admin(event)
    # print(f"admin check: {is_admin}")
    # if is_admin:

    await build_checkin_list(bot, GRP_ID)

@checkin_resp.handle()
async def morning_checkin_prod(bot: Bot, event: Event):
    # check if the first date of a month, if yes, freeze for 10 mins for 
    # database update
    def check_if_maintainess(curr_time: dt.datetime):
        if curr_time.day == 1 and (dt.time(0,0) <= curr_time.time() < dt.time(0, 10)):
            return True
        else:
            return False

    curr_date = dt.datetime.now()
    event_name = event.get_event_name().split(".")
    if event_name[1] == "group" and event_name[2] == "normal":
        sender = event.get_session_id().split("_")
        gid = str(sender[1])
        uid = str(sender[-1])
        if gid == GRP_ID or gid == TEST_GRP_ID:
            if check_if_maintainess(curr_date):
                await bot.call_api("send_msg", message="上月签到数据结算中，请0点10分后签到！", group_id=gid)
            else:
                res = await update_checkin_time(curr_date, uid)
                if res:
                    cmd = str(uid) + ": 你的打卡成功啦！"
                    await bot.call_api("send_msg", message=cmd, group_id=gid)

@check_credit_resp.handle()
async def check_credit_response(bot: Bot, event: Event):
    event_name = event.get_event_name().split(".")
    if event_name[1] == "group" and event_name[2] == "normal":
        sender = event.get_session_id().split("_")
        gid = sender[1]
        uid = str(sender[-1])
        if gid == GRP_ID or gid == TEST_GRP_ID:
            res = await check_credits(uid)
            if res is not None:
                cred, combo_days, curr_combo_days = res
                cmd = f"{uid}：\n当前积分：{cred}\n最大连续签到：{combo_days}天\n当前连续签到：{curr_combo_days}天"
                await bot.call_api("send_msg", message=cmd, group_id=gid)

@connect_bili_id_resp.handle()
async def connect_bid_response(bot: Bot, event: Event):
    event_name = event.get_session_id().split("_")
    bid_str = (str(event.get_message()).split(" "))[-1]
    sender_qid = event_name[-1]
    connect_id_response = ""
    if sender_qid.isdecimal() and bid_str.isdecimal():
        update_cmd = '''UPDATE checkin_table 
                            SET bid = ?
                        WHERE qid = ?;'''
        search_cmd = "SELECT qid FROM checkin_table WHERE qid = ?;"
        db_conn = await sql.connect(CHKIN_DAT_PATH)
        db_cursor = await db_conn.execute(search_cmd, (sender_qid,))
        res = await db_cursor.fetchone()
        if res is None:
            connect_id_response = "没找到你的记录！请联系管理员处理"
        else:
            await db_conn.execute(update_cmd, (bid_str, sender_qid))
            await db_conn.commit()
            connect_id_response = f"已将QQ号{sender_qid}连接至b站uid{bid_str}"

        await db_cursor.close()
        await db_conn.close()

    else:
        connect_id_response = "不对劲的b站uid！"

    print(event_name)
    print(connect_id_response)
    if len(event_name) > 1 and event_name[0] == "group":
        await bot.call_api("send_msg", message=connect_id_response, group_id=event_name[1])
    elif len(event_name) == 1:
        await bot.call_api("send_msg", message=connect_id_response, user_id=sender_qid)


