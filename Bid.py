import json

class Bid:
    def __init__(self, data):
        self.time=data["time"]
        self.user=data["user"]
        self.amount=data["amount"]
        self.auction=data["auction"]
        self.checksumUntilNow=None

    def addCheckSum(self, check):
        self.checksumUntilNow=check

    def getRepr(self):
        return {"auction":self.auction, "user":self.user, "amount":str(self.amount), "time":self.time}