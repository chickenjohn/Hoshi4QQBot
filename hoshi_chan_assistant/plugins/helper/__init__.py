from nonebot import on_command
from nonebot import rule
from nonebot.plugin import on
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import utils
from nonebot.config import Config
from ..libs.file_reader import encode_f_to_cq

GRP_IDS = [str(Config(".env").cap_grp_id)]

async def group_member_incr_rule(bot: Bot, event: Event, state: T_State) -> bool:
    event_name = event.get_event_name()
    event_desc = eval(event.get_event_description())
    if event_name == "notice.group_increase.approve":
        for grp in GRP_IDS:
            if str(event_desc["group_id"]) == grp:
                return True
    else:
        return False

    return False

async def check_if_admin(event: Event) -> bool:
    event_name = event.get_event_name()
    admin_names = Config(".env").admin_id
    if event_name == "message.private.friend":
        sess_id = event.get_session_id()
        
        for admin_id in admin_names:
            if str(admin_id) == sess_id:
                return True

    return False

async def send_message(bot: Bot, event: Event, cmd: str):
    event_name = event.get_event_name().split(".")
    if "group" in event_name[1]: 
        if event_name[-1] == "normal":
            _, gid, uid = tuple(event.get_session_id().split("_"))
            print(gid)
            await bot.call_api("send_msg", message=cmd, group_id=gid)
        else:
            event_desc = eval(event.get_event_description())
            gid = event_desc['group_id']
            print(gid)
            await bot.call_api("send_msg", message=cmd, group_id=gid)
    elif event_name[1] == "private":
        uid = event.get_session_id()
        await bot.call_api("send_msg", message=cmd, user_id=uid)

group_member_incr_resp = on("notice", rule.Rule(group_member_incr_rule), priority=3)
hoshi_helper_responser = on("message", rule.keyword("帮助") & rule.to_me(), priority=3, block=True)
record_responser = on("message", rule.keyword("肆指路") & rule.to_me(), priority=5)
intro_responser = on("message", rule.keyword("自我介绍") & rule.to_me(), priority=5)

@record_responser.handle()
async def records_list_resp(bot: Bot, event: Event):
    lines = "肆录播：http://t.hk.uy/w5V\n" + \
            "爱发电：http://afdian.net/@hoshi4\n" + \
            "提问箱：http://t.hk.uy/8TG\n" + \
            "萌娘百科：http://t.hk.uy/8TA\n" + \
            "水友歌会：http://t.hk.uy/w5C\n" + \
            "满月回：http://t.hk.uy/25N\n" + \
            "近期连麦：http://t.hk.uy/25N\n" + \
            "歌曲切切：http://t.hk.uy/w5H\n" + \
            "日常切切：http://t.hk.uy/w5Q"
    await bot.send(event=event, message=lines)

@group_member_incr_resp.handle()
async def welcome_msg(bot: Bot, event: Event):
    event_desc = eval(event.get_event_description())
    user_id = event_desc['user_id']
    welcome_lines = "欢迎来到船火人的群，我是群助手小小肆！\n" + \
                    "在群里您可以用 @小小肆 附加命令 的方式使用我！\n" + \
                    "为了不打扰群里的大家，您可以私戳我并发送 帮助 来获取一份详细的命令单\n" + \
                    "特别提醒：请尽快将自己的群备注改为B站用户名，不然你的用户名会被坏人盗用进群的！\n" + \
                    f"祝你在群里玩的开心！[CQ:at,qq={user_id}]"
    print("incr sending msg")
    await send_message(bot, event, welcome_lines)

@intro_responser.handle()
async def intro_welcome_msg(bot: Bot, event: Event):
    welcome_lines = "大家好，我是群助手小小肆！\n" + \
                    "在群里您可以用 @小小肆 附加命令 的方式使用我！\n" + \
                    "同时，我还会推送肆宝开播和动态的更新消息~ \n" + \
                    "如果你励志做肆宝的单推人，也可以联系鸡酱将你加入我的关注列表哦！\n" + \
                    "为了不打扰群里的大家，您可以私戳我并发送 帮助 来获取一份详细的命令单\n" + \
                    "特别提醒：请尽快将自己的群备注改为B站用户名，不然你的用户名会被坏人盗用进群的！\n" + \
                    "祝你在群里玩的开心！"
    await send_message(bot, event, welcome_lines)

@hoshi_helper_responser.handle()
async def send_first_help_response(bot: Bot, event: Event):
    helper_img_path = Config(".env").proj_path
    is_admin = await check_if_admin(event)
    if is_admin:
        cmd = await encode_f_to_cq(helper_img_path+"special_help.png", "image", "cache=0")
    else:
        cmd = await encode_f_to_cq(helper_img_path+"help.png", "image", "cache=0")

    await send_message(bot, event, cmd)