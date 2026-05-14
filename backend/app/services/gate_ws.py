import asyncio
import json
import websockets

GATE_WS = "wss://api.gateio.ws/ws/v4/"

tracked = {
    "BTC_USDT": {
        "last": 79000,
        "volume": 999999,
        "change": 5.2
    }
}

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
                    "payload": ["BTC_USDT"]
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

                            print("TRACKED:", tracked)

        except Exception as e:

            print("WS ERROR:", str(e))

            await asyncio.sleep(5)