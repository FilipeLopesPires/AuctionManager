import os
import json
import asyncio
import websockets

from Repository import Repository

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

repo = Repository()

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

    jsonData = json.loads(message.decode("utf-8"))
    client_public_key = jsonData["key"]
    del jsonData["key"]

    return symmetric_key, symmetric_iv, client_public_key, json.dumps(jsonData)


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



async def sioRepository(websocket, path):
    with open("repository_private_key.pem", "rb") as repository_private_key_file:
        repository_private_key = serialization.load_pem_private_key(repository_private_key_file.read(), password=b"SIO_85048_85122", backend=default_backend())

        while True:
            request = await websocket.recv()
            
            symmetric_key, symmetric_iv, client_public_key_str, data = decryptMsg(request, repository_private_key)

            client_public_key = serialization.load_pem_public_key(
                str.encode(client_public_key_str),
                backend=default_backend()
            )

            response = await repo.process(data,client_public_key)

            out = encryptMsg(response, client_public_key)

            await websocket.send(out)

start_server = websockets.serve(sioRepository, 'localhost', 7654)
#start_server = websockets.serve(sioRepository, '0.0.0.0', 7654)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
