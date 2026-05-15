import asyncio
import json
import websockets

GATE_WS = "wss://api.gateio.ws/ws/v4/"

tracked = {}
volume_history = {}
price_history = {}

async def gate_loop():

    print("STARTING GATE LOOP")

    while True:

        try:
            print("CONNECTING TO GATE")

            async with websockets.connect(GATE_WS) as ws:

                print("CONNECTED!")

                payload = {
                    "time": 0,
                    "channel": "spot.tickers",
                    "event": "subscribe",
                    "payload": ["!all"]
                }

                await ws.send(json.dumps(payload))

                print("SUBSCRIBED")

                while True:

                    msg = await ws.recv()

                    print("RAW MESSAGE:", msg)

                    data = json.loads(msg)

                    if data.get("event") == "update":

                        result = data.get("result")

                        print("UPDATE:", result)

                        if isinstance(result, dict):

                            symbol = result.get("currency_pair")

                            tracked[symbol] = {
                                "last": result.get("last"),
                                "volume": result.get("base_volume"),
                                "change": result.get("change_percentage"),
                            }

                        current_volume = float(result.get("base_volume", 0))
                        current_price = float(result.get("last", 0))

                        if symbol not in volume_history:
                            volume_history[symbol] = []

                        volume_history[symbol].append(current_volume)
                        if symbol not in price_history:
                            price_history[symbol] = []

                        price_history[symbol].append(current_price)

                        price_history[symbol] = price_history[symbol][-20:]

                        # chỉ giữ 20 mẫu gần nhất
                        volume_history[symbol] = volume_history[symbol][-20:]

                        current_price = float(result.get("last", 0))

                        if symbol not in price_history:
                            price_history[symbol] = []

                        price_history[symbol].append(current_price)

                        price_history[symbol] = price_history[symbol][-50:]

                        print("TRACKED:", tracked)

        except Exception as e:

            print("WS ERROR:", str(e))

            await asyncio.sleep(5)