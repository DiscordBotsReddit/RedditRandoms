# https://www.reddit.com/r/discordbots/comments/10122ci/looking_for_a_bot_to_replace_autodelete_for_those/

import os
import sqlite3
from asyncio import sleep
from datetime import datetime, timedelta, timezone

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from discord.ext import commands
from humanfriendly import parse_timespan

## EDIT THESE WITH YOUR VAULES
PREFIX = "?purge "
TOKEN = "BOT TOKEN"  # Replace with your token or put the token in environment variables
DEFULT_MESSAGE_AGE = "5 minutes"  # Default message age to purge
HOW_OFTEN_PURGE_RUNS = "20 minutes"
##

db = sqlite3.connect("channels.db")
cur = db.cursor()
cur.execute(
    "CREATE TABLE IF NOT EXISTS channels_not_to_purge(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL UNIQUE);"
)
cur.execute(
    "CREATE TABLE IF NOT EXISTS timers(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER UNIQUE NOT NULL, timer INTEGER NOT NULL);"
)
cur.close()
db.close()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

activity = discord.Activity(name=f"for {PREFIX}", type=discord.ActivityType.watching)
bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    description="PurgeBot - Purges messages frequently",
    activity=activity,
)


@bot.event
async def on_ready():
    scheduler = AsyncIOScheduler()
    trigger = IntervalTrigger(seconds=parse_timespan(HOW_OFTEN_PURGE_RUNS))
    scheduler.add_job(check_timers, trigger=trigger)
    scheduler.start()
    print(f"Logged in as {bot.user}")


@bot.command(name="remove", aliases=["dontpurge"])
@commands.has_permissions(manage_guild=True)
async def no_purge(ctx):
    """Adds the channel the command was sent in to the no-purge list"""
    await ctx.message.delete()
    guild_id = ctx.guild.id
    channel_id = ctx.channel.id
    db = sqlite3.connect("channels.db")
    cur = db.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO channels_not_to_purge(guild_id, channel_id) VALUES(?,?);",
        (guild_id, channel_id),
    )
    db.commit()
    cur.close()
    db.close()
    await ctx.author.send(
        f"The `{ctx.channel.name}` channel has been added to the no-purge list."
    )


@bot.command(name="add", aliases=["purge"])
@commands.has_permissions(manage_guild=True)
async def purge(ctx):
    """Removes the channel the command was sent in from the no-purge list"""
    await ctx.message.delete()
    guild_id = ctx.guild.id
    channel_id = ctx.channel.id
    db = sqlite3.connect("channels.db")
    cur = db.cursor()
    channel = cur.execute(
        f"SELECT * FROM channels_not_to_purge WHERE guild_id='{guild_id}' AND channel_id='{channel_id}';"
    ).fetchone()
    if channel is None:
        await ctx.author.send(
            f"The `{ctx.channel.name}` channel is already being purged."
        )
        cur.close()
        db.close()
        return
    else:
        cur.execute(
            f"DELETE FROM channels_not_to_purge WHERE guild_id='{guild_id}' AND channel_id='{channel_id}';"
        )
        db.commit()
        cur.close()
        db.close()
        await ctx.author.send(
            f"The `{ctx.channel.name}` channel has been removed from the no-purge list."
        )


@bot.command(name="set", aliases=["update"])
@commands.has_permissions(manage_guild=True)
async def settimer(ctx, *, length: str = DEFULT_MESSAGE_AGE):
    """Messages older than this length of time are purged"""
    try:
        timer = parse_timespan(length)
        guild_id = ctx.guild.id
        db = sqlite3.connect("channels.db")
        cur = db.cursor()
        guild = cur.execute(
            f"SELECT * FROM timers WHERE guild_id='{guild_id}';"
        ).fetchone()
        if guild is None:
            cur.execute(
                "INSERT INTO timers(guild_id, timer) VALUES(?,?);", (guild_id, timer)
            )
            db.commit()
            cur.close()
            db.close()
            await ctx.reply(f"Purge age for this guild/server set to `{length}`.")
        else:
            cur.execute(
                "UPDATE timers SET timer=? WHERE guild_id=?;", (timer, guild_id)
            )
            db.commit()
            cur.close()
            db.close()
            await ctx.reply(f"Purge age for this guild/server updated to `{length}`.")
    except:
        await ctx.reply(
            "There was an error with your inputted length.\nOnly 1 time setting can be used at this time (ex. `30m` or `1w` or `2 days`).\n\nSupported time units are:\n- s, sec, secs, second, seconds\n- m, min, mins, minute, minutes\n- h, hour, hours\n- d, day, days\n- w, week, weeks\n- y, year, years"
        )


def check_pinned(message):
    return not message.pinned


async def check_timers():
    print("Purge starting...")
    db = sqlite3.connect("channels.db")
    cur = db.cursor()
    timers = cur.execute("SELECT guild_id, timer FROM timers;").fetchall()
    if timers is None:
        cur.close()
        db.close()
        return
    else:
        for guild in timers:
            total_purge = 0
            guild_id = guild[0]  # guild.id (int)
            interval = guild[1]  # interval in seconds (int)
            now_timestamp = datetime.utcnow()
            year = now_timestamp.year
            month = now_timestamp.month
            day = now_timestamp.day
            hour = now_timestamp.hour
            minute = now_timestamp.minute
            second = now_timestamp.second
            tzaware = datetime(
                year, month, day, hour, minute, second, tzinfo=timezone.utc
            )
            time_to_purge_before = tzaware - timedelta(seconds=interval)
            working_guild = bot.get_guild(guild_id)
            for channel in working_guild.text_channels:
                no_purge = cur.execute(
                    f"SELECT * FROM channels_not_to_purge WHERE channel_id='{channel.id}' AND guild_id='{channel.guild.id}';"
                ).fetchone()
                if no_purge:
                    pass
                else:
                    try:
                        channel = working_guild.get_channel(channel.id)
                        # channel_purge = 0
                        # skipped_messages = 0
                        # async for message in channel.history(limit=1000):
                        #     if message.pinned:
                        #         skipped_messages += 1
                        #         pass
                        #     elif message.created_at < time_to_purge_before:
                        #         await message.delete()
                        #         total_purge += 1
                        #         channel_purge += 1
                        #         await sleep(1)
                        # if channel_purge > 0:
                        #     print(f'Purge complete.\nPurged `{channel_purge}` message(s).\nSkipped `{skipped_messages}` pinned message(s).')
                        purged = await channel.purge(
                            limit=10000, before=time_to_purge_before, check=check_pinned
                        )
                        if len(purged) > 0:
                            print(f"Purged #{channel.name} - {len(purged)} messages.")
                            total_purge += len(purged)
                        await sleep(1)  # trying to prevent rate-limiting
                    except Exception as error:
                        pass
                        # await working_guild.public_updates_channel.send(f"Not able to purge messages from {channel.name}:\n{error}")
            print(f">> Purged {working_guild.name} of {total_purge} messages <<")
        cur.close()
        db.close()


bot.run(TOKEN)
