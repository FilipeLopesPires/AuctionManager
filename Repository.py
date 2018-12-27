import os
import json
import asyncio
import websockets
from EnglishAuction import EnglishAuction
from ReversedAuction import ReversedAuction
from BlindAuction import BlindAuction

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class Repository:

    def __init__(self):
        self.auctions={}
        self.closed={}

    async def process(self, jsonData):
        data=json.loads(jsonData)
        action=data["action"]
        if action=="1":#create auction          ---------receber action e auction->completa
            if data["auction"] != None:
                auct=data["auction"]

                if auct["serialNum"] in self.auctions.keys() or auct["serialNum"] in self.closed.keys():
                    return '{"status":1}'

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
                    self.closed[auct["serialNum"]]=self.auctions[auct["serialNum"]]
                    del self.auctions[auct["serialNum"]]
        elif action=="3":#list auctions          ---------receber action
            return json.dumps({"opened":[self.auctions[x].getRepr() for x in self.auctions.keys()], "closed":[self.closed[x].getRepr() for x in self.closed.keys()]})
        elif action=="4":#list bids of auction         ---------receber action e auction->serialNum
            auct=data["auction"]
            if auct["serialNum"] not in self.closed:
                return '{"status":1}'
            return json.dumps({"bids":self.closed[auct["serialNum"]].getBids()})
        elif action=="5":#list bids by user --------receber action e user
            user=data["user"]
            liveBids=[self.auctions[x].getBids() for x in self.auctions.keys()]
            deadBids=[self.closed[x].getBids() for x in self.closed.keys()]
            return json.dumps({"bids":[y.getRepr() for x in liveBids for y in x if y.getUser()==user] + [y.getRepr() for x in deadBids for y in x if y.getUser()==user]})
        elif action=="6":#get Auction outcome          ---------receber action e auction->serialNum
            auct=data["auction"]
            return self.auctions[auct["serialNum"]].getWinningBid().getUser()
        elif action=="7":#make Bid          ---------receber action e bid
            bid=data["bid"]
            return await self.auctions[bid["auction"]].makeBid(data["bid"])
        return '{"status":0}'


    def end(self, serialNum):
        self.auctions[serialNum].endAuction()
        self.closed[serialNum]=self.auctions[serialNum]
        del self.auctions[serialNum]

    async def validateBid(self, bid):
        async with websockets.connect('ws://localhost:8765') as man:
            with open("manager_public_key.pem", "rb") as manager_public_key_file:
                with open("repository_public_key.pem", "rb") as repository_public_key_file:
                    with open("repository_private_key.pem", "rb") as repository_private_key_file:
                        manager_public_key = serialization.load_pem_public_key(manager_public_key_file.read(), backend=default_backend())
                        repository_public_key = serialization.load_pem_public_key(repository_public_key_file.read(), backend=default_backend())
                        repository_private_key = serialization.load_pem_private_key(repository_private_key_file.read(), password=b"SIO_85048_85122", backend=default_backend())

                        out = encryptMsg(json.dumps({'action':'10', 'bid':bid.getRepr(), 'key':repository_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")}),manager_public_key)

                        await man.send(out)
                        receive = await man.recv()
                        symmetric_key, symmetric_iv, result = decryptMsg(receive, repository_private_key)
                        print(result)

                        return (True if json.loads(result)["status"]==0 else False)

def decryptMsg(request, private_key):
    requestList = request.split(b"PROJ_SIO_2018")

    symmetric_key = private_key.decrypt(
        requestList[0],
        padding.PKCS1v15()
    )

    symmetric_iv = private_key.decrypt(
        requestList[1],
        padding.PKCS1v15()
    )

    cipher = Cipher(algorithms.AES(symmetric_key), modes.OFB(symmetric_iv), backend=default_backend())
    decryptor = cipher.decryptor()
    message = decryptor.update(requestList[2]) + decryptor.finalize()

    jsonData = message.decode("utf-8")

    return symmetric_key, symmetric_iv, jsonData


def encryptMsg(response, public_key):
    message = str.encode(response)

    symmetric_key = os.urandom(32)
    symmetric_iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(symmetric_key), modes.OFB(symmetric_iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(message) + encryptor.finalize()


    key_cyphered = public_key.encrypt(
        symmetric_key,
        padding.PKCS1v15()
    )

    iv_cyphered = public_key.encrypt(
        symmetric_iv,
        padding.PKCS1v15()
    )

    out= key_cyphered+ b"PROJ_SIO_2018"+ iv_cyphered+ b"PROJ_SIO_2018"+ ct

    return out