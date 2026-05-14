import asyncio
import json
import websockets

GATE_WS = "wss://api.gateio.ws/ws/v4/"

tracked = {}

async def gate_loop():
    while True:
        try:
            async with websockets.connect(GATE_WS) as ws:

                payload = {
                    "time": 0,
                    "channel": "spot.tickers",
                    "event": "subscribe",
                    "payload": ["ALL"]
                }

                await ws.send(json.dumps(payload))

                while True:
                    msg = await ws.recv()

                    data = json.loads(msg)

                    if "result" in data:
                        result = data["result"]

                        if isinstance(result, dict):

                            symbol = result.get("currency_pair")

                            tracked[symbol] = {
                                "last": result.get("last"),
                                "volume": result.get("base_volume"),
                                "change": result.get("change_percentage"),
                            }

        except Exception as e:
            print("Gate WS error:", e)

            await asyncio.sleep(5)