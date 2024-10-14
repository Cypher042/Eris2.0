from pymongo import MongoClient
from config import *
from nextcord import Interaction, Embed
from json import loads
import os

class Database:

    def __init__(self):
        client = MongoClient("mongodb://localhost:27017")
        db = client['db']
        self.users = db['users']
        self.cotd = db['cotd']
        try:
            self.ongoing_cotd = self.cotd.find().sort("day", -1).limit(1)[0]
        except IndexError:
            self.ongoing_cotd = dict(day=-1, flag="", hint="")
        self.day = self.ongoing_cotd.get("day")
        self.flag = self.ongoing_cotd.get("flag")
        self.hint = self.ongoing_cotd.get("hint")
        if self.hint is None: self.hint = ""
        if self.flag is None: self.flag = ""
        if self.day is None: self.day = -1

    def isUserPresent(self, uid):
        return self.users.count_documents({"_id":uid})

    def getHint(self):
        return None if len(self.hint) == 0 else self.hint

    def updateHint(self, hint : str | None = None):
        self.hint = "" if hint is None else hint
        self.cotd.update_one({"day":self.day}, {"$set":{"hint": self.hint}})

    def register(self, interaction: Interaction):
        uid = interaction.user.id
        nick = interaction.user.nick
        name = interaction.user.name
        try:
            presence = self.users.count_documents({"_id":uid}, limit=1)
            if presence == 0:
                insert = dict(_id=uid, nick=nick, name=name, points=0, messages=list())
                self.users.insert_one(insert)
                return 0
            else:
                return 1
        except:
            return -1
    
    def get_flag(self):
        return self.flag
    
    # def check_repeated_submit(self, interaction: Interaction):
    #     user = self.cotd.find_one({"day":self.day})

    #     if not self.isUserPresent(interaction.user.id):
    #         self.register(interaction)

    #     if interaction.user.id in user.get("solves"):
    #         return 1
    #     else:
    #         self.cotd.update_one({"day":self.day}, {'$push':{'messages': interaction.user.id}})
    #         return 0
    
    def update_status(self):
        self.users.update_many({}, {'$set': {'messages': list()}})

    def scoreboard(self):
        return list(self.users.find({}, {"name": 1, "points": 1}))
    
    def add_message(self, interaction, messageid):
        self.users.update_one({"_id":interaction.user.id}, {"$push":{"messages":messageid}})
        return 0

    def add_cotd(self, flag):
        self.day = self.day + 1
        self.cotd.insert_one(dict(day=self.day, flag=flag, hint="", solves=list()))
        self.flag = flag
        self.hint = None
        self.update_status()
        return self.day

    def get_scoreboard(self):
        lst = list(self.users.find({}, {"_id":0, "name":1, "points":1}))
        lst = [str(i["points"]) + " " + i["name"] for i in lst]
        lst = sorted(lst)
        return lst[::-1]

    def update_flag(self, flag):
        self.flag = flag
        self.cotd.update_one({"day":self.day}, {"$set": {"flag":flag}})

    def accept_response(self, uid):
        if len(self.users.find_one({"_id":uid}).get("messages")) > 2: return 1
        else : return 0

    def get_message_user(self, messageid):
        lst = self.users.find_one({"messages":{"$in":[messageid]}})
        return lst.get("_id"), lst.get("messages")
    
    def increase_score(self, userid):
        solves = self.cotd.find_one({"day" : self.day}).get("solves")
        if userid not in solves:
            self.cotd.update_one({"day": self.day}, {"$addToSet" : {"solves": userid}})
            self.users.update_one({"_id":userid}, {"$inc": {"points":1}})
    
    def remove_message(self, userid, messageid):
        self.users.update_one({"_id":userid}, {"$pull":{"messages": messageid}})

    def submit_flag(self, interaction):

        info = self.cotd.find_one({"day": self.day})
        if interaction.user.id in info.get("solves"):
            return 1
        else:
            return 0
