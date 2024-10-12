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

class Response(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None
    @nextcord.ui.button(label="Approve", style=nextcord.ButtonStyle.green)
    async def approve(self, button: nextcord.ui.button, interaction: Interaction):
        isthere, messageids = database.get_message_user(interaction.message.id)
        if isthere:
            user = await bot.fetch_user(isthere)
            user.send(f"Approved! Your proof of work was accepted!")
            database.increase_score(interaction.message.id)
            for messageid in messageids:
                try:
                    message = await interaction.channel.fetch_message(messageid)
                    await message.delete()
                except:
                    continue
    
    @nextcord.ui.button(label="Disapprove", style=nextcord.ButtonStyle.red)
    async def disapprove(self, button: nextcord.ui.Button, interaction:Interaction):
        isthere = database.get_message_user(interaction.message.id) 
        if isthere:
            user = bot.fetch_user(isthere)
            user.send(f"Oops! Your proof of work was rejected!")
        message = interaction.message.id
        message = await interaction.channel.fetch_message(message)
        message.delete()
            

class Modal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "Proof Of Work!"
        )

        self.main_title = nextcord.ui.TextInput(
            label="Title",
            min_length=2,
            max_length=20,
            placeholder="Title"
        )

        self.main_desc = nextcord.ui.TextInput(
            label="Writeup",
            min_length=10,
            max_length=500,
            placeholder="Writeup",
            style=nextcord.TextInputStyle.paragraph
        )    
        
        self.add_item(self.main_desc)
        self.add_item(self.main_title)
    
    async def callback(self, interaction: Interaction):
        channel = bot.get_channel(1258097832590708756)
        title = self.main_title.value
        desc = self.mani_title.desc
        message = await channel.send(embed=Embed(title=f"Message from {interaction.user.name}", description=f"```{title}```\n```{desc}```"))
        response = Response()
        await interaction.response.send_message(embed=Embed(title="Update!", description="Sent for validation, you will be notified in DM."),view= response, ephemeral=True)
        database.add_message(interaction, message.id)


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
    forward_channel = bot.get_channel(1258097832590708756)
    if flag is None:
        return await interaction.followup.send(embed=WHAT_YOU_DOING)

    if flag != ans_flag:
        await interaction.followup.send(embed=INCORRECT_FLAG_EMBED)
        await forward_channel.send(embed=Embed(title=f"Wrong flag by {interaction.user.name}", description=flag))

    else:
        _submit = database.submit_flag(interaction)
        if _submit == 1:              
            await interaction.followup.send(embed=REPEATED_SUBMIT_EMBED)
        else:
            modal = Modal()
            await interaction.followup.send(modal=modal)

@bot.slash_command(name="scoreboard", description="COTD Scoreboard!", guild_ids=GID)
async def scoreboard(interaction: Interaction):
    await interaction.response.defer()
    scoreboard_list = database.get_scoreboard()
    pages = menus.ButtonMenuPages(source=ScoreBoarder(scoreboard_list))
    await pages.start(interaction=interaction)

@bot.event
async def on_ready():
    print("I am ready")

if __name__ == "__main__":
    bot.run(TOKEN)