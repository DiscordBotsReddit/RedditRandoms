import aiohttp
import discord
from discord import Webhook
from discord.ext import commands
import os

## PLEASE EDIT THESE WITH THE CORRECT VALUES
PREFIX = '.'
TOKEN = os.getenv("REDDIT_REQUESTS")
# URL for the webhook of guild 1
GUILD_1_WEBHOOK_URL = 'https://discord.com/api/webhooks/12345/abc'
# URL for the webhook of guild 2
GUILD_2_WEBHOOK_URL = 'https://discord.com/api/webhooks/12345/abc'
# Channel ID for where messages to/from guild 1 should go (should be the same channel that was used to make the webhook)
GUILD_1_CHANNEL = 123456
# Channel ID for where messages to/from guild 2 should go (should be the same channel that was used to make the webhook)
GUILD_2_CHANNEL = 123456


intents =  discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, description='Guild alliance webhook')

@bot.event
async def on_message(message):
    if message.channel.id == GUILD_1_CHANNEL:
        if message.author.bot != True:
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(GUILD_2_WEBHOOK_URL, session=session)
                await webhook.send(content=message.content, username=message.author.name+"#"+message.author.discriminator, avatar_url=message.author.avatar)
    if message.channel.id == GUILD_2_CHANNEL:
        if message.author.bot != True:
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(GUILD_1_WEBHOOK_URL, session=session)
                await webhook.send(content=message.content, username=message.author.name+"#"+message.author.discriminator, avatar_url=message.author.avatar)


bot.run(TOKEN)