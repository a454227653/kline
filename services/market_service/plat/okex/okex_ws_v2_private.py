import asyncio
import aiohttp
import json
import time
import hmac
import base64
import sys

# # 在 Windows 上强制使用 SelectorEventLoop
# if sys.platform == 'win32':
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# === OKX API 配置（请替换为你的 API Key 信息） ===
API_KEY = "1902dede-d512-4a4c-bcb1-c417d1405cfa"        # 你的 API Key
SECRET_KEY = "97057E0919FE0BC86D0C05DB521FB3CE"  # 你的 API Secret
PASSPHRASE = "qjj135791Q."  # 你的 Passphrase

# === OKX WebSocket API 地址 ===
PRIVATE_WS_URL = "wss://wspap.okx.com:8443/ws/v5/private"  # 私有 WebSocket（账户数据）


def generate_okx_signature(timestamp, method, request_path, body=""):
    """
    生成 OKX API 签名
    :param timestamp: 当前时间戳
    :param method: HTTP 方法（"GET", "POST"）
    :param request_path: 请求路径
    :param body: 请求体
    :return: 签名
    """
    message = f"{timestamp}{method}{request_path}{body}"
    mac = hmac.new(SECRET_KEY.encode("utf-8"), message.encode("utf-8"), digestmod="sha256")
    return base64.b64encode(mac.digest()).decode("utf-8")


async def connect_private_ws():
    """连接 OKX 私有 WebSocket 并订阅账户数据"""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(PRIVATE_WS_URL) as ws:
            print("✅ 成功连接到 OKX 私有 WebSocket")

            # 计算 API 认证参数
            timestamp = str(time.time())
            signature = generate_okx_signature(timestamp, "GET", "/users/self/verify")

            # 发送 API Key 认证请求
            auth_msg = {
                "op": "login",
                "args": [{
                    "apiKey": API_KEY,
                    "passphrase": PASSPHRASE,
                    "timestamp": timestamp,
                    "sign": signature
                }]
            }
            await ws.send_json(auth_msg)
            print("🔐 发送 API 认证请求...")

            # 监听认证结果
            auth_response = await ws.receive_json()
            if auth_response.get("event") == "login" and auth_response.get("code") == "0":
                print("✅ API 认证成功！")
            else:
                print(f"❌ API 认证失败: {auth_response}")
                return  # 退出连接

            # 订阅账户余额 & 订单数据
            subscribe_msg = {
                "op": "subscribe",
                "args": [{
                    "channel": "balance_and_position"
                }]
            }
            await ws.send_json(subscribe_msg)
            print("📡 已订阅账户余额 & 订单数据")
           
            # 订阅账户余额 & 订单数据
            subscribe_msg =  {
                "id": "1512",
                "op": "order",
                "args": [{
                    "side": "buy",
                    "instId": "BTC-USDT",
                    "tdMode": "cash",
                    "ordType": "market",
                    "sz": "99047"
                }]
            }
            await ws.send_json(subscribe_msg)
            # 监听账户数据
            async for msg in ws:
                data = json.loads(msg.data)
                if "data" in data:
                    print(f"📊 [私有] 账户数据: {data}")
                else:
                    print(f"⚠️ [私有] 收到消息: {data}")


async def main():
    """同时运行 公共 & 私有 WebSocket 连接"""
    await asyncio.gather(connect_private_ws())


if __name__ == "__main__":
    asyncio.run(main())