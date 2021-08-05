from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.config import Config

async def group_member_incr_rule(bot: Bot, event: Event, state: T_State) -> bool:
    GRP_IDS = [str(Config(".env").cap_grp_id)]
    event_name = event.get_event_name()
    event_desc = eval(event.get_event_description())
    if event_name == "notice.group_increase.approve":
        for grp in GRP_IDS:
            if str(event_desc["group_id"]) == grp:
                return True
    else:
        return False

    return False