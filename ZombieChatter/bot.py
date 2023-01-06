import discord
from aiohttp import ClientSession
from random import choice
from discord import Webhook
from discord.ext import commands
import os

## PLEASE EDIT THESE WITH THE CORRECT VALUES

ZOMBIE_CHATS = [
    'nnrr',
    'mnuhhhh',
    'mrrrrr',
    'braaaaaains',
    'i\'m a zombie',
    "this is another chat to show that you can use either kind of quotes"
]

PREFIX = '.'
TOKEN = os.getenv("REDDIT_REQUESTS")

# ZOMBIE_ROLE and WEBHOOK_NAME are case insensitive (ZomBiE = ZOMBIE = zombie)

ZOMBIE_ROLE = 'ZOMBIE'
# The name of the role that you want to have messages replaced.
ZOMBIE_CHANNEL = 123456789
# Right click on the channel and pick 'Copy ID'.
# If you don't see this option, enable developer tools in your user settings App Settings -> Advanced
WEBHOOK_NAME = 'ZombieChat'
# CREATE A WEBHOOK  in server settings -> Integrations.  The avatar doesn't matter.
# Make sure the channel is set to the one you want.


intents =  discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, description='ZomBot')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        pass
    hooks = await message.channel.webhooks()
    for hook in hooks:
        if hook.name.lower() == WEBHOOK_NAME.lower() and hook.channel == message.channel:
            try:
                for role in message.author.roles:
                    if role.name.lower() == ZOMBIE_ROLE.lower():
                        await message.delete()
                        new_message = choice(ZOMBIE_CHATS)
                        async with ClientSession() as session:
                            webhook = Webhook.from_url(hook.url, session=session)
                            await webhook.send(content=new_message, username=f"[ZOMBIE] {message.author.display_name}", avatar_url=message.author.avatar)
            except Exception as e:
                pass

bot.run(TOKEN)