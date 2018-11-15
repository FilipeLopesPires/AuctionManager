import json

class Bid:
    def __init__(self, data):
        self.time=data["time"]
        self.user=data["user"]
        self.amount=data["amount"]
        self.auction=data["auction"]


    def getUser(self):
        return self.user

    def getAmount(self):
        return self.amount

    def getRepr(self):
        return {"auction":self.auction, "user":self.user, "amount":self.amount, "time":self.time}