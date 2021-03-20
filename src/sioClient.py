import os
import json
import base64
import asyncio
import pickle
import websockets
from datetime import datetime, timedelta
import PyKCS11
import binascii
import pickle

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography import x509
from cryptography.x509 import oid

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





#CERTIFICATES

try:
    lib = '/usr/local/lib/libpteidpkcs11.so'

    pkcs11 = PyKCS11.PyKCS11Lib()
    pkcs11.load(lib)

    all_attr = list(PyKCS11.CKA.keys())
    all_attr = [e for e in all_attr if isinstance(e, int)] # filter attributes

    slots = pkcs11.getSlotList()
    slot = slots[0]

    session = pkcs11.openSession(slot)

except:
    print("No Reader inserted.")
    quit()



certificates = {}
def loadVerifiedCert(cert):
    if cert.not_valid_before < datetime.now() and cert.not_valid_after > datetime.now():
        certificates[cert.subject] = cert
        return True
    return False
def loadCCDir():
    try:
        for ob in session.findObjects([(PyKCS11.CKA_CLASS, 1)]):
            attr = session.getAttributeValue(ob, all_attr)
            attr = dict(zip(map(PyKCS11.CKA.get, all_attr), attr))
            c = x509.load_der_x509_certificate(bytes(attr['CKA_VALUE']), default_backend())
            r=loadVerifiedCert(c)
    except:
        print("No SmartCard inserted.")
        quit()

def loadDirPem(path):
    for d in os.scandir(path):
        if d.is_file():
            c = x509.load_pem_x509_certificate(open(d,'rb').read(), default_backend())
            r=loadVerifiedCert(c)
def loadDirDer(path):
    for d in os.scandir(path):
        if d.is_file():
            c = x509.load_der_x509_certificate(open(d,'rb').read(), default_backend())
            r=loadVerifiedCert(c)
def buildChain(cert):
    ret = []
    ret.append(cert)
    aux = certificates[cert.issuer]
    while aux.subject != aux.issuer:
        ret.append(aux)
        aux = certificates[aux.issuer]
    ret.append(aux)
    return ret


loadCCDir()
loadDirPem('/etc/ssl/certs')
loadDirDer('cert')


try:
    sign_cert = session.findObjects([(PyKCS11.CKA_CLASS, 1),(PyKCS11.CKA_LABEL, 'CITIZEN SIGNATURE CERTIFICATE')])[0]
    attr = session.getAttributeValue(sign_cert, all_attr)
    attr = dict(zip(map(PyKCS11.CKA.get, all_attr), attr))
    cert = x509.load_der_x509_certificate(bytes(attr['CKA_VALUE']), default_backend())

    chain=buildChain(cert)
    serChain=[base64.b64encode(x.public_bytes(serialization.Encoding.PEM)).decode("utf-8") for x in chain]

    cc_private_key = session.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),(PyKCS11.CKA_LABEL, 'CITIZEN SIGNATURE KEY')])[0]
    cc_mechanism = PyKCS11.Mechanism(PyKCS11.CKM_SHA1_RSA_PKCS,None)
except:
    print("No SmartCard inserted.")
    quit()


#CLIENT_KEYS

client_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )

client_public_key = client_private_key.public_key()



async def interface():
        with open("repository_public_key.pem", "rb") as repository_public_key_file:
            with open("manager_public_key.pem", "rb") as manager_public_key_file:
                # Security Keys
                manager_public_key = serialization.load_pem_public_key(manager_public_key_file.read(), backend=default_backend())
                repository_public_key = serialization.load_pem_public_key(repository_public_key_file.read(), backend=default_backend())
                
                #enter system
                print("\nWelcome to 'Blockchain-Based Auction Manager'!\nThis program was developed by Filipe Pires (85122) and Joao Alegria (85048) for the discipline SIO 2018/19.\n")
                
                entered=False
                while not entered:
                    user=input("Type in your username: ")
                    signature = bytes(session.sign(cc_private_key, bytes(user, "utf-8"), cc_mechanism))
                    message = {"action":"9", "user": user, "signature": base64.b64encode(signature).decode("utf-8"), "chain": serChain}
                    message["key"]=client_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
                    out = encryptMsg(json.dumps(message), repository_public_key)


                    async with websockets.connect('ws://localhost:7654') as websocket2: # sioRepository
                        await websocket2.send(out)

                        # Receive and decrypt response message
                        response = await websocket2.recv()
                        symmetric_key, symmetric_iv, data = decryptMsg(response, client_private_key)
                        print(data)
                        entered=True if json.loads(data)["status"]==0 else False
                        websocket2.close()


                message={}

                # User Interface Menu
                act = input("0-Leave\n1-Create Auction\n2-Close Auction\n3-List Auctions\n4-List Bids of Auction\n5-List My Bids\n6-Check Outcome\n7-Make Bid\nAction: ")
                while act!="0":
                    if act!="1" and act!="2":
                        message={"action":act}
                        if act=="4" or act=="6":
                            message["auction"]={"serialNum":input("*Serial Number: ")}
                        if act=="5":
                            message["user"]=user
                        if act=="7":
                            # Send encrypted message (specifying the target auction)
                            auction = input("*Auction: ")
                            message["auction"] = auction
                            message["key"]=client_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
                            

                            async with websockets.connect('ws://localhost:7654') as websocket2: # sioRepository
                                out = encryptMsg(json.dumps(message), repository_public_key)
                                await websocket2.send(out)
                                # Receive and decrypt response message
                                response = await websocket2.recv()
                                symmetric_key, symmetric_iv, data = decryptMsg(response, client_private_key)
                                data = json.loads(data)
                                websocket2.close()


                            if "status" not in data.keys():

                                # Fill in bid form
                                if "current_value" in data.keys():
                                    if "margin_value" in data.keys():
                                        print("This is an auction of Reversed type with a margin value of: " + str(data["margin_value"]) + " and a minimum value of: " + str(data["minimum_value"]) + ".\nThe auction winning bid is currently at value: " + str(data["current_value"]))
                                    else:
                                        print("This is an auction of English type.\n The auction winning bid is currently at value: " + str(data["current_value"]))
                                else:
                                    print("This is an auction of Blind type with a minimum value of: " + str(data["minimum_value"]) + ".")
                                message["bid"]={"auction": auction,"user": user,"amount":float(input("*Amount: ")), "time":str(datetime.now())}
                                

                                #add signature
                                signature = bytes(session.sign(cc_private_key, bytes(message["bid"]["user"], "utf-8"), cc_mechanism))
                                message["bid"]["signature"]=base64.b64encode(signature).decode("utf-8")


                                allow_manipulation = input("*Do you want your bid value to adapt to new bids? (y/n): ")
                                if allow_manipulation=="y" or allow_manipulation=="Y":
                                    message["amount_limit"] = float(input("Amount limit: "))
                                    message["amount_step"] = float(input("Amount step: "))

                                # Solve Crypto Puzzle
                                puzzle = base64.b64decode(data["cryptopuzzle"])
                                print("To solve this puzzle, your checksum must beggin with: " + base64.b64encode(puzzle).decode("utf-8"))
                                proposals = set([])
                                while True:
                                    random_bytes = os.urandom(16)
                                    message["bid"]["cryptoanswer"] = base64.b64encode(random_bytes).decode("utf-8")
                                    serialized_message = str.encode(json.dumps(message["bid"], sort_keys=True))
                                    concat = serialized_message + random_bytes
                                    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
                                    digest.update(concat)
                                    checksum = digest.finalize()
                                    checksum = checksum[0:len(puzzle)]
                                    if puzzle==checksum:
                                        proposals.add((checksum,random_bytes))
                                        break
                                    else:
                                        if len(proposals)<4:
                                            proposals.add((checksum,random_bytes))

                                message["bid"]["cryptoanswer"] = base64.b64encode(b"").decode("utf-8")

                                for p in proposals:
                                    answer = input("Puzzle - " + base64.b64encode(puzzle).decode("utf-8") + " | Checksum - " + base64.b64encode(p[0]).decode("utf-8") + "\nDoes it solve the puzzle? (y/n): ")
                                    if answer=="y" or answer =="Y":
                                        message["bid"]["cryptoanswer"] = base64.b64encode(p[1]).decode("utf-8")
                                        break


                        async with websockets.connect('ws://localhost:7654') as websocket2: # sioRepository
                            # Send encrypted message
                            message["key"]=client_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
                            out = encryptMsg(json.dumps(message), repository_public_key)
                            await websocket2.send(out)

                            # Receive and decrypt response message
                            response = await websocket2.recv()
                            symmetric_key, symmetric_iv, data = decryptMsg(response, client_private_key)
                            print(data)
                            websocket2.close()

                        file=open(user+"Log.txt", "a")
                        file.write(str(datetime.now())+"  --  ")
                        file.write(data)
                        file.write("\n")
                        file.close()


                        jdata=json.loads(data)
                        if "status" not in jdata.keys():
                            if act=="7":
                                try:
                                    repository_public_key.verify(base64.b64decode(jdata["signature"]),bytes(jdata["user"],"utf-8"),padding.PKCS1v15(),hashes.SHA1())
                                    print("Signature Valid")
                                except:
                                    print("Signature Invalid")


                            if act=="4":
                                dcrpt = input("Do you want to decrypt the chain?(y/n)->")
                                if dcrpt == "y" or dcrpt =="Y":
                                    chiperbids=json.loads(data)["chain"]
                                    chiperkey=base64.b64decode(json.loads(data)["key"])
                                    chiperiv=base64.b64decode(json.loads(data)["iv"])
                                    clearBids=[]

                                    startIndex=len(chiperbids)-2
                                    for i in range(len(chiperbids)-1):
                                        actualIndex=startIndex-i

                                        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
                                        digest.update(bytes(chiperbids[actualIndex-1]))
                                        checksum = digest.finalize()

                                        serializedBid = bytes(chiperbids[actualIndex])
                                        thisIv=checksum[0:16] if actualIndex!=0 else chiperiv

                                        xorValue=[]
                                        for i in range(len(serializedBid)):
                                            xorValue.append(serializedBid[i] ^ thisIv[i%len(thisIv)])

                                        xorValue=bytes(xorValue)


                                        cipher = Cipher(algorithms.AES(chiperkey), modes.OFB(thisIv), backend=default_backend())
                                        decryptor = cipher.decryptor()
                                        ct = decryptor.update(xorValue) + decryptor.finalize()
                                        bid = pickle.loads(ct)

                                        clearBids.append(bid.getRepr())
                                    clearBids.reverse()
                                    print(clearBids)



                    else:
                        message={"action":act}
                        if act=="1": # Auction creation
                            print("Fill in the form below to create an auction (* means the field is mandatory)")
                            atype = input("*Auction Type (1-English Auction, 2-Reversed Auction, 3-BlindAuction): ")
                            minimumV = float(input("*Minimum Value: "))
                            if atype=="2":
                                startingV = float(input("*Starting Value: "))
                                marginV = float(input("*Margin Value: "))
                                message["auction"]={"type":atype,"minv":minimumV,"startv":startingV,"marginv":marginV,"name":input("*Name: "),"descr":input("*Description: "),"serialNum":input("*Serial Number: "), "time":str(datetime.now()+timedelta(minutes=int(input("*Valid Minutes: "))))}
                            else:
                                message["auction"]={"type":atype,"minv":minimumV,"name":input("*Name: "),"descr":input("*Description: "),"serialNum":input("*Serial Number: "), "time":str(datetime.now()+timedelta(minutes=int(input("*Valid Minutes: "))))}
                            
                            difficulty=input("CryptoPuzzle difficulty(1..): ")
                            if difficulty=="":
                                difficulty="1"
                            limitUsers=input("Limit of Users: ")
                            if limitUsers=="":
                                limitUsers="-1"
                            usersBids=input("Limit of Bids per User: ")
                            if usersBids=="":
                               usersBids="-1"
                            message["auction"]["limitusers"]=int(limitUsers)
                            message["auction"]["userbids"]=int(usersBids)
                            message["auction"]["difficulty"]=int(difficulty)

                            
                            print("Validation function (write a function called 'validate' accepting two arguments 'bid_user' and 'bid_amount' with Python3 syntax, write 'end' to finish or skip this step):")
                            validation_func = ""
                            input_str = input()
                            while input_str != "end":
                                validation_func += input_str + "\n"
                                input_str = input()
                            if validation_func != "":
                                validation_func += "\nresult=validate(bid_user, bid_amount)\n"
                                #print(validation_func)
                                #exec(validation_func, {'bid':bid_obj})
                            message["auction"]["validation"]=validation_func
                            
                            print("Manipulation functions (write a function called 'manipulate' accepting four arguments 'auction_amount','client_amount','client_amount_limit','client_amount_step' with Python3 syntax, write 'end' to finish or skip this step):")
                            manipulation_func = ""
                            input_str = input()
                            while input_str != "end":
                                manipulation_func += input_str + "\n"
                                input_str = input()
                            if manipulation_func != "":
                                manipulation_func += "\nresult=manipulate(auction_amount,client_amount,client_amount_limit,client_amount_step)\n"
                                #print(manipulation_func)
                                #exec(manipulation_func, {'bid':bid_obj})
                            message["auction"]["manipulation"]=manipulation_func
                            message["user"]=user

                            #add signature
                            signature = bytes(session.sign(cc_private_key, bytes(message["user"], "utf-8"), cc_mechanism))
                            message["signature"]=base64.b64encode(signature).decode("utf-8")

                            
                        if act=="2":
                            message["auction"]={"serialNum":input("*Serial Number: ")}
                            message["user"]=user


                        async with websockets.connect('ws://localhost:8765') as websocket1: # sioManager
                            # Send encrypted message
                            message["key"]=client_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
                            out = encryptMsg(json.dumps(message), manager_public_key)
                            await websocket1.send(out)
                            
                            # Receive and decrypt response message
                            response = await websocket1.recv()
                            symmetric_key, symmetric_iv, data = decryptMsg(response, client_private_key)
                            print(data)
                            websocket1.close()

                        file=open(user+"Log.txt", "a")
                        file.write(str(datetime.now())+"  --  ")
                        file.write(data)
                        file.write("\n")
                        file.close()

                    act = input("0-Leave\n1-Create Auction\n2-Close Auction\n3-List Auctions\n4-List Bids of Auction\n5-List My Bids\n6-Check Outcome\n7-Make Bid\nAction: ")


                #LOGOUT(remove name)
                message={"action":"0"}
                message["user"]=user

                async with websockets.connect('ws://localhost:7654') as websocket2: # sioRepository
                    # Send encrypted message
                    message["key"]=client_public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
                    out = encryptMsg(json.dumps(message), repository_public_key)
                    await websocket2.send(out)

                    # Receive and decrypt response message
                    response = await websocket2.recv()
                    symmetric_key, symmetric_iv, data = decryptMsg(response, client_private_key)
                    print(data)

                    websocket2.close()

                file=open(user+"Log.txt", "a")
                file.write(str(datetime.now())+"  --  ")
                file.write(data)
                file.write("\n")
                file.close()


asyncio.get_event_loop().run_until_complete(interface())
