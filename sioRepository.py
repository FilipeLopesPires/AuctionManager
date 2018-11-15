import asyncio
import websockets
from Repository import Repository

repo = Repository()

async def sioRepository(websocket, path):
    while True:
        request = await websocket.recv()
        await websocket.send(await repo.process(request))

start_server = websockets.serve(sioRepository, 'localhost', 7654)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
