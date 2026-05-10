import asyncio
import websockets

async def test():
    print("Starting test...")
    try:
        async with websockets.connect("wss://api.sgroup.qq.com/websocket/") as ws:
            print("Connected!")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
