import os
import json
import time
import asyncio
import websockets
import requests
import logging
import ssl

# 设置 SSL 证书路径
os.environ["SSL_CERT_FILE"] = "/Users/daniel/.hermes/hermes-agent/venv/lib/python3.11/site-packages/certifi/cacert.pem"

# 配置
APP_ID = os.getenv("QQ_APP_ID", "1903991726")
APP_SECRET = os.getenv("QQ_APP_SECRET", "iMn11nLgojQt87sO")
ZHI_XING_LU_API = "http://localhost:5001"
IS_SANDBOX = True  # 沙箱环境

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 强制 print 刷新
def log(msg):
    msg = f"[QQ Bot] {msg}"
    print(msg, flush=True)
    with open("bot_debug.log", "a") as f:
        f.write(msg + "\n")

class QQBot:
    def __init__(self):
        self.token = None
        self.ws_url = None
        self.session_id = None
        self.shard_id = 0
        self.shard_count = 1

    def get_token(self):
        url = "https://bots.qq.com/app/getAppAccessToken"
        payload = {
            "appId": APP_ID,
            "clientSecret": APP_SECRET
        }
        headers = {"Content-Type": "application/json"}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            data = resp.json()
            if "access_token" in data:
                self.token = data["access_token"]
                log("Token acquired successfully.")
                return True
            else:
                log(f"Failed to get token: {data}")
                return False
        except Exception as e:
            log(f"Token request error: {e}")
            return False

    async def connect(self):
        headers = {"Authorization": f"QQBot {self.token}"}
        
        # 获取网关地址
        ws_url = "wss://api.sgroup.qq.com/websocket/"
        if IS_SANDBOX:
            ws_url = "wss://sandbox.api.sgroup.qq.com/websocket/"
            
        try:
            async with websockets.connect(ws_url, additional_headers=headers) as ws:
                log("Connected to QQ Gateway.")
                await self.listen(ws)
        except Exception as e:
            log(f"Connection error: {e}")
            await asyncio.sleep(5)

    async def listen(self, ws):
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                op = data.get("op")
                
                if op == 10: # Hello
                    logging.info("Received Hello, sending Identify.")
                    identify = {
                        "op": 2,
                        "d": {
                            "token": f"QQBot {self.token}",
                            "intents": 268435457, # 订阅所有事件 (268435457 = 0x10000001)
                            "shard": [self.shard_id, self.shard_count],
                            "properties": {"os": "macos", "browser": "python"}
                        }
                    }
                    log(f"Sending Identify payload with Intents: {identify['d']['intents']}")
                    await ws.send(json.dumps(identify))
                    
                    # Start heartbeat
                    interval = data["d"]["heartbeat_interval"] / 1000
                    asyncio.create_task(self.heartbeat(ws, interval))
                    
                elif op == 0: # Dispatch
                    t = data.get("t")
                    d = data.get("d")
                    
                    if t == "READY":
                        self.session_id = d.get("session_id")
                        logging.info(f"Bot Ready. Session: {self.session_id}")
                        
                    elif t == "AT_MESSAGE_CREATE":
                        await self.handle_message(ws, d)
                    elif t == "DIRECT_MESSAGE_CREATE":
                        await self.handle_message(ws, d, is_dm=True)
                        
                elif op == 1: # Heartbeat ACK
                    pass # Handled by heartbeat task
                    
            except Exception as e:
                logging.error(f"Listen error: {e}")
                await asyncio.sleep(5)
                break

    async def heartbeat(self, ws, interval):
        while True:
            try:
                await asyncio.sleep(interval)
                payload = {"op": 1, "d": int(time.time() * 1000)}
                await ws.send(json.dumps(payload))
            except:
                break

    async def handle_message(self, ws, msg, is_dm=False):
        content = msg.get("content", "").strip()
        msg_id = msg.get("id")
        
        # 提取指令 (去除 @Bot 部分)
        if "@!" in content or "@Bot" in content:
            content = content.replace("@Bot", "").strip()
            import re
            content = re.sub(r"<@!\d+>", "", content).strip()

        if content.startswith("/help"):
            await self.reply(ws, msg, "用法：\n1. /分析 [股票代码] (如 /分析 600519)\n2. /list (查看持仓)\n3. /help (帮助)")
            return

        if content.startswith("/分析") or content.startswith("/report"):
            code = content.replace("/分析", "").replace("/report", "").strip()
            if not code:
                await self.reply(ws, msg, "请输入股票代码，例如：/分析 600519")
                return
            await self.generate_report(ws, msg, code)

    async def reply(self, ws, msg, text, is_dm=False):
        # 发送被动消息
        msg_id = msg.get("id")
        group_id = msg.get("group_id")
        guild_id = msg.get("guild_id")
        channel_id = msg.get("channel_id")
        
        # 截断超长文本
        if len(text) > 1500:
            text = text[:1490] + "..."

        url = "https://api.sgroup.qq.com/v2/groups/123/messages" # 占位
        if is_dm:
             url = f"https://api.sgroup.qq.com/dms/{msg.get('guild_id')}/messages"
        elif group_id:
             url = f"https://api.sgroup.qq.com/v2/groups/{group_id}/messages"
        else:
             # 频道消息 (旧接口)
             url = f"https://api.sgroup.qq.com/channels/{channel_id}/messages"
             if IS_SANDBOX:
                 url = url.replace("api.sgroup.qq.com", "sandbox.api.sgroup.qq.com")

        headers = {
            "Authorization": f"QQBot {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": text,
            "msg_id": msg_id
        }
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            logging.info(f"Reply sent: {resp.status_code}")
        except Exception as e:
            logging.error(f"Reply error: {e}")

    async def generate_report(self, ws, msg, code):
        await self.reply(ws, msg, f"正在分析 {code}，请稍候（可能需要 1-3 分钟）...")
        
        # 调用本地 API
        try:
            # 知行录的接口通常是流式返回 HTML，我们需要简单处理一下
            # 这里为了简单，先尝试获取基本信息，或者触发后台任务
            # 实际上知行录主要是 Web 端展示，QQ 端做一个简版摘要
            
            # 假设有一个简版 API 或者我们抓取首页数据
            # 这里演示调用 /api/search 确认股票存在
            search_url = f"{ZHI_XING_LU_API}/api/search?q={code}"
            res = requests.get(search_url)
            stocks = res.json()
            
            if not stocks:
                await self.reply(ws, msg, f"未找到股票：{code}")
                return

            stock = stocks[0]
            await self.reply(ws, msg, f"正在生成 {stock['name']} ({code}) 的深度分析报告...\n\n由于报告较长（包含财务、估值、AI 观点），请前往本地 Web 端查看详细报告：\nhttp://localhost:5001/report/{code}")
            
        except Exception as e:
            await self.reply(ws, msg, f"分析失败：{str(e)}")

    async def run(self):
        log("Bot run loop started.")
        while True:
            if self.get_token():
                await self.connect()
            else:
                log("Failed to get token, retrying in 10s...")
                await asyncio.sleep(10)

if __name__ == "__main__":
    with open("bot_started.txt", "w") as f: f.write("started")
    bot = QQBot()
    asyncio.run(bot.run())
