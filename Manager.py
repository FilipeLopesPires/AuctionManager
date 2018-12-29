import os
import json
import websockets
import asyncio
from datetime import datetime, timedelta

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class Manager:
    
    def __init__(self):
        self.auctions={} # auctionkey: {limituser:...,userbids:...,validation:..., modification:...,users:{user1:nBids, ....}}

    async def process(self, jsonData, repo):
        with open("repository_public_key.pem", "rb") as repository_public_key_file:
            with open("manager_public_key.pem", "rb") as manager_public_key_file:
                with open("manager_private_key.pem", "rb") as manager_private_key_file:
                    repository_public_key = serialization.load_pem_public_key(repository_public_key_file.read(), backend=default_backend())
                    manager_public_key = serialization.load_pem_public_key(manager_public_key_file.read(), backend=default_backend())
                    manager_private_key = serialization.load_pem_private_key(manager_private_key_file.read(), password=b"SIO_85048_85122", backend=default_backend())
                    data=json.loads(jsonData)
                    action=data["action"]

                    if action=="1": #create auction
                        validation_func = data["auction"]["validation"]
                        manipulation_func = data["auction"]["manipulation"]
                        if (validation_func=="" or syntaticValidation(validation_func)) and (manipulation_func=="" or syntaticValidation(manipulation_func)):
                            self.auctions[data["auction"]["serialNum"]]={"limitUsers":data["auction"]["limitusers"],"userBids":data["auction"]["userbids"],"validation":validation_func,"manipulation":manipulation_func, "users":{}}
                        else:
                            return '{"status":1}'

                    elif action=="2": #end auction
                        if data["auction"]["serialNum"] in self.auctions:
                            del self.auctions[data["auction"]["serialNum"]]
                        
                    if action=="10":   #bid validation
                        bid=data["bid"]
                        #if self.auctions[bid["auction"]]["validation"] != "":
                            # if validation fails return false!!!!!!!!! check how to do validation!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        if bid["user"] in self.auctions[bid["auction"]]["users"].keys():
                            if (self.auctions[bid["auction"]]["users"][bid["user"]] < self.auctions[bid["auction"]]["userBids"]) or self.auctions[bid["auction"]]["userBids"]==-1:
                                self.auctions[bid["auction"]]["users"][bid["user"]]+=1
                                return '{"status":0}'
                            return '{"status":1}'
                        else:
                            if (len(self.auctions[bid["auction"]]["users"].keys()) < self.auctions[bid["auction"]]["limitUsers"]) or self.auctions[bid["auction"]]["limitUsers"]==-1:
                                self.auctions[bid["auction"]]["users"][bid["user"]]=1
                                return '{"status":0}'
                            else:
                                return '{"status":1}'

                    jsonData = json.loads(jsonData)
                    jsonData["key"] = manager_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
                    data = encryptMsg(json.dumps(jsonData), repository_public_key)
                    await repo.send(data)

                    response = await repo.recv()
                    symmetric_key, symmetric_iv, out = decryptMsg(response,manager_private_key)

                    return out

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
    print("now validating code...")
    # Forbidden words:
    if "import" in code or "sys" in code or "path" in code or "dir" in code:
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
    a = code.find("validate(bid)")
    if a == -1:
        return False
    return True