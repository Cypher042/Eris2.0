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
        self.flag = open(".flag").read().strip()
        self.hint = open(".hint").read().strip()

    def isUserPresent(self, uid):
        return self.users.find_one({"_id":uid})

    def getHint(self):
        return None if len(self.hint) == 0 else self.hint

    def updateHint(self, hint : str | None = None):
        f = open(".hint", "w") 
        hint = "" if hint is None else hint
        f.write(hint)
        f.close()
        self.hint = hint

    def register(self, interaction: Interaction):
        uid = interaction.user.id
        nick = interaction.user.nick
        name = interaction.user.name
        try:
            presence = self.users.count_documents({"_id":uid}, limit=1)
            if presence == 0:
                insert = dict(_id=uid, nick=nick, name=name, points=0, messages=list(), submitted=False)
                self.users.insert_one(insert)
                return 0
            else:
                return 1
        except:
            return -1
    
    def get_flag(self):
        return self.flag
    
    def check_repeated_submit(self, interaction: Interaction):
        user = self.users.find_one({"_id":interaction.user.id})

        if not self.isUserPresent(interaction.user.id):
            self.register(interaction)

        if user.get["submitted"] is True:
            return 1
        else:
            self.users.update_one({"_id":interaction.user.id}, {'$set':{'submitted': True}})
            return 0
    
    def update_status(self):
        self.users.update_many({}, {'$set': {'submitted': False}})

    def scoreboard(self):
        return list(self.users.find({}, {"name": 1, "points": 1}))
    
    def add_message(self, interaction, messageid):
        info = self.users.find_one({"_id":interaction.user.id})
        if len(info["messages"]) > 3: 
            return 1
        temp = info["messages"] 
        temp.append(messageid)
        self.users.update_one({"_id":interaction.user.id}, {"$set":{"messages":temp}})
        return 0

    def get_scoreboard(self):
        lst = list(self.users.find({}, {"_id":0, "name":1, "points":1}))
        lst = [str(i["points"]) + " " + i["name"] for i in lst]
        lst = sorted(lst)
        return lst[::-1]

    def update_flag(self, flag):
        self.flag = flag
        f = open(".flag", "w")
        f.write(flag)
        f.close()

    def get_message_user(self, messageid):
        lst = self.users.find()
        for i in lst:
            if messageid in i["messages"]:
                return i["_id"], i["messages"]
        return None, None
    
    def increase_score(self, userid):
        hasSubmitted = self.users.find_one({"_id":userid}, {"submitted":1})
        if hasSubmitted["submitted"] is False:
            self.users.update_one({"_id":userid}, {"$inc": {"points":1}, "$set":{"submitted":True}})
    
    def remove_message(self, userid, messageid):
        lst = self.users.find_one({"_id":userid})
        i = lst["messages"]
        i.remove(messageid) if messageid in i else i
        if i is None: i=list()
        self.users.update_one({"_id":userid}, {"$set":{"messages": i}})

    def submit_flag(self, interaction):
        if not self.isUserPresent(interaction.user.id):
            self.register(interaction)
        info = self.users.find_one({"_id": interaction.user.id})
        if info["submitted"] is True:
            return 1
        else:
            return 0
