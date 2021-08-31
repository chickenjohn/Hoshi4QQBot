from nonebot import on_command
from nonebot import rule
from nonebot.plugin import on
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import utils
from nonebot.config import Config

import csv
import os
import datetime
import copy

SCHE_FILE_PATH = "data/schedule.csv"

def get_sche_today():
    try:
        with open(SCHE_FILE_PATH, newline='') as sche_dat:
            sche_reader = csv.DictReader(sche_dat, delimiter=',')
            for row in sche_reader:
                curr_year = datetime.datetime.now().date()
                curr_year = curr_year.strftime('%y')
                curr_date = datetime.datetime.strptime(row['date']+f'/{curr_year}', '%m/%d/%y')
                if curr_date.date() == datetime.datetime.today().date():
                    return row['start_time'], row['end_time'], row['content']
    except EnvironmentError:
        print(f"IO error. Non-existing file {SCHE_FILE_PATH}?")

    return None, None

def get_sche():
    res = None
    try:
        with open(SCHE_FILE_PATH, newline='') as sche_dat:
            sche_reader = csv.DictReader(sche_dat, delimiter=',')
            res = [copy.deepcopy(row) for row in sche_reader]
    except EnvironmentError:
        print(f"IO error. Non-existing file {SCHE_FILE_PATH}?")

    return res

ask_schedule_responser = on("message", rule.keyword("播吗") & rule.to_me(), priority=4)
ask_entire_schedule_responser = on("message", rule.keyword("排班表") & rule.to_me(), priority=4)

@ask_schedule_responser.handle()
async def ask_schedule_resp(bot: Bot, event: Event):
    start_time, end_time, content = get_sche_today()
    cmd = ''
    if start_time is None or end_time is None:
        cmd = '关于这周的排班，小小肆还什么都不知道！QAQ'
    elif start_time == 'x' or end_time == 'x':
        cmd = '烦肆了！今天不播！'
    elif start_time == 'b' or end_time == 'b':
        cmd = '病没好，播个p！TuT'
    else:
        cmd = f'今天预计的排班：\n' + \
                f'{start_time}至{end_time}-{content}'

    await bot.send(event=event, message=cmd)

@ask_entire_schedule_responser.handle()
async def ask_entire_sche_resp(bot: Bot, event: Event):
    sche_list = get_sche()
    cmd = ''
    if sche_list is None:
        cmd = '关于这周的排班，小小肆还什么都不知道！QAQ'
    else:
        cmd = '本周：\n'
        for d in sche_list:
            date, start, end = d['date'], d['start_time'], d['end_time']
            content = d['content']
            cmd += f'{date}：'
            if start == 'x' or end == 'x':
                cmd += '不播\n'
            elif start == 'b' or end == 'b':
                cmd += '病没好，播个p！TuT\n'
            else:
                cmd += f'{start} - {end}：{content}\n'

    print(cmd)
    await bot.send(event=event, message=cmd)