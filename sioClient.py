# WS client example

import asyncio
import websockets
import json
from datetime import datetime, timedelta
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

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




async def interface():
    async with websockets.connect('ws://localhost:8765') as websocket1:
        async with websockets.connect('ws://localhost:7654') as websocket2:
            with open("server_public_key.pem", "rb") as server_public_key_file:
                with open("client_public_key.pem", "rb") as client_public_key_file:
                    with open("client_private_key.pem", "rb") as client_private_key_file:
                        with open("symmetric_key.txt", "rb") as symmetric_key_file:
                            server_public_key = serialization.load_pem_public_key(server_public_key_file.read(), backend=default_backend())
                            client_public_key = serialization.load_pem_public_key(client_public_key_file.read(), backend=default_backend())
                            client_private_key = serialization.load_pem_private_key(client_private_key_file.read(), password=b"SIO_85048_85122", backend=default_backend())

                            act = input("0-Leave\n1-Create Auction\n2-Close Auction\n3-List Auctions\n4-List Bids of Auction\n5-List Bids by Client\n6-Check Outcome\n7-Make Bid\nAction: ")
                            while act!="0":
                                if act!="1" and act!="2":
                                    message={"action":act}
                                    if act=="4" or act=="6":
                                        message["auction"]={"serialNum":input("Serial Number: ")}
                                    if act=="5":
                                        message["user"]=input("User: ")
                                    if act=="7":
                                        message["bid"]={"auction": input("Auction: "),"user": input("User: "),"amount":float(input("Amount: ")), "time":str(datetime.now())}
                                    

                                    message["key"]=client_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
                                    

                                    out = encryptMsg(json.dumps(message), server_public_key)

                                    await websocket2.send(out)
                                    response = await websocket2.recv()

                                    symmetric_key, symmetric_iv, data = decryptMsg(response, client_private_key)

                                    print(data)
                                else:
                                    message={"action":act}
                                    if act=="1":
                                        atype = input("Auction Type (1-English Auction, 2-Reversed Auction, 3-BlindAuction): ")
                                        minimumV = float(input("Minimum Value: "))
                                        if atype=="2":
                                            startingV = float(input("Starting Value: "))
                                            marginV = float(input("Margin Value: "))
                                            message["auction"]={"type":atype,"minv":minimumV,"startv":startingV,"marginv":marginV,"name":input("Name: "),"descr":input("Description: "),"serialNum":input("Serial Number: "), "time":str(datetime.now()+timedelta(minutes=int(input("Valid Minutes: "))))}
                                        else:
                                            message["auction"]={"type":atype,"minv":minimumV,"name":input("Name: "),"descr":input("Description: "),"serialNum":input("Serial Number: "), "time":str(datetime.now()+timedelta(minutes=int(input("Valid Minutes: "))))}
                                        limitUsers=input("Limit of Users: ")
                                        if limitUsers=="":
                                            limitUsers="-1"
                                        usersBids=input("Limit of Bids per User: ")
                                        if usersBids=="":
                                           usersBids="-1"
                                        message["auction"]["limitusers"]=int(limitUsers)
                                        message["auction"]["userbids"]=int(usersBids)
                                        message["auction"]["validation"]=input("Validation file: ")
                                    if act=="2":
                                        message["auction"]={"serialNum":input("Serial Number: ")}
                                    await websocket1.send(json.dumps(message))
                                    response = await websocket1.recv()
                                    print(response)
                                act = input("0-Leave\n1-Create Auction\n2-Close Auction\n3-List Auctions\n4-List Bids of Auction\n5-List Bids by Client\n6-Check Outcome\n7-Make Bid\nAction: ")

asyncio.get_event_loop().run_until_complete(interface())
