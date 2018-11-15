# WS client example

import asyncio
import websockets
import json
from datetime import datetime, timedelta

async def hello():
    async with websockets.connect('ws://localhost:8765') as websocket1:
        async with websockets.connect('ws://localhost:7654') as websocket2:
            act = input("0-Leave\n1-Create Auction\n2-Close Auction\n3-List Auctions\n4-List Bids of Auction\n5-List Bids by Client\n6-Check Outcome\n7-Make Bid\nAction: ")
            while act!="0":
                if act!="1" and act!="2":
                    message={"action":act}
                    if act=="4" or act=="6":
                        message["auction"]={"serialNum":input("Serial Number: ")}
                    if act=="5":
                        message["user"]=input("User: ")
                    if act=="7":
                        message["bid"]={"auction": input("Auction: "),"user": input("User: "),"amount":float(input("Amount: ")), "time":str(datetime.now())}
                    await websocket2.send(json.dumps(message))
                    response = await websocket2.recv()
                    print(response)
                else:
                    message={"action":act}
                    if act=="1":
                        atype = input("Auction Type (1-English Auction, 2-Reversed Auction, 3-BlindAuction): ")
                        minimumV = float(input("Minimum Value: "))
                        if atype=="2":
                            startingV = float(input("Starting Value: "))
                            marginV = float(input("Margin Value: "))
                            message["auction"]={"type":atype,"minv":minimumV,"startv":startingV,"marginv":marginV,"name":input("Name: "),"descr":input("Description: "),"serialNum":input("Serial Number: "), "time":str(datetime.now()+timedelta(minutes=int(input("Valid Minutes: "))))}
                        else:
                            message["auction"]={"type":atype,"minv":minimumV,"name":input("Name: "),"descr":input("Description: "),"serialNum":input("Serial Number: "), "time":str(datetime.now()+timedelta(minutes=int(input("Valid Minutes: "))))}
                        limitUsers=input("Limit of Users: ")
                        if limitUsers=="":
                            limitUsers="-1"
                        usersBids=input("Limit of Bids per User: ")
                        if usersBids=="":
                           usersBids="-1"
                        message["auction"]["limitusers"]=int(limitUsers)
                        message["auction"]["userbids"]=int(usersBids)
                        message["auction"]["validation"]=input("Validation file: ")
                    if act=="2":
                        message["auction"]={"serialNum":input("Serial Number: ")}
                    await websocket1.send(json.dumps(message))
                    response = await websocket1.recv()
                    print(response)
                act = input("0-Leave\n1-Create Auction\n2-Close Auction\n3-List Auctions\n4-List Bids of Auction\n5-List Bids by Client\n6-Check Outcome\n7-Make Bid\nAction: ")

asyncio.get_event_loop().run_until_complete(hello())
