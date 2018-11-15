import json
import asyncio
import websockets
from EnglishAuction import EnglishAuction
from ReversedAuction import ReversedAuction
from BlindAuction import BlindAuction


class Repository:

    def __init__(self):
        self.auctions={}
        self.closed=[]

    async def process(self, jsonData):
        data=json.loads(jsonData)
        action=data["action"]
        if action=="1":#create auction          ---------receber action e auction->completa
            if data["auction"] != None:
                auct=data["auction"]
                if auct["type"]=="1":
                	a = EnglishAuction(auct["name"], auct["descr"], auct["time"], auct["serialNum"], self, auct["minv"])
                if auct["type"]=="2":
                	a = ReversedAuction(auct["name"], auct["descr"], auct["time"], auct["serialNum"], self, auct["startv"], auct["marginv"], auct["minv"])
                if auct["type"]=="3":
                	a = BlindAuction(auct["name"], auct["descr"], auct["time"], auct["serialNum"], self, auct["minv"])
                self.auctions[auct["serialNum"]]=a
        elif action=="2":#end auction         ---------receber action e auction->serialNum
            if data["auction"] != None:
                auct=data["auction"]
                if auct["serialNum"] in self.auctions.keys():
                    self.auctions[auct["serialNum"]].endAuction()
                    self.closed.append(self.auctions[auct["serialNum"]])
                    del self.auctions[auct["serialNum"]]
        elif action=="3":#list auctions          ---------receber action
            return json.dumps({"opened":[self.auctions[x].getRepr() for x in self.auctions.keys()], "closed":[x.getRepr() for x in self.closed]})
        elif action=="4":#list bids of auction         ---------receber action e auction->serialNum
            auct=data["auction"]
            return json.dumps({"bids":self.auctions[auct["serialNum"]].getBids()})
        elif action=="5":#list bids by user --------receber action e user
            user=data["user"]
            liveBids=[self.auctions[x].getBids() for x in self.auctions.keys()]
            deadBids=[x.getBids() for x in self.closed]
            return json.dumps({"bids":[y.getRepr() for x in liveBids for y in x if y.getUser()==user] + [y.getRepr() for x in deadBids for y in x if y.getUser()==user]})
        elif action=="6":#get Auction outcome          ---------receber action e auction->serialNum
            auct=data["auction"]
            return self.auctions[auct["serialNum"]].getWinningBid().getUser()
        elif action=="7":#make Bid          ---------receber action e bid
            bid=data["bid"]
            await self.auctions[bid["auction"]].makeBid(data["bid"])
        return "OK"


    def end(self, serialNum):
        self.auctions[serialNum].endAuction()
        self.closed.append(self.auctions[serialNum])
        del self.auctions[serialNum]

    async def validateBid(self, bid):
        async with websockets.connect('ws://localhost:8765') as man:
            await man.send(json.dumps({'action':'10', 'bid':bid.getRepr()}))
            result = await man.recv()
            return (True if result=="1" else False)