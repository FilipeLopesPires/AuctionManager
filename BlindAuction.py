from datetime import datetime
import asyncio
import websockets
import threading
import json
from Bid import Bid

'''
    Sealed first-price auction. Each bidder bids only once and waits for the end of the auction to find out the results. 
    The bids have a minimum value allowed.
'''
class BlindAuction:
    def __init__(self, name, descript, time, serialNum, repository, minimumValue):
        self.bids=[]
        self.name=name
        self.serialNum=serialNum
        self.descript=descript
        self.time=datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        self.live=True
        self.repository=repository
        self.minimumValue=minimumValue
        threading.Thread(target=self.threadAction).start()

    def threadAction(self):
        while datetime.now()<self.time and self.live:
            pass
        if self.live:
            self.repository.end(self.serialNum)
        self.live=False

    def endAuction(self):
        print("end")
        self.live=False

    def getBids(self):
        return [x.getRepr() for x in self.bids]

    #adicionar aos bids e atualizar a higher bid
    async def makeBid(self, bid):
        bid = Bid(bid)
        if await self.repository.validateBid(bid):
            if self.live:
                if bid.getAmount()>self.minimumValue:
                    self.bids.append(bid)

    def getWinningBid(self):
        highestBid = self.bids(0);
        for b in self.bids:
            if b.getAmount()>highestBid.getAmount():
                highestBid = b
        return highestBid

    def getRepr(self):
        return {"name":self.name, "description":self.descript, "serialNum":self.serialNum, "time":str(self.time)}