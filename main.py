from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Image, At, Plain
from astrbot.api import logger
import requests
import re
import random
import json
import os
from datetime import date
from typing import Dict, Optional
import aiohttp
import asyncio

@register("钻石插件", " ByDiamond", "Horizon游戏人数获取", "1.0.0")
class MyPlugin(Star):
    # 插件初始化方法与销毁方法
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_file = os.path.join(os.path.dirname(__file__), "wife_data.json")
        self.user_data = self.今日老婆_加载数据()
        self.loli_messages = [
            "这是你今天的萝莉哦，要好好爱她~",
            "嘿，你的小萝莉已送达，请签收！",
            "今日份的可爱萝莉，请查收~",
            "你的专属萝莉已上线！",
            "萝莉时间到！快来抱走你的小可爱！",
            "新鲜出炉的萝莉，还热乎着呢！",
            "今天也要和萝莉一起元气满满哦！",
            "叮！你的小萝莉已空降！",
            "这只萝莉说想你了~",
            "萝莉向你发送了一个wink！",
            "请查收今日份的治愈系萝莉~",
            "你的小天使萝莉来咯！",
            "萝莉在此，快来互动吧！",
            "今日幸运萝莉，与你相遇~",
            "可爱的萝莉正在等你呢！",
            "这是你今天的萝莉，请好好珍惜~",
            "萝莉拍了拍你，说：今天也要开心哦！",
            "给你变出一只小萝莉！",
            "你的小萝莉正在偷看你~",
            "这只萝莉是今天限定的哦！",
            "快来领取你的专属小可爱！",
            "萝莉已经准备好陪你啦！",
            "今天的萝莉格外可爱呢！",
            "你的小萝莉正向你跑来~",
            "萝莉说：今天要一直陪着你！",
            "这是你今天的幸运萝莉~",
            "你的小可爱突然出现！",
            "萝莉为你准备了一份好心情！",
            "今天的萝莉也元气十足！",
            "快来抱抱你的小萝莉~",
            "你的专属小萝莉已绑定！",
            "萝莉正在向你发射爱心~",
            "这是你今天的甜心萝莉~",
            "萝莉说：今天也要加油哦！",
            "你的小萝莉已上线，请互动~",
            "今日份的可爱已送达！",
            "萝莉等你很久啦！",
            "你的小天使已降临~",
            "这只萝莉超级粘人哦！",
            "萝莉正在呼唤你~",
            "今日萝莉：可爱指数满格！",
            "你的小萝莉准备了一个惊喜~",
            "萝莉想和你一起玩耍！",
            "这是你今天的专属小可爱~",
            "萝莉说：你是最棒的！",
            "你的小萝莉正在对你笑~",
            "今日幸运物：一只小萝莉！",
            "萝莉为你带来了好运气~",
            "你的小可爱已送达，请查收！",
            "萝莉说：今天要一直一直陪着你！"
        ]

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        self.今日老婆_保存数据()

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # 指令区
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————

    @filter.command("cx", alias={'查询', '查询人数','cs','cxx'})
    async def 指令_查询人数(self, event: AstrMessageEvent):
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
    async def 指令_查询数据(self, event: AstrMessageEvent):
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

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # 群消息监听 · 今日老婆功能
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def 今日老婆_监听器(self, event: AstrMessageEvent):
        message_str = event.message_str 
        if message_str == "今日老婆" or message_str == "换老婆":
            sender_id = str(event.get_sender_id())
            if not self.今日老婆_是否能换老婆(sender_id):
                last_wife = self.今日老婆_获取上次老婆信息(sender_id)
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

                self.今日老婆_消耗娶老婆次数(sender_id, nickname, qq_number)
                user_info = self.今日老婆_获取用户信息(sender_id)
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
                hitokoto = await self.今日老婆_获取每日一言()
                if hitokoto:
                    message_chain.append(Plain(text=f"\n\n{hitokoto}"))

                yield event.chain_result(message_chain)
            else:
                yield event.plain_result("获取失败\nError Code: 002")

    def 今日老婆_加载数据(self) -> Dict:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[Diamond Plugin]加载Wife数据失败: {e}")
                return {}
        return {}

    def 今日老婆_保存数据(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[Diamond Plugin]保存Wife数据失败: {e}")

    def 今日老婆_获取用户信息(self, user_id: str) -> Dict:
        today = date.today().isoformat()
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "date": today,
                "chances": 2,
                "last_wife": None
            }
            self.今日老婆_保存数据()
        else:
            if self.user_data[user_id].get("date") != today:
                self.user_data[user_id]["date"] = today
                self.user_data[user_id]["chances"] = 2
                self.今日老婆_保存数据()
        return self.user_data[user_id]

    def 今日老婆_是否能换老婆(self, user_id: str) -> bool:
        user_info = self.今日老婆_获取用户信息(user_id)
        return user_info.get("chances", 0) > 0

    def 今日老婆_消耗娶老婆次数(self, user_id: str, wife_nickname: str, wife_qq: str):
        user_info = self.今日老婆_获取用户信息(user_id)
        if user_info.get("chances", 0) > 0:
            user_info["chances"] -= 1
            user_info["last_wife"] = {
                "nickname": wife_nickname,
                "qq": wife_qq
            }
            self.今日老婆_保存数据()
            return True
        return False

    def 今日老婆_获取上次老婆信息(self, user_id: str) -> Optional[Dict]:
        user_info = self.今日老婆_获取用户信息(user_id)
        return user_info.get("last_wife")

    async def 今日老婆_获取每日一言(self) -> str:
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

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # 群消息监听 · 今日萝莉功能
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def 今日萝莉_监听器(self, event: AstrMessageEvent):
        message_str = event.message_str

        if message_str == "今日萝莉" or message_str == "换萝莉":
            sender_id = event.get_sender_id()
            sender_name = event.get_sender_name()
            image_url = await self.今日老婆_获取图片()
            random_message = random.choice(self.loli_messages)

            if image_url:
                content = [
                    At(qq=sender_id),
                    Plain(text=f"\n{random_message}\n"),
                    Image.fromURL(image_url)
                ]
            else:
                content = [
                    At(qq=sender_id),
                    Plain(text="\n获取萝莉图片失败了，请稍后再试~")
                ]

            node = Node(
                uin=sender_id,
                name=sender_name,
                content=content
            )
            yield event.chain_result([node])

    async def 今日老婆_获取图片(self) -> str:
        url = "https://api.yppp.net/pc.php?return=json"
        timeout = aiohttp.ClientTimeout(total=5)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        acgurl = data.get("acgurl", "")
                        if acgurl:
                            return acgurl.replace("\\/", "/")
                    return ""
        except asyncio.TimeoutError:
            logger.warning("[Diamond Plugin]获取萝莉图片超时")
            return ""
        except Exception as e:
            logger.error(f"[Diamond Plugin]获取萝莉图片失败: {e}")
            return ""
        
        