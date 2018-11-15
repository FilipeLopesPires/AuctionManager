# WS server example

import asyncio
import websockets
from Manager import Manager

man = Manager()

async def sioManager(websocket, path):
    async with websockets.connect('ws://localhost:7654') as repo:
        while True:
            request = await websocket.recv()
            await websocket.send(await man.process(request,repo))

start_server = websockets.serve(sioManager, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
