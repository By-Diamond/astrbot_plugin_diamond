import asyncio
import json
import os
import random
import socket
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import aiohttp

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import At, Image, Plain
from astrbot.api.star import Context, Star, register

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
    i = 6  # 4 字节头 + 'I' + 协议号
    name, i = a2s_读取字符串(data, i)
    mapname, i = a2s_读取字符串(data, i)
    i = a2s_读取字符串(data, i)[1]  # folder
    game, i = a2s_读取字符串(data, i)
    i += 2  # appid
    return {
        "name": name,
        "map": mapname,
        "game": game,
        "players": data[i],
        "maxplayers": data[i + 1],
    }


def a2s_查询(host, port, timeout=0.5, retries=1):
    """在线返回 dict，否则 None。A2S 会间歇性丢包，默认重试 1 次。"""
    for _ in range(int(retries) + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        try:
            s.sendto(A2S_INFO, (host, port))
            data, _ = s.recvfrom(65535)
            if data[:5] == b"\xff\xff\xff\xffA":  # 需要挑战码
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


@register("钻石插件", " ByDiamond", "Horizon游戏人数获取", "1.2.0")
class MyPlugin(Star):
    # 插件初始化方法与销毁方法
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config if config is not None else {}
        self.data_file = os.path.join(os.path.dirname(__file__), "wife_data.json")
        self.user_data = self.今日老婆_加载数据()
        self.picture_data_file = os.path.join(
            os.path.dirname(__file__), "picture_data.json"
        )
        self.picture_user_data = self.加载数据(self.picture_data_file)
        self.draw_lock = asyncio.Lock()
        self.picture_lock = asyncio.Lock()

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        self.今日老婆_保存数据()
        self.保存数据(self.picture_data_file, self.picture_user_data)

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # 指令区
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————

    @filter.command("cx", alias={"查询", "查询人数", "cs", "cxx"})
    async def 指令_查询人数(self, event: AstrMessageEvent):
        """获取Horizon服务器人数（A2S 直查）"""
        results = await asyncio.gather(
            *(
                asyncio.to_thread(a2s_查询, host, port)
                for _, host, port in HORIZON_SERVERS
            )
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
        if event.message_str.strip() not in {"今日老婆", "换老婆"}:
            return
        sender_id = str(event.get_sender_id())
        group_id = f"{event.get_platform_name()}:{event.get_group_id()}"
        async with self.draw_lock:
            user_info = self.今日老婆_获取用户信息(group_id, sender_id)
            if user_info["chances"] <= 0:
                yield event.chain_result(
                    [At(qq=sender_id), Plain(text="渣男！你今天没老婆了！")]
                )
                return
            try:
                group = await event.get_group()
            except Exception as error:
                logger.warning(f"[Diamond Plugin] Failed to get group: {error}")
                group = None
            if not group or not group.members:
                yield event.plain_result("获取失败\nError Code: 002")
                return
            members = list(group.members)
            last_wife = user_info.get("last_wife") or {}
            alternatives = [
                member
                for member in members
                if str(member.user_id) != last_wife.get("qq")
            ]
            random_member = random.choice(alternatives or members)
            qq_number = str(random_member.user_id)
            nickname = (
                getattr(random_member, "card", None)
                or random_member.nickname
                or f"QQ {qq_number}"
            )
            warning = (
                "渣男，再换你今天就没老婆了！\n" if user_info["chances"] == 1 else ""
            )
            self.今日老婆_消耗娶老婆次数(group_id, sender_id, nickname, qq_number)
            yield event.chain_result(
                [
                    At(qq=sender_id),
                    Plain(text=f"\n{warning}你今天的群友老婆是：\n"),
                    Image.fromURL(f"https://q1.qlogo.cn/g?b=qq&nk={qq_number}&s=640"),
                    Plain(text=f"\n{nickname}({qq_number})"),
                ]
            )

    def 加载数据(self, path: str) -> dict:
        try:
            with open(path, encoding="utf-8") as data_file:
                data = json.load(data_file)
            return data if isinstance(data, dict) else {}
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as error:
            logger.error(f"[Diamond Plugin] Failed to load data: {error}")
            raise

    def 保存数据(self, path: str, data: dict):
        temporary_path = path + ".tmp"
        with open(temporary_path, "w", encoding="utf-8") as data_file:
            json.dump(data, data_file, ensure_ascii=False, indent=2)
        os.replace(temporary_path, path)

    def 今日老婆_加载数据(self) -> dict:
        return self.加载数据(self.data_file)

    def 今日老婆_保存数据(self):
        self.保存数据(self.data_file, self.user_data)

    def 今日老婆_获取用户信息(self, group_id: str, user_id: str) -> dict:
        today = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
        group_data = self.user_data.setdefault("groups", {}).setdefault(group_id, {})
        if group_data.get(user_id, {}).get("date") != today:
            group_data[user_id] = {"date": today, "chances": 2, "last_wife": None}
        return group_data[user_id]

    def 今日老婆_是否能换老婆(self, group_id: str, user_id: str) -> bool:
        return self.今日老婆_获取用户信息(group_id, user_id)["chances"] > 0

    def 今日老婆_消耗娶老婆次数(
        self, group_id: str, user_id: str, wife_nickname: str, wife_qq: str
    ):
        user_info = self.今日老婆_获取用户信息(group_id, user_id)
        if user_info["chances"] <= 0:
            return False
        previous_info = dict(user_info)
        user_info["chances"] -= 1
        user_info["last_wife"] = {"nickname": wife_nickname, "qq": wife_qq}
        try:
            self.今日老婆_保存数据()
        except OSError:
            user_info.update(previous_info)
            raise
        return True

    # —— 今日图图次数（每人每天 2 次） ——

    # build 26.07.20.2新增每日一言
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
    # 群消息监听 · 今日图图功能
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def 今日图图_监听器(self, event: AstrMessageEvent):
        if event.message_str.strip() not in {"今日图图", "换图图"}:
            return
        sender_id = str(event.get_sender_id())
        group_id = f"{event.get_platform_name()}:{event.get_group_id()}"
        async with self.picture_lock:
            today = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
            group_data = self.picture_user_data.setdefault("groups", {}).setdefault(
                group_id, {}
            )
            if group_data.get(sender_id, {}).get("date") != today:
                group_data[sender_id] = {"date": today, "chances": 2}
            user_info = group_data[sender_id]
            if user_info["chances"] <= 0:
                yield event.chain_result(
                    [
                        At(qq=sender_id),
                        Plain(text="你今天的图图次数已用完，明天再来吧！"),
                    ]
                )
                return
            picture = await self.今日图图_获取图片()
            if picture is None:
                yield event.chain_result(
                    [
                        At(qq=sender_id),
                        Plain(
                            text="暂时没有可用的图图，请配置本地图库或外部图库后再试。"
                        ),
                    ]
                )
                return
            user_info["chances"] -= 1
            try:
                self.保存数据(self.picture_data_file, self.picture_user_data)
            except OSError:
                user_info["chances"] += 1
                raise
            yield event.chain_result(
                [At(qq=sender_id), Plain(text="\n你今天的图图是：\n"), picture]
            )

    async def 今日图图_获取图片(self):
        source = self.config.get("picture_source", "auto")
        directory = Path(self.config.get("picture_local_dir") or "images")
        if not directory.is_absolute():
            directory = Path(__file__).parent / directory
        if source in {"auto", "local"}:
            try:
                pictures = (
                    [
                        path
                        for path in directory.iterdir()
                        if path.is_file()
                        and path.suffix.lower()
                        in {".jpg", ".jpeg", ".png", ".gif", ".webp"}
                    ]
                    if directory.is_dir()
                    else []
                )
                if pictures:
                    return Image.fromFileSystem(str(random.choice(pictures).resolve()))
            except OSError as error:
                logger.warning(f"[Diamond Plugin] Failed to read local images: {error}")
            if source == "local":
                return None
        url = self.config.get(
            "picture_external_url", "https://api.yppp.net/pc.php?return=json"
        ).strip()
        if source not in {"auto", "external"} or not url:
            return None
        if not url.startswith(("https://", "http://")):
            return None
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    content_type = response.headers.get("Content-Type", "").lower()
                    if content_type.startswith("image/"):
                        return Image.fromURL(str(response.url))
                    data = await response.json(content_type=None)
                    field = self.config.get("picture_external_json_field", "acgurl")
                    for key in field.split("."):
                        data = data[key]
                    if isinstance(data, str) and data.startswith(
                        ("https://", "http://")
                    ):
                        return Image.fromURL(data)
        except (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            logger.warning(f"[Diamond Plugin] Failed to fetch external image: {error}")
        return None
