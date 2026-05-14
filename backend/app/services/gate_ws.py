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

                print("Connected to Gate.io websocket")

                while True:
                    msg = await ws.recv()

                    data = json.loads(msg)

                    if data.get("event") == "update":

                        results = data.get("result", [])

                        for result in results:

                            symbol = result.get("currency_pair")

                            if symbol:

                                tracked[symbol] = {
                                    "last": result.get("last"),
                                    "volume": result.get("base_volume"),
                                    "change": result.get("change_percentage"),
                                }

        except Exception as e:
            print("Gate WS error:", e)

            await asyncio.sleep(5)