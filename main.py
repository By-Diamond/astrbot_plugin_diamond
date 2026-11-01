from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Image, At, Plain
from astrbot.api import logger
import random
import json
import os
import socket
from datetime import date
from typing import Dict
import aiohttp
import asyncio

# ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# A2S 直查服务器人数（与 SL_Restart 同一套实现）
# ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————

A2S_INFO = b"\xff\xff\xff\xffTSource Engine Query\x00"

# (服务器名, 地址, 端口) —— 顺序即输出顺序
HORIZON_SERVERS = [
    ("无规则轻插件一服", "180.188.21.179", 7777),
    ("有规则轻插件二服", "180.188.21.179", 7778),
    ("无规则轻插件三服", "180.188.21.179", 7779),
    ("有规则轻插件四服", "180.188.21.179", 7780),
    ("无规则轻插件五服", "180.188.21.179", 7781),
    ("有规则轻插件六服", "180.188.21.179", 7782),
    ("有规则轻插件七服", "180.188.21.179", 7783),
    ("有规则轻插件八服", "180.188.21.179", 7784),
]


def a2s_读取字符串(buf, i):
    j = buf.index(b"\x00", i)
    return buf[i:j].decode("utf-8", "replace"), j + 1


def a2s_解析(data):
    """解析 A2S_INFO 回包；挑战包(0x41)/其它异常返回 None。"""
    if data[:5] != b"\xff\xff\xff\xffI":
        return None
    i = 6                      # 4 字节头 + 'I' + 协议号
    name, i = a2s_读取字符串(data, i)
    mapname, i = a2s_读取字符串(data, i)
    i = a2s_读取字符串(data, i)[1]      # folder
    game, i = a2s_读取字符串(data, i)
    i += 2                     # appid
    return {"name": name, "map": mapname, "game": game,
            "players": data[i], "maxplayers": data[i + 1]}


def a2s_查询(host, port, timeout=0.5, retries=1):
    """在线返回 dict，否则 None。A2S 会间歇性丢包，默认重试 1 次。"""
    for _ in range(int(retries) + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        try:
            s.sendto(A2S_INFO, (host, port))
            data, _ = s.recvfrom(65535)
            if data[:5] == b"\xff\xff\xff\xffA":        # 需要挑战码
                s.sendto(A2S_INFO + data[5:9], (host, port))
                data, _ = s.recvfrom(65535)
            info = a2s_解析(data)
            if info is not None:
                return info
        except (socket.timeout, OSError):
            pass
        finally:
            s.close()
    return None

@register("钻石插件", " ByDiamond", "Horizon游戏人数获取", "1.1.0")
class MyPlugin(Star):
    # 插件初始化方法与销毁方法
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_file = os.path.join(os.path.dirname(__file__), "wife_data.json")
        self.user_data = self.今日老婆_加载数据()
        self.loli_data_file = os.path.join(os.path.dirname(__file__), "loli_data.json")
        self.loli_user_data = self.今日萝莉_加载数据()
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
        self.今日萝莉_保存数据()

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # 指令区
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————

    @filter.command("cx", alias={'查询', '查询人数','cs','cxx'})
    async def 指令_查询人数(self, event: AstrMessageEvent):
        """获取Horizon服务器人数（A2S 直查）"""
        results = await asyncio.gather(
            *(asyncio.to_thread(a2s_查询, host, port) for _, host, port in HORIZON_SERVERS)
        )
        lines = []
        for (server_name, _, _), info in zip(HORIZON_SERVERS, results):
            people = "离线" if not info else f"{info['players']}/{info['maxplayers']}"
            lines.append(f"HORIZON {server_name} 在线人数：{people}")
        yield event.plain_result("\n".join(lines))

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # 群消息监听 · 今日老婆功能
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def 今日老婆_监听器(self, event: AstrMessageEvent):
        message_str = event.message_str 
        if message_str == "今日老婆" or message_str == "换老婆":
            sender_id = str(event.get_sender_id())
            if not self.今日老婆_是否能换老婆(sender_id):
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

    # —— 今日萝莉次数（每人每天 2 次） ——

    def 今日萝莉_加载数据(self) -> Dict:
        if os.path.exists(getattr(self, "loli_data_file", "")):
            try:
                with open(self.loli_data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[Diamond Plugin]加载Loli数据失败: {e}")
                return {}
        return {}

    def 今日萝莉_保存数据(self):
        try:
            with open(self.loli_data_file, "w", encoding="utf-8") as f:
                json.dump(self.loli_user_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[Diamond Plugin]保存Loli数据失败: {e}")

    def 今日萝莉_获取用户信息(self, user_id: str) -> Dict:
        today = date.today().isoformat()
        user_info = self.loli_user_data.get(user_id)
        if user_info is None or user_info.get("date") != today:
            self.loli_user_data[user_id] = {"date": today, "chances": 2}
            self.今日萝莉_保存数据()
        return self.loli_user_data[user_id]

    def 今日萝莉_是否能获取(self, user_id: str) -> bool:
        return self.今日萝莉_获取用户信息(user_id).get("chances", 0) > 0

    def 今日萝莉_消耗次数(self, user_id: str) -> bool:
        user_info = self.今日萝莉_获取用户信息(user_id)
        if user_info.get("chances", 0) > 0:
            user_info["chances"] -= 1
            self.今日萝莉_保存数据()
            return True
        return False

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
            if not self.今日萝莉_是否能获取(str(sender_id)):
                return
            image_url = await self.今日老婆_获取图片()
            if not image_url:
                return
            self.今日萝莉_消耗次数(str(sender_id))
            random_message = random.choice(self.loli_messages)

            content = [
                At(qq=sender_id),
                Plain(text=f"\n{random_message}\n"),
                Image.fromURL(image_url)
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
        
        