import nextcord 
from nextcord.ext import commands, menus
from nextcord import Intents, Interaction, Embed, File
from config import * 
from typing import Dict, List, Optional 
from nextcord.ext.commands.errors import MissingAnyRole
from nextcord.utils import escape_markdown
from database import Database

intents = Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
database = Database()

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

class ScoreBoarder(menus.ListPageSource):
    
    def __init__(self, data):
        super().__init__(data, per_page=15)
    
    async def format_page(self, menu, entries):
        desc = "```\n"
        desc += "╔"+"═"*14+"╦"+"═"*20+"╗"
        k=1
        for entry in entries:
            desc+="\n╠"+"═"*14+"╬"+"═"*20+"╣"
            name, score = entry.split()
            desc += "\n║"+name[0:14]+" "*(14-len(name))+"║"+"  "+score+" "*(17)+"║"
        desc += "\n╚"+"═"*14+"╩"+"═"*20+"╝"
        desc += "\n```"
        embed=Embed(title="Here you go!", description=desc, color=nextcord.Color.gold())
        return embed

@bot.slash_command(name="submit_flag", description="Submit the flag!", guild_ids=GID)
async def submit_flag(interaction: Interaction, flag:str):
    await interaction.response.defer()
    ans_flag = database.get_flag()

    if flag is None:
        return await interaction.followup.send(embed=WHAT_YOU_DOING)

    if flag != ans_flag:
        await interaction.followup.send(embed=INCORRECT_FLAG_EMBED)
    else:
        _submit = database.submit_flag(interaction)
        if _submit == 1:
                         
            await interaction.followup.send(embed=REPEATED_SUBMIT_EMBED)
        else:
        
            await interaction.followup.send(embed=ENQUEUE_FOR_VALIDATION_EMBED)

@bot.slash_command(name="scoreboard", description="COTD Scoreboard!", guild_ids=GID)
async def scoreboard(interaction: Interaction):
    await interaction.response.defer()
    scoreboard_list = database.get_scoreboard()
    pages = menus.ButtonMenuPages(source=ScoreBoarder(scoreboard_list))
    await pages.start(interaction=interaction)

if __name__ == "__main__":
    bot.run(TOKEN)