from astrbot.api import event
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import requests
import re
import random
from astrbot.api.message_components import Image, At, Plain
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
import json
import os
from datetime import date
from typing import Dict, Optional
from astrbot.api.message_components import Image, At, Plain
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
import aiohttp

@register("钻石插件", " ByDiamond", "Horizon游戏人数获取", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_file = os.path.join(os.path.dirname(__file__), "wife_data.json")
        self.user_data = self._load_data()

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    @filter.command("cx", alias={'查询', '查询人数'})
    async def cx(self, event: AstrMessageEvent):
        """获取Horizon服务器人数"""
        url = "https://scp.manghui.net/list/?serverName=hor"
        try:
            response = requests.get(url, timeout=10)
            response.encoding = 'gbk'
            a = response.text
        except Exception as e:
            yield event.plain_result("获取失败\nError Code: 001") # 发送一条纯文本消息
            return
        c = ""
        if a:
            tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', a, re.DOTALL)
        
            server_types = [
                "无规则轻插件一服", "有规则轻插件二服", "无规则轻插件三服",
                "有规则轻插件四服", "有规则轻插件五服", "有规则轻插件六服",
                "有规则轻插件七服", "有规则轻插件八服"
            ]
    
            lines = []
            for i, tr_content in enumerate(tr_matches[1:9], 1):
                td_matches = re.findall(r'<td[^>]*>(.*?)</td>', tr_content, re.DOTALL)
                if len(td_matches) >= 4:
                    people_clean = re.sub(r'<[^>]+>', '', td_matches[3]).strip()
                    lines.append(f"HORIZON {server_types[i-1]} 在线人数：{people_clean}")
            
            c = "\n".join(lines)
        yield event.plain_result(c) 

    @filter.command("stat")
    async def stat(self, event: AstrMessageEvent):
        stats_text = """数据获取失败！
当前等级：0
------击杀统计------
击杀玩家次数：0
死亡次数：0
击杀收容物数：0
对收容物伤害：0
击杀D级人员数：0
击杀科学家数：0
------角色统计------
成为收容物次数：0
成为D级人员次数：0
成为科学家次数：0
成为设施警卫次数：0
重生为混沌分裂者次数：0
重生为九尾狐次数：0
------其他统计------
逃离设施次数：0
游玩时长：0小时
MVP次数：0把"""
        yield event.plain_result(stats_text)


    def _load_data(self) -> Dict:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载数据失败: {e}")
                return {}
        return {}

    def _save_data(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def _get_user_info(self, user_id: str) -> Dict:
        today = date.today().isoformat()
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "date": today,
                "chances": 2,
                "last_wife": None
            }
            self._save_data()
        else:
            if self.user_data[user_id].get("date") != today:
                self.user_data[user_id]["date"] = today
                self.user_data[user_id]["chances"] = 2
                self._save_data()
        return self.user_data[user_id]

    def _can_use(self, user_id: str) -> bool:
        user_info = self._get_user_info(user_id)
        return user_info.get("chances", 0) > 0

    def _use_chance(self, user_id: str, wife_nickname: str, wife_qq: str):
        user_info = self._get_user_info(user_id)
        if user_info.get("chances", 0) > 0:
            user_info["chances"] -= 1
            user_info["last_wife"] = {
                "nickname": wife_nickname,
                "qq": wife_qq
            }
            self._save_data()
            return True
        return False

    def _get_last_wife(self, user_id: str) -> Optional[Dict]:
        user_info = self._get_user_info(user_id)
        return user_info.get("last_wife")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        message_str = event.message_str 
        if message_str == "今日老婆" or message_str == "换老婆":
            sender_id = str(event.get_sender_id())
            if not self._can_use(sender_id):
                last_wife = self._get_last_wife(sender_id)
                if last_wife:
                    qq_number = last_wife["qq"]
                    nickname = last_wife["nickname"]
                    avatar_url = f"https://q1.qlogo.cn/g?b=qq&nk={qq_number}&s=640"
                    message_chain = [
                        At(qq=event.get_sender_id()),
                        Plain(text="\n渣男，你今天没老婆了！\n你今天的群友老婆是：\n"),
                        Image.fromURL(avatar_url),
                        Plain(text=f"{nickname}({qq_number})")
                    ]
                else:
                    message_chain = [
                        At(qq=event.get_sender_id()),
                        Plain(text="\n渣男，你今天没老婆了！")
                    ]
                yield event.chain_result(message_chain)
                return
            
            group = await event.get_group()
            if group and group.members:
                member_list = group.members
                random_member = random.choice(member_list)
                qq_number = str(random_member.user_id)
                nickname = random_member.nickname or f"QQ {qq_number}"
                avatar_url = f"https://q1.qlogo.cn/g?b=qq&nk={qq_number}&s=640"

                self._use_chance(sender_id, nickname, qq_number)
                user_info = self._get_user_info(sender_id)
                remaining = user_info.get("chances", 0)
                
                message_chain = [
                    At(qq=event.get_sender_id()),
                    Plain(text=f"\n你今天的群友老婆是：\n"),
                    Image.fromURL(avatar_url),
                    Plain(text=f"{nickname}({qq_number})\n")
                ]
                if remaining > 0:
                    message_chain.append(Plain(text=f"剩余今日换老婆次数：{remaining}次"))
                else:
                    message_chain.append(Plain(text="这是你的最后一个老婆了，要好好对待她哦~"))
                #build 26.07.20.2新增每日一言
                hitokoto = await self._fetch_hitokoto()
                if hitokoto:
                    message_chain.append(Plain(text=f"\n{hitokoto}"))

                yield event.chain_result(message_chain)
            else:
                yield event.plain_result("获取失败\nError Code: 002")

    async def _fetch_hitokoto(self) -> str:
        url = "https://v1.hitokoto.cn/?c=i&encode=json"
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        hitokoto = data.get("hitokoto", "")
                        return f"「 {hitokoto} 」" if hitokoto else ""
                    return ""
        except Exception:
            return ""


    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        self._save_data()
