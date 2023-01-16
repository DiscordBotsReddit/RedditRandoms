# https://www.reddit.com/r/Discord_Bots/comments/10b85nr/bot_that_limits_specific_channel_to_one_post_per/

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

TOKEN = os.getenv("REDDIT_REQUESTS")
PREFIX = ">dev"
APPROVED_DOMAINS = [
    "youtube",
    "youtu",
    "spotify",
    "apple",
]  # I have no idea what the apple music URL looks like
# youtube and youtu are both for youtube.  Pressing the share button generates a https://youtu.be/ link.

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix=when_mentioned_or(PREFIX), intents=intents)

channels_to_watch = []


@bot.event
async def on_ready():
    print("Logged in as", bot.user)


@bot.command(name="watch")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def watch_channel(ctx, channel: discord.TextChannel = None):
    """Sets the channel so only 1 post per user allowed."""
    if channel is None:
        channel = ctx.channel
    if channel.id in channels_to_watch:
        await ctx.reply(f"{channel.mention} is already being watched.")
    else:
        channels_to_watch.append(channel.id)
        await ctx.reply(f"{channel.mention} is now being watched.")


@bot.command(name="stop")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def watch_channel(ctx, channel: discord.TextChannel = None):
    """Stops deleting messages"""
    if channel is None:
        channel = ctx.channel
    if channel.id not in channels_to_watch:
        await ctx.reply(f"{channel.mention} is already not being watched.")
    else:
        channels_to_watch.pop(channel.id)
        await ctx.reply(f"{channel.mention} is no longer being watched.")


@bot.event
async def on_message(message):
    if message.author.bot == True:
        return
    messages_to_delete = []
    if message.channel.id not in channels_to_watch:
        await bot.process_commands(message)
    else:
        flag = 0
        for i in (
            message.content.replace("http://", "").replace("https://", "").split(".")
        ):
            for j in APPROVED_DOMAINS:
                if i == j:
                    flag = 1
                    break
        if flag == 0:
            await message.author.send(
                f"`{message.content}` is not allowed in the {message.channel.mention} channel."
            )
            await message.delete()
            return
        async for m in message.channel.history(
            before=datetime.now(tz=ZoneInfo("UTC")) - timedelta(seconds=1)
        ):
            if m.author == message.author:
                messages_to_delete.append(m)
        await message.channel.delete_messages(messages_to_delete)


bot.run(TOKEN)
