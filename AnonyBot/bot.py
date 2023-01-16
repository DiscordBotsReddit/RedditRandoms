# https://www.reddit.com/r/Discord_Bots/comments/107yuhq/anonymity_bot_for_forum_channel/

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

TOKEN = os.getenv("REDDIT_REQUESTS")
FORUM_CHANNEL = "test-forum"
GUILD_NAME = "TestGuild"
TIMEZONE = ZoneInfo("US/Eastern")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(
    command_prefix=discord.ext.commands.when_mentioned_or("?"), intents=intents
)


@bot.event
async def on_ready():
    print("Logged in as", bot.user)


@bot.event
async def on_message(message):
    if (
        type(message.channel) == discord.channel.DMChannel
        and message.content is not None
    ):
        async for guild in bot.fetch_guilds():
            if guild.name.lower() == GUILD_NAME.lower():
                channels = await guild.fetch_channels()
                for channel in channels:
                    if (
                        channel.name.lower() == FORUM_CHANNEL.lower()
                        and type(channel) == discord.channel.ForumChannel
                    ):
                        now = datetime.now(tz=TIMEZONE)
                        string_date = now.strftime("%m/%d/%Y - %H:%M:%S")
                        await channel.create_thread(
                            name=f"Anonymous Post - {string_date}",
                            auto_archive_duration=1440,
                            content=message.content,
                        )
                        break


bot.run(TOKEN)
