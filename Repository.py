import os
import json
import base64
import asyncio
import websockets
from datetime import datetime

from EnglishAuction import EnglishAuction
from ReversedAuction import ReversedAuction
from BlindAuction import BlindAuction

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

#MANAGERIP='ws://172.18.0.10:8765'
MANAGERIP='ws://localhost:8765'


class Repository:

    def __init__(self):
        self.users={}
        self.auctions={}
        self.closed={}
        self.puzzles={}

    async def process(self, jsonData, client_public_key):
        file=open("repositoryLog.txt", "a")
        file.write(str(datetime.now())+"  --  ")
        file.write(jsonData)
        file.write("\n")
        file.close()
        data=json.loads(jsonData)
        action=data["action"]
        
        if action=="1":#create auction          ---------receber action e auction->completa
            try:
                pubKeyClient=None
                for num, tup in self.users.items():
                    if tup[0]==data["user"]:
                        pubKeyClient=tup[1]
                if pubKeyClient!=None:
                    pubKeyClient.verify(base64.b64decode(data["signature"]),bytes(data["user"], "utf-8"),padding.PKCS1v15(),hashes.SHA1())
                else:
                    return '{"status":1, "error":"Something wrong with the user."}'
            except:
                return '{"status":1, "error":"Invalid Signature."}'
            if data["auction"] != None:
                auct=data["auction"]
                if auct["serialNum"] in self.auctions.keys() or auct["serialNum"] in self.closed.keys():
                    return '{"status":1, "error":"This serial number already exists."}'
                if auct["type"]=="1":
                	a = EnglishAuction(data["user"],auct["name"], auct["descr"], auct["time"], auct["serialNum"], self, auct["minv"],auct["difficulty"], auct["validation"], auct["manipulation"])
                if auct["type"]=="2":
                	a = ReversedAuction(data["user"],auct["name"], auct["descr"], auct["time"], auct["serialNum"], self, auct["startv"], auct["marginv"], auct["minv"],auct["difficulty"], auct["validation"], auct["manipulation"])
                if auct["type"]=="3":
                	a = BlindAuction(data["user"],auct["name"], auct["descr"], auct["time"], auct["serialNum"], self, auct["minv"], auct["difficulty"], auct["validation"], auct["manipulation"])
                self.auctions[auct["serialNum"]]=a
        
        elif action=="2":#end auction         ---------receber action e auction->serialNum
            if "auction" in data:
                auct=data["auction"]
                if auct["serialNum"] in self.auctions.keys():
                    if data["user"] == self.auctions[auct["serialNum"]].autor:
                        self.auctions[auct["serialNum"]].endAuction()
                        self.closed[auct["serialNum"]]=self.auctions[auct["serialNum"]]
                        del self.auctions[auct["serialNum"]]
                    else:
                        return '{"status":1, "error":"This auction is not yours."}'
                else:
                    return '{"status":1, "error":"This auction does not exist or has already finished."}'
        
        elif action=="3":#list auctions          ---------receber action
            return json.dumps({"opened":[self.auctions[x].getRepr() for x in self.auctions.keys()], "closed":[self.closed[x].getRepr() for x in self.closed.keys()]})
        
        elif action=="4":#list bids of auction         ---------receber action e auction->serialNum
            auct=data["auction"]
            if auct["serialNum"] not in self.closed:
                return '{"status":1, "error":"This auction either does not exist, or you do not have permission to see it, or it is still in progress, if that\'s the case the information will only be available once it is finished."}'
            auctKey, auctIv = self.closed[auct["serialNum"]].getKeyIv()
            return json.dumps({"key": auctKey , "iv": auctIv , "chain": self.closed[auct["serialNum"]].bids})
        
        elif action=="5":#list bids by user --------receber action e user
            user=data["user"]

            liveBids=[self.auctions[x].getBids() for x in self.auctions.keys()]
            deadBids=[self.closed[x].getBids() for x in self.closed.keys()]
            return json.dumps({"bids":[y.getRepr() for x in liveBids for y in x if y.user==user] + [y.getRepr() for x in deadBids for y in x if y.user==user]})
        
        elif action=="6":#get Auction outcome          ---------receber action e auction->serialNum
            auct=data["auction"]

            if auct["serialNum"] not in self.closed:
                return '{"status":1, "error":"This auction does not exist or it is still in progress, if that\'s the case the information will only be available once it is finished."}'

            return self.closed[auct["serialNum"]].getOutcome()
        
        elif action=="7":#make Bid          ---------receber action e bid
            if "bid" in data.keys():
                bid=data["bid"]
                user=bid["user"]

                if "cryptoanswer" in bid.keys() and self.validateCryptoPuzzle(client_public_key, bid, bid["cryptoanswer"]):
                    if "amount_limit" in data:
                        response = await self.subscribe(bid, data["amount_limit"], data["amount_step"])
                        if json.loads(response)["status"]==1:
                            return response
                    if self.users[client_public_key.public_numbers()][0]==bid["user"]:
                        return await self.auctions[bid["auction"]].makeBid(bid, self.users[client_public_key.public_numbers()][1])
                return '{"status":1, "error":"Bid failed cryptopuzzle."}'

            if data["auction"] in self.auctions:
                auction = self.auctions[data["auction"]]
                puzzle_msg = {"cryptopuzzle":self.createCryptoPuzzle(auction, client_public_key)}
                if isinstance(auction,EnglishAuction):
                    puzzle_msg["current_value"] = auction.highestBidValue
                elif isinstance(auction,ReversedAuction):
                    puzzle_msg["current_value"] = auction.lowestBidValue
                    puzzle_msg["margin_value"] = auction.marginValue
                    puzzle_msg["minimum_value"] = auction.minimumValue
                elif isinstance(auction,BlindAuction):
                    puzzle_msg["minimum_value"] = auction.minimumValue
                return json.dumps(puzzle_msg)

            return '{"status":1, "error":"This auction does not exists or it is already closed."}'

        elif action=="8":#make internal Bid          ---------receber action e bid
            if "bid" in data.keys():
                bid=data["bid"]
                return await self.auctions[bid["auction"]].makeBid(data["bid"], None, 1)
            return '{"status":1, "error":"Internal error while updating subscription bid."}'

        elif action=="9":  #enter system
            user=data["user"]
            if client_public_key.public_numbers() in self.users.keys():
                if self.users[client_public_key.public_numbers()][0]!=user:
                    return '{"status":1, "error":"Username already taken. Clients must choose unique usernames."}'
            else:
                if user in [x[0] for x in self.users.values()]:
                    return '{"status":1, "error":"Username already taken. Clients must choose unique usernames."}'

                serChain=data["chain"]
                chain=[x509.load_pem_x509_certificate(base64.b64decode(x), default_backend()) for x in serChain]

                if revokated(chain):
                    return '{"status":1, "error":"Unfortunately your smarthcard path has a revoked certificate."}'
                if not validatePath(chain):
                    return '{"status":1, "error":"Unfortunately your smarthcard path is not valid."}'
                if not correctRoot(chain):
                    return '{"status":1, "error":"Unfortunately your smarthcard path is not signed by the right CA."}'
                if not verifySignature(user,base64.b64decode(data["signature"]),chain):
                    return '{"status":1, "error":"Unfortunately your signature is not valid."}'
                self.users[client_public_key.public_numbers()] = (user, chain[0].public_key())

        elif action=="0":
            if data["user"] in [self.users[x][0] for x in self.users]:
                k=[x for x in self.users if self.users[x][0]==data["user"]][0]
                del self.users[k]
                return '{"status":0, "msg":"Logged Out"}'
            return '{"status":1, "error":"User invalid."}'
            
        return '{"status":0}'


    def end(self, serialNum):
        self.auctions[serialNum].endAuction()
        self.closed[serialNum]=self.auctions[serialNum]
        del self.auctions[serialNum]

    async def validateBid(self, bid):
        async with websockets.connect(MANAGERIP) as man:
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

                        return (True if json.loads(result)["status"]==0 else False)

    async def subscribe(self, bid, amount_limit, amount_step):
        async with websockets.connect(MANAGERIP) as man:
            with open("manager_public_key.pem", "rb") as manager_public_key_file:
                with open("repository_public_key.pem", "rb") as repository_public_key_file:
                    with open("repository_private_key.pem", "rb") as repository_private_key_file:
                        manager_public_key = serialization.load_pem_public_key(manager_public_key_file.read(), backend=default_backend())
                        repository_public_key = serialization.load_pem_public_key(repository_public_key_file.read(), backend=default_backend())
                        repository_private_key = serialization.load_pem_private_key(repository_private_key_file.read(), password=b"SIO_85048_85122", backend=default_backend())

                        out = encryptMsg(json.dumps({'action':'11', 'bid':bid, 'amount_limit':amount_limit, 'amount_step':amount_step, 'key':repository_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")}),manager_public_key)

                        await man.send(out)
                        receive = await man.recv()
                        symmetric_key, symmetric_iv, result = decryptMsg(receive, repository_private_key)
                        return result

    def createCryptoPuzzle(self,auction, client_public_key):
        puzzle = os.urandom(auction.difficulty)
        self.puzzles[client_public_key.public_numbers()] = puzzle
        return base64.b64encode(puzzle).decode("utf-8")

    def validateCryptoPuzzle(self, client_public_key, client_bid, client_cryptoanswer):
        puzzle = self.puzzles[client_public_key.public_numbers()]
        del self.puzzles[client_public_key.public_numbers()]
        serialized_client_bid = str.encode(json.dumps(client_bid, sort_keys=True))
        client_cryptoanswer = base64.b64decode(client_cryptoanswer)
        concat = serialized_client_bid + client_cryptoanswer
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(concat)
        checksum = digest.finalize()
        checksum = checksum[0:len(puzzle)]
        if puzzle==checksum:
            return True
        return False

    def getPrivKey(self):
        with open("repository_private_key.pem", "rb") as repository_private_key_file:
            repository_private_key = serialization.load_pem_private_key(repository_private_key_file.read(), password=b"SIO_85048_85122", backend=default_backend())
            return repository_private_key


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

def revokated(lst):
    rl=[]
    for i in range(4):
        i+=1
        f=open("crl/cc_ec_cidadao_crl00"+str(i)+"_crl.crl","rb")
        data=f.read()
        crl = x509.load_der_x509_crl(data, default_backend())
        for x in crl:
            rl.append(x.serial_number)

    for x in lst:
        if x.serial_number in rl:
            return True
    return False

def validatePath(lst):
    try:
        for i in range(len(lst)):
            index=i
            index2=i+1
            if index==len(lst)-1:
                index2=i
            c1=lst[index]
            c2=lst[index2]
            pub=c2.public_key()
            pub.verify(c1.signature,c1.tbs_certificate_bytes,padding.PKCS1v15(),c1.signature_hash_algorithm)
        return True
    except:
        return False

def correctRoot(lst):
    c = x509.load_der_x509_certificate(open("cert/ECRaizEstado.crt",'rb').read(), default_backend())
    if lst[len(lst)-2]==c and lst[len(lst)-1].subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value=="Baltimore CyberTrust Root":
        return True
    return False


def verifySignature(value, sig, chain):
    pub=chain[0].public_key()
    try:
        pub.verify(sig,bytes(value, "utf-8"),padding.PKCS1v15(),hashes.SHA1())
        return True
    except:
        return False
