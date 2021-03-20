import os
import json
import websockets
import asyncio
import threading
from datetime import datetime, timedelta

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

#REPOIP='ws://172.18.0.11:7654'
REPOIP='ws://localhost:7654'


class Manager:
    
    def __init__(self):
        self.auctions={} # auctionkey: {limituser:...,userbids:...,validation:..., manipulation:...,users:{user1:nBids, ....}}
        self.manipulation_threads={} # username: amount_limit, step
        self.auct_manip={} #auct:  manipthread

    async def process(self, jsonData, repo):
        with open("repository_public_key.pem", "rb") as repository_public_key_file:
            with open("manager_public_key.pem", "rb") as manager_public_key_file:
                with open("manager_private_key.pem", "rb") as manager_private_key_file:
                    repository_public_key = serialization.load_pem_public_key(repository_public_key_file.read(), backend=default_backend())
                    manager_public_key = serialization.load_pem_public_key(manager_public_key_file.read(), backend=default_backend())
                    manager_private_key = serialization.load_pem_private_key(manager_private_key_file.read(), password=b"SIO_85048_85122", backend=default_backend())
                    

                    file=open("managerLog.txt", "a")
                    file.write(str(datetime.now())+"  --  ")
                    file.write(jsonData)
                    file.write("\n")
                    file.close()


                    data=json.loads(jsonData)
                    action=data["action"]

                    if action=="1": #create auction
                        validation_func = data["auction"]["validation"]
                        manipulation_func = data["auction"]["manipulation"]
                        if (validation_func=="" or syntaticValidation(validation_func)) and (manipulation_func=="" or syntaticValidation(manipulation_func)):
                            self.auctions[data["auction"]["serialNum"]]={"bids":[],"limitUsers":data["auction"]["limitusers"],"userBids":data["auction"]["userbids"],"validation":validation_func,"manipulation":manipulation_func, "users":{}}
                        else:
                            return '{"status":1, "error":"Unable to create auction due to unacceptable behaviour of the validation/manipulation functions."}'

                    #elif action=="2": #end auction
                    #    if data["auction"]["serialNum"] in self.auctions:
                    #        del self.auctions[data["auction"]["serialNum"]]
                        
                    elif action=="10": #bid validation
                        bid=data["bid"]
                        # check if bid passes the validation function (if applicable)
                        if self.auctions[bid["auction"]]["validation"] != "":
                            validationResult={}
                            exec(self.auctions[bid["auction"]]["validation"], {"bid_user":bid["user"], "bid_amount":bid["amount"]}, validationResult)
                            if not validationResult["result"]:
                                return '{"status":1, "error":"Your bid failed the auction\'s validation step."}'
                        # make bid
                        if bid["user"] in self.auctions[bid["auction"]]["users"].keys(): # if user has already done a previous bid
                            # if auction accepts more bids from the same user
                            if (self.auctions[bid["auction"]]["users"][bid["user"]] < self.auctions[bid["auction"]]["userBids"]) or self.auctions[bid["auction"]]["userBids"]==-1:
                                self.auctions[bid["auction"]]["users"][bid["user"]]+=1
                            else:
                                return '{"status":1, "error":"You are no longer allowed to make bids on this auction."}'
                        else: # if it's user's first bid
                            # if auction accepts more users
                            if (len(self.auctions[bid["auction"]]["users"].keys()) < self.auctions[bid["auction"]]["limitUsers"]) or self.auctions[bid["auction"]]["limitUsers"]==-1: 
                                self.auctions[bid["auction"]]["users"][bid["user"]]=1
                            else:
                                return '{"status":1, "error":"This auction does not accept more clients."}'
                        self.auctions[bid["auction"]]["bids"].append(bid)
                        return '{"status":0}'

                    elif action=="11": #subscription
                        bid=data["bid"]
                        # start a thread dedicated to the manipulation of that bid (if applicable)
                        if self.auctions[bid["auction"]]["manipulation"] != "":
                            self.manipulation_threads[bid["user"]] = (data["amount_limit"],data["amount_step"])
                            thread=threading.Thread(target=self.launchManipulationThread, args=(bid, manager_public_key,repository_public_key, manager_private_key))
                            if bid["auction"] not in self.auct_manip.keys():
                                self.auct_manip[bid["auction"]]=[]
                            self.auct_manip[bid["auction"]].append(thread)
                            thread.start()
                            return '{"status":0}'
                        else:
                            return '{"status":1, "error":"No manipulation function. This auction does not support subscriptions."}'

                    jsonData = json.loads(jsonData)
                    jsonData["key"] = manager_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
                    outdata = encryptMsg(json.dumps(jsonData), repository_public_key)
                    await repo.send(outdata)

                    response = await repo.recv()
                    symmetric_key, symmetric_iv, out = decryptMsg(response,manager_private_key)

                    if action=="2":
                        jdata=json.loads(out)
                        if jdata["status"]==0:
                            if data["auction"]["serialNum"] in self.auctions:
                                del self.auctions[data["auction"]["serialNum"]]
                                if data["auction"]["serialNum"] in self.auct_manip.keys():
                                    for x in self.auct_manip[data["auction"]["serialNum"]]:
                                        x.join(0)

                    return out

    def launchManipulationThread(self, bid,manager_public_key,repository_public_key, manager_private_key):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.manipulationThread(bid,manager_public_key,repository_public_key, manager_private_key))


    async def manipulationThread(self,client_bid,manager_public_key,repository_public_key, manager_private_key):
        async with websockets.connect(REPOIP) as repo:
            try:
                client_name = client_bid["user"]
                client_amount = client_bid["amount"]
                auction = client_bid["auction"]
                auction_manipulation_func = self.auctions[auction]["manipulation"]
                auction_bid_count = len(self.auctions[auction]["bids"])
                while auction in self.auctions: # while auction not finished
                    client_amount_limit,client_amount_step = self.manipulation_threads[client_name]
                    if len(self.auctions[auction]["bids"]) > auction_bid_count:
                        auction_bid_count = len(self.auctions[auction]["bids"])
                        bid_user = self.auctions[auction]["bids"][len(self.auctions[auction]["bids"])-1]["user"]
                        if bid_user != client_name:
                            auction_amount = self.auctions[auction]["bids"][len(self.auctions[auction]["bids"])-1]["amount"]
                            modificationResult = {}
                            exec(auction_manipulation_func, {'auction_amount':auction_amount,'client_amount':client_amount,'client_amount_limit':client_amount_limit,'client_amount_step':client_amount_step}, modificationResult)
                            if modificationResult["result"] > client_amount_limit:
                                return '{"status":1, "error":"Auction creator violated your conditions (your amount limit was surpassed)."}'
                            if auction_amount > client_amount_limit:
                                break

                            print(modificationResult["result"])
                            message={"action":"8", "bid":{"auction":auction, "user": client_name,"amount":modificationResult["result"], "time":str(datetime.now())}}
                            message["key"] = manager_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
                            data = encryptMsg(json.dumps(message), repository_public_key)
                            await repo.send(data)
                            response = await repo.recv()
                            symmetric_key, symmetric_iv, out = decryptMsg(response,manager_private_key)
                            print(out)

                del self.manipulation_threads[client_name]
            except:
                pass

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
    print(message.decode("utf-8"))

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

def syntaticValidation(code):
    # Forbidden words:
    if "import" in code or "sys" in code or "open" in code or "exec" in code or "self." in code or "path" in code or "dir" in code:
        return False
    # Function definition in the beggining of the string (with only 1 'def'!) 
    i = code.find("def")
    if i == -1:
        return False
    else:
        if i != 0:
            return False
        i2 = code.find("def", i+1)
        if i2 != -1:
            return False
    # Function name and its only argument:
    a = code.find("def validate(bid_user, bid_amount)")
    if a == -1:
        a = code.find("def manipulate(auction_amount,client_amount,client_amount_limit,client_amount_step)")
        if a == -1:
            return False
    return True
