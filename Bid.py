import json
from cryptography.hazmat.primitives import serialization
import base64

class Bid:
    def __init__(self, data, key=None):
        self.time=data["time"]
        self.user=data["user"]
        self.amount=data["amount"]
        self.auction=data["auction"]
        self.signature=None if key==None else data["signature"]
        self.clientKey=None if key==None else base64.b64encode(key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.PKCS1)).decode("utf-8")
        self.checksumUntilNow=b""

    def addCheckSum(self, check):
        self.checksumUntilNow=check

    def getRepr(self):
        return {"time":self.time,"user":self.user, "amount":self.amount, "auction":self.auction, "signature":self.signature, "client_key":self.clientKey, "checksumUntilNow":base64.b64encode(self.checksumUntilNow).decode("utf-8")}