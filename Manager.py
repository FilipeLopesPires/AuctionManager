import json
import websockets
import asyncio
from datetime import datetime, timedelta

class Manager:
    
    def __init__(self):
        self.auctions={} # auctionkey: {limituser:...,userbids:...,validation:...,users:{user1:nBids, ....}}

    async def process(self, jsonData, repo):
        data=json.loads(jsonData)
        action=data["action"]
        if action=="1":#create auction
            self.auctions[data["auction"]["serialNum"]]={"limitUsers":data["auction"]["limitusers"],"userBids":data["auction"]["userbids"],"validation":data["auction"]["validation"], "users":{}}
            await repo.send(jsonData)
            response=await repo.recv()
        elif action=="2":#end auction
            del self.auctions[data["auction"]["serialNum"]]
            await repo.send(jsonData)
            response=await repo.recv()
        elif action=="10":
            bid=data["bid"]
            #if self.auctions[bid["auction"]]["validation"] != "":
                # if validation fails return false !!!!!!!!!!!!!!!!!!!!!!!!!check how to do validation!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
            if bid["user"] in self.auctions[bid["auction"]]["users"].keys():
                if self.auctions[bid["auction"]]["users"][bid["user"]] < self.auctions[bid["auction"]]["userBids"]:
                    self.auctions[bid["auction"]]["users"][bid["user"]]+=1
                    return "1"
                return "0"
            else:
                if len(self.auctions[bid["auction"]]["users"].keys()) < self.auctions[bid["auction"]]["limitUsers"]:
                    self.auctions[bid["auction"]]["users"][bid["user"]]=1
                    return "1"
                else:
                    return "0"

        return response
