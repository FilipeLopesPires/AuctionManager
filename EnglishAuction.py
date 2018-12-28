from datetime import datetime
import asyncio
import websockets
import threading
import json
from Bid import Bid
import os
import pickle
import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

'''
    Ascending price auction. Each bid must overcome the value of the previous one. 
    The auction starts with a minimum value.
'''
class EnglishAuction:
    def __init__(self, name, descript, time, serialNum, repository, minimumValue):
        self.bids=[]
        self.name=name
        self.serialNum=serialNum
        self.descript=descript
        self.time=datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        self.live=True
        self.repository=repository
        self.highestBidValue=minimumValue
        self.minimumValue=minimumValue

        self.key=os.urandom(32)
        self.iv=os.urandom(16)

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

        repoPrivKey = self.repository.getPrivKey()

        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(self.bids[len(self.bids)-1])
        checksum = digest.finalize()

        sealBid= Bid({"auction":self.serialNum, "user":"", "amount":str(-1), "time":datetime.strptime( str(datetime.now()), '%Y-%m-%d %H:%M:%S.%f')})

        check_cyphered = repoPrivKey.sign(
            symmetric_iv,
            padding.PKCS1v15(),
            utils.Prehashed(hashes.SHA256())
        )

        sealBid.addCheckSum(check_cyphered)

        thisIv=checksum[0:16]

        cipher = Cipher(algorithms.AES(self.key), modes.OFB(thisIv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(serializedBid) + encryptor.finalize()

        xorValue=b""
        for i in range(len(ct)):
            xorValue+=str.encode(chr(ct[i] ^ thisIv[i%len(thisIv)]))

        self.bids.append(xorValue)



    def getBids(self):
        return [base64.b64encode(x).decode("utf-8") for x in self.bids]


    def getKeyIv(self):
        return base64.b64encode(self.key).decode("utf-8"), base64.b64encode(self.iv).decode("utf-8")



    #adicionar aos bids e atualizar a higher bid
    async def makeBid(self, bid):
        bid = Bid(bid)
        if await self.repository.validateBid(bid):
            if self.live:
                if bid.getAmount()>self.highestBidValue:

                    self.highestBidValue=bid.getAmount()

                    if len(self.bids)==0:
                        bid.addCheckSum(self.iv)
                        serializedBid = pickle.dumps(bid)

                        cipher = Cipher(algorithms.AES(self.key), modes.OFB(self.iv), backend=default_backend())
                        encryptor = cipher.encryptor()
                        ct = encryptor.update(serializedBid) + encryptor.finalize()

                        xorValue=b""
                        for i in range(len(ct)):
                            xorValue+=str.encode(chr(ct[i] ^ self.iv[i%len(self.iv)]))

                    else:

                        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
                        digest.update(self.bids[len(self.bids)-1])
                        checksum = digest.finalize()

                        bid.addCheckSum(checksum)

                        serializedBid = pickle.dumps(bid)

                        thisIv=checksum[0:16]

                        cipher = Cipher(algorithms.AES(self.key), modes.OFB(thisIv), backend=default_backend())
                        encryptor = cipher.encryptor()
                        ct = encryptor.update(serializedBid) + encryptor.finalize()

                        xorValue=b""
                        for i in range(len(ct)):
                            xorValue+=str.encode(chr(ct[i] ^ thisIv[i%len(thisIv)]))

                    #self.bids.append(bid)
                    self.bids.append(xorValue)
                    return '{"user":'+bid.user+',"amount":'+ str(bid.amount) + ',"auction":' + str(bid.auction) + ',"evidence":' + base64.b64encode(xorValue).decode("utf-8") +'}'
        return '{"status":1}'

    def getWinningBid(self):
            return [x for x in self.bids if x.getAmount()==self.highestBidValue][0]

    def getRepr(self):
        return {"name":self.name, "description":self.descript, "serialNum":self.serialNum, "time":str(self.time)}