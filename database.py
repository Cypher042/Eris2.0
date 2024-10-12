from pymongo import MongoClient
from config import *
from nextcord import Interaction, Embed
from json import loads
import os

class Database:
    def __init__(self):
        client = MongoClient(MONGO_URI)
        db = client['db']
        self.users = db['users']
        self.flag = "heybond"

    def isUserPresent(self, uid):
        return self.users.find_one({"_id":uid})

    def register(self, interaction: Interaction):
        uid = interaction.user.id
        nick = interaction.user.nick
        name = interaction.user.name
        try:
            presence = self.users.count_documents({"_id":uid}, limit=1)
            if presence == 0:
                insert = dict(uid=uid, nick=nick, name=name, points=0)
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