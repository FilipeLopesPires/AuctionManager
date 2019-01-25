import json
from datetime import datetime

class FirstBlock:
    def __init__(self, name, descript, time, serialNum, minimumValue, marginValue, startingValue, validation, modification):
        self.name=name
        self.serialNum=serialNum
        self.descript=descript
        self.time=datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        self.highestBidValue=minimumValue
        self.minimumValue=minimumValue
        self.marginValue=marginValue
        self.validation=validation
        self.modification=modification
        self.startingValue=startingValue

    def addCheckSum(self, check):
        self.checksumUntilNow=check

    def getRepr(self):
        return {"name":self.name, "descript":self.descript, "time":self.time, "serialNum":self.serialNum, "minimumValue":self.minimumValue, "marginValue":self.marginValue, "startingValue":self.startingValue, "validation":self.validation, "modification":self.modification}