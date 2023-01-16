import os

import discord
from discord.ext import commands

## PLEASE EDIT THESE WITH THE CORRECT VALUES
PREFIX = "."
TOKEN = os.getenv("REDDIT_REQUESTS")  # 'your-token-here'
ROLE_NAME = "Super Awesome Role for Advertising our Server to your Friends!"
ADVERTISMENT_PREFIX = "[Custom]"
## STOP EDITING

intents = discord.Intents.default()
intents.presences = True
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    description="Giving a special role for advertising the world's greatest graphic design server",
)


@bot.event
async def on_presence_update(before, after):
    if after.bot:
        pass
    has_role = False
    for role in after.guild.roles:
        if role.name == ROLE_NAME:
            new_role = after.guild.get_role(role.id)
    if after.activity:
        if after.activity.name.lower().startswith(ADVERTISMENT_PREFIX.lower()):
            for role in after.roles:
                if role.name == ROLE_NAME:
                    has_role = True
            if has_role == False:
                try:
                    await after.add_roles(new_role)
                except:
                    pass
            if has_role == True:
                pass
        if not after.activity.name.lower().startswith(ADVERTISMENT_PREFIX.lower()):
            for role in after.roles:
                if role.name == ROLE_NAME:
                    has_role = True
            if has_role == True:
                try:
                    await after.remove_roles(new_role)
                except:
                    pass
    else:
        try:
            await after.remove_roles(new_role)
        except:
            pass


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


bot.run(TOKEN)
