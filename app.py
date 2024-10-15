import nextcord 
from nextcord.ext import commands, menus
from nextcord import Intents, Interaction, Embed, File
from config import * 
from typing import Dict, List, Optional 
from nextcord.ext.commands.errors import MissingAnyRole
from nextcord.utils import escape_markdown
from database import Database
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN=os.getenv('TOKEN')
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
        await interaction.response.defer()
        self.points_channel = await bot.fetch_channel(POINTS_CHANNEL_ID)
        isthere, messageids = database.get_message_user(interaction.message.id)
        if isthere:
            user = await bot.fetch_user(isthere)
            username = interaction.user.nick if interaction.user.nick is not None else interaction.user.name
            if database.submission_status(interaction.user.id) is False:
                await user.send(f"Approved! Your Proof Of Work was accepted by {username}.")
                await interaction.followup.send(f"{interaction.user.mention} approved {user.name} (uid: {user.id}) PoW.")
                res = database.increase_score(isthere)
                if res == 0:
                    await self.points_channel.send(f"Added 1 point to {user.mention}.")
            else:
                await interaction.followup.send(f"{user.name} PoW already approved.")
            self.stop()
            for messageid in messageids:
                try:
                    database.remove_message(isthere, messageid)
                    message = interaction.channel.get_partial_message(messageid)
                    await message.delete()
                except Exception as e:
                    print(str(e))
                    continue
    
    @nextcord.ui.button(label="Reject", style=nextcord.ButtonStyle.red)
    async def disapprove(self, button: nextcord.ui.Button, interaction:Interaction):
        await interaction.response.defer()
        isthere, _ = database.get_message_user(interaction.message.id) 
        if isthere:
            user = await bot.fetch_user(isthere)
            await user.send(f"Oops! Your proof of work was rejected by {interaction.user.nick if interaction.user.nick is not None else interaction.user.name}!\nYou may DM him/her and sort things out!")
            await interaction.followup.send(f"{interaction.user.mention} rejected {user.mention} PoW.")
        database.remove_message(isthere, interaction.message.id)
        message = interaction.message.id
        message = interaction.channel.get_partial_message(message)
        self.stop()
        await message.delete()
            

class Modal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Proof Of Work!", timeout=None)

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
        await interaction.response.defer()
        channel = bot.get_channel(CORRECT_FLAG_CHANNEL_ID)
        title = self.main_title.value
        desc = self.main_desc.value
        response = Response()
        success = database.accept_response(interaction.user.id)
        if success == 0:
            message = await channel.send(embed=Embed(title=f"Message from {interaction.user.name}", description=f"```{title}```\n```{desc}```"), view=response)
            database.add_message(interaction, message.id)
            await interaction.followup.send(embed=SENT_FOR_VAILDATION_EMBED, ephemeral=EPHEMERAL)
        else:
            await interaction.followup.send(embed=EXCESS_VALIDATION_EMBED, ephemeral=EPHEMERAL)


class ScoreBoarder(menus.ListPageSource):
    
    def __init__(self, data):
        super().__init__(data, per_page=15)
    
    async def format_page(self, menu, entries):
        desc = "```\n"
        desc += "╔"+"═"*15+"═"*20+"╗"
        k=1
        desc += "\n║" + "             SCOREBOARD            "+"║"
        
        for entry in entries:
            if k == 1:
                desc+="\n╠"+"═"*14+"╦"+"═"*20+"╣"
                k=0
            else:
                desc+="\n╠"+"═"*14+"╬"+"═"*20+"╣"
            score, name = entry.split()
            desc += "\n║"+name[0:14]+" "*(14-len(name))+"║"+"  "+score+" "*(18-len(score))+"║"
        desc += "\n╚"+"═"*14+"╩"+"═"*20+"╝"
        desc += "\n```"
        embed=Embed(title="Here you go!", description=desc, color=nextcord.Color.gold())
        return embed

def toggleEphemeral():
    global EPHEMERAL
    EPHEMERAL = not EPHEMERAL

@bot.slash_command(name="submit_flag", description="Submit the flag!", guild_ids=GID)
async def submit_flag(interaction: Interaction, flag:str):
    ans_flag = database.get_flag()

    if database.isUserPresent(interaction.user.id) == 0:
        database.register(interaction)

    if flag is None:
        return await interaction.response.send_message(embed=WHAT_YOU_DOING)

    if flag != ans_flag:
        forward_channel = bot.get_channel(WRONG_FLAG_CHANNEL_ID)
        await interaction.response.send_message(embed=INCORRECT_FLAG_EMBED, ephemeral=EPHEMERAL)
        await forward_channel.send(embed=Embed(title=f"Wrong flag by {interaction.user.name}", description=flag))

    else:
        _submit = database.submit_flag(interaction)
        if _submit == 1:              
            await interaction.response.send_message(embed=REPEATED_SUBMIT_EMBED, ephemeral=EPHEMERAL)
        else:
            modal = Modal()
            await interaction.response.send_modal(modal=modal)

@bot.slash_command(name="scoreboard", description="COTD Scoreboard!", guild_ids=GID)
@commands.has_any_role(*ADMIN_ROLES)
async def scoreboard(interaction: Interaction):
    await interaction.response.defer()
    scoreboard_list = database.get_scoreboard()
    pages = menus.ButtonMenuPages(source=ScoreBoarder(scoreboard_list))
    await pages.start(interaction=interaction)

@bot.group(name="set", invoke_without_subcommand=True)
@commands.has_any_role(*ADMIN_ROLES)
async def _set(ctx : commands.Context):
    if ctx.invoked_subcommand is None:
        await ctx.send("**Use $help set**")

@_set.command(name="flag")
@commands.has_any_role(*ADMIN_ROLES)
async def setFlag(ctx, flag : str | None = None):
    if flag is None:
        return await ctx.send(f"Cannot update new flag to None.")
    else:
        database.updateHint()
        database.update_status()
        database.update_flag(flag)
        await ctx.send(f"Updated flag to {flag}")

@_set.command(name="ephemeral")
@commands.has_any_role(*ADMIN_ROLES)
async def ephemeral(ctx, action : str | None = None):
    global EPHEMERAL
    if action is None:
        return await ctx.send("Usage:- $set ephemeral on/off.\nToggles ephemeral messages.")
    if action == "off":
        if EPHEMERAL is False:
            await ctx.send("Ephemeral messages are already off.")
        else:
            toggleEphemeral()
            await ctx.send("Ephemeral messages are now off.")
    elif action == "on":
        if EPHEMERAL is True:
            await ctx.send("Ephemeral messages are already on.")
        else:
            toggleEphemeral()
            await ctx.send("Ephemeral messages are now on.")
    else:
        await ctx.send(f"Invalid action:- {action}")

@_set.command(name="hint")
@commands.has_any_role(*ADMIN_ROLES)
async def hint(ctx, hint : str = None):
    if hint == 0:
        database.updateHint(None)
    else:
        database.updateHint(hint)
    await ctx.send("Hint added!")

@bot.slash_command(name="hint", description="Hint for ongoing COTD!", guild_ids=GID)
async def hint(interaction : Interaction):
    hint = database.getHint()
    if hint is None:
        await interaction.response.send_message(embed=NO_HINT_ADDED_EMBED, ephemeral=EPHEMERAL)
    else:
        await interaction.response.send_message(embed=Embed(title="Hint!", description=hint), ephemeral=EPHEMERAL)

@bot.slash_command(name="register", description="Register yourself for COTD!", guild_ids=GID)
async def register(interaction: Interaction):
    await interaction.response.defer()
    result = database.register(interaction)
    if result == 0:
        await interaction.followup.send(embed=REGISTERED_SUCCESSFULLY_EMBED)
    elif result == 1:
        await interaction.followup.send(embed=ALREADY_REGISTERED_EMBED)
    else:
        await interaction.followup.send(embed=REGISTRATION_FAILURE_EMBED)

@bot.command(name="flag")
@commands.has_any_role(*ADMIN_ROLES)
async def flag(ctx):
    await ctx.send(f"`Flag:- {database.get_flag()}`")

@bot.command(name="addcotd")
@commands.has_any_role(*ADMIN_ROLES)
async def flag(ctx, flag : str = None):
    if flag is None:
        return await ctx.send("Can't add cotd with an empty flag.")
    else:
        challday = database.add_cotd(flag)
        await ctx.send(f"Added cotd{challday} with flag {flag}.")

@bot.slash_command(name="add", description="Add point to a user.", guild_ids=GID)
@commands.has_any_role(*ADMIN_ROLES)
async def add(interaction: Interaction, user: nextcord.Member, points: int = None):
    await interaction.response.defer()
    isPresent = database.isUserPresent(user.id)
    if points is None:
        if isPresent:
            await interaction.followup.send(f"User already present.")
        else:
            database._register(user)
            await interaction.followup.send(f"Added **{user.mention}** to scoreboard.")
    else:
        points = int(points)
        if points <= 0:
            await interaction.followup.send(f"Points to be added should be more than 0.")
        elif points is not None:
            database.add(user, int(points))
            await interaction.followup.send(f"Added {points} points to **{user.mention}**.")

@bot.slash_command(name="subtract", description="Subtract point of a user.", guild_ids=GID)
@commands.has_any_role(*ADMIN_ROLES)
async def subtract(interaction: Interaction, user: nextcord.Member, points: int):
    points = int(points)
    if points <= 0:
        await interaction.response.send_message(f"Points to be deducted should be greater than 0.", ephemeral=True)
    else:
        database.sub(user.id, int(points))
        await interaction.response.send_message(f"Subtracted {points} points of **{user.mention}**.")

@bot.slash_command(name="show", description="Get the points of a user.", guild_ids=GID)
@commands.has_any_role(*ADMIN_ROLES)
async def show(interaction: Interaction, user: nextcord.Member):
    score = database.show(user.id)
    if score is None:
        await interaction.response.send_message(f"No such user added yet.")
    else:
        await interaction.response.send_message(f"{user.mention} has a score of {str(score)}.")

@bot.slash_command(name="ping", description="Check Bot Latency.", guild_ids=GID)
async def ping(interaction:Interaction):
    await interaction.response.send_message(f"Pong! In {round(bot.latency*1000)}ms.", ephemeral=EPHEMERAL)

@bot.event
async def on_ready():
    print("I am ready")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, MissingAnyRole):
        await ctx.send(embed=RESTRICTED_EMBED) 
if __name__ == "__main__":
    bot.run(TOKEN)
