import os
import json
import asyncio
import websockets
import pickle
import base64
import threading
from Bid import Bid
from datetime import datetime

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

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

        if len(self.bids)>0:
            lastBlock = bytes(self.bids[len(self.bids)-1])

            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(lastBlock)
            checksum = digest.finalize()

        else:
            checksum=self.iv


        sealBid= Bid({"auction":self.serialNum, "user":"", "amount":str(-1), "time":datetime.strptime( str(datetime.now()), '%Y-%m-%d %H:%M:%S.%f')})

        check_cyphered = repoPrivKey.sign(
            checksum,
            padding.PKCS1v15(),
            utils.Prehashed(hashes.SHA256())
        )

        sealBid.addCheckSum(check_cyphered)
        serializedBid = pickle.dumps(sealBid)

        thisIv=checksum[0:16]

        cipher = Cipher(algorithms.AES(self.key), modes.OFB(thisIv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(serializedBid) + encryptor.finalize()

        xorValue=[]
        for i in range(len(ct)):
            xorValue.append(ct[i] ^ thisIv[i%len(thisIv)])


        self.bids.append(xorValue)



    def getBids(self):
        return [base64.b64encode(bytes(x)).decode("utf-8") for x in self.bids]

    #adicionar aos bids e atualizar a higher bid
    async def makeBid(self, bid):
        bid = Bid(bid)
        if await self.repository.validateBid(bid):
            if self.live:
                if bid.amount>self.minimumValue:

                    if len(self.bids)==0:
                        bid.addCheckSum(self.iv)
                        serializedBid = pickle.dumps(bid)

                        cipher = Cipher(algorithms.AES(self.key), modes.OFB(self.iv), backend=default_backend())
                        encryptor = cipher.encryptor()
                        ct = encryptor.update(serializedBid) + encryptor.finalize()

                        xorValue=[]
                        for i in range(len(ct)):
                            xorValue.append(ct[i] ^ self.iv[i%len(self.iv)])

                    else:

                        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
                        digest.update(bytes(self.bids[len(self.bids)-1]))
                        checksum = digest.finalize()

                        bid.addCheckSum(checksum)

                        serializedBid = pickle.dumps(bid)
                        print(serializedBid)

                        thisIv=checksum[0:16]
                        cipher = Cipher(algorithms.AES(self.key), modes.OFB(thisIv), backend=default_backend())
                        encryptor = cipher.encryptor()
                        ct = encryptor.update(serializedBid) + encryptor.finalize()
                        xorValue=[]
                        for i in range(len(ct)):
                            xorValue.append(ct[i] ^ thisIv[i%len(thisIv)])

                    #self.bids.append(bid)1
                    self.bids.append(xorValue)
                    return '{"user":'+bid.user+',"amount":'+ str(bid.amount) + ',"auction":' + str(bid.auction) + ',"evidence":"' + base64.b64encode(bytes(xorValue)).decode("utf-8") +'"}'
        return '{"status":1}'


    def getOutcome(self):
        clearBids=[]

        startIndex=len(self.bids)-2
        for i in range(len(self.bids)-1):
            actualIndex=startIndex-i

            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(bytes(self.bids[actualIndex-1]))
            checksum = digest.finalize()

            serializedBid = bytes(self.bids[actualIndex])
            thisIv=checksum[0:16] if actualIndex!=0 else self.iv

            xorValue=[]
            for i in range(len(serializedBid)):
                xorValue.append(serializedBid[i] ^ thisIv[i%len(thisIv)])

            xorValue=bytes(xorValue)


            cipher = Cipher(algorithms.AES(self.key), modes.OFB(thisIv), backend=default_backend())
            decryptor = cipher.decryptor()
            ct = decryptor.update(xorValue) + decryptor.finalize()
            bid = pickle.loads(ct)

            clearBids.append(bid)

        maxAmount=0
        maxUser=""
        for b in clearBids:
            if b.amount>maxAmount:
                maxAmount=b.amount
                maxUser=b.user

        return '{"user":'+maxUser+'}'



    def getKeyIv(self):
        return base64.b64encode(self.key).decode("utf-8"), base64.b64encode(self.iv).decode("utf-8")


    def getRepr(self):
        return {"name":self.name, "description":self.descript, "serialNum":self.serialNum, "time":str(self.time)}