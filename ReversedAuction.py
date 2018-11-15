from datetime import datetime
import asyncio
import websockets
import threading
import json
from Bid import Bid

'''
    Descending price auction. Each bid must undercome the value of the previous one, given a static margin. 
    The auction starts with a maximum value and never hits a value lower than a given minimum.
'''
class ReversedAuction:
    def __init__(self, name, descript, time, serialNum, repository, startingValue, marginValue, minimumValue):
        self.bids=[]
        self.name=name
        self.serialNum=serialNum
        self.descript=descript
        self.time=datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        self.live=True
        self.repository=repository
        self.lowestBidValue=startingValue
        self.marginValue=marginValue
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
                if bid.getAmount()<self.lowestBidValue and self.lowestBidValue-bid.getAmount()<self.marginValue and bid.getAmount()>self.minimumValue:
                    self.lowestBidValue=bid.getAmount()
                    self.bids.append(bid)

    def getWinningBid(self):
        return [x for x in self.bids if x.getAmount()==self.lowestBidValue][0]

    def getRepr(self):
        return {"name":self.name, "description":self.descript, "serialNum":self.serialNum, "time":str(self.time)}