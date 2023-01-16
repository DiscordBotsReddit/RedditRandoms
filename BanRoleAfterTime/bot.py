# https://www.reddit.com/r/discordbots/comments/1007eek/is_there_a_bot_that_autobans_certain_roles_after/

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from discord.ext import commands
from humanfriendly import parse_timespan

# from zoneinfo import ZoneInfo
from tzlocal import get_localzone

## EDIT TO YOUR VALUES
PREFIX = "?banbot "  # Prefix for the init and help commands
TOKEN = os.getenv("REDDIT_REQUESTS")
TIMERS_FILE = "timers.db"  # If you want the database file name to be different, doesn't really matter
DEFAULT_TIMER = (
    "1 week"  # If no length is specified in the init command, defaults to this length
)
MINIMUM_TIMER = 30  # Minimum timer length in seconds, also how often the bot checks for bannable members
TIMEZONE = get_localzone()
## DON'T EDIT BELOW


db = sqlite3.connect(TIMERS_FILE)
cur = db.cursor()
cur.execute(
    f"CREATE TABLE IF NOT EXISTS timers(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL UNIQUE, timer TEXT NOT NULL DEFAULT '{DEFAULT_TIMER}');"
)
db.commit()
cur.close()
db.close()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

activity = discord.Activity(name=f"{PREFIX}help", type=discord.ActivityType.playing)
bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    description="BootBot - Bans users with no extra roles",
    activity=activity,
)


@bot.command()
@commands.has_permissions(manage_guild=True)
async def init(ctx, *, length: Optional[str]):
    """Initialize the db for timers, include length before ban"""
    try:
        if length:
            if parse_timespan(length) < MINIMUM_TIMER:
                await ctx.reply("Minimum timer length is 60 seconds.")
                return
        db = sqlite3.connect(TIMERS_FILE)
        cur = db.cursor()
        guild_timer = cur.execute(
            f"SELECT * FROM timers WHERE guild_id={ctx.guild.id};"
        ).fetchone()
        if guild_timer is None:
            cur.execute(
                f"INSERT INTO timers(guild_id, timer) VALUES('{ctx.guild.id}', '{length if length else DEFAULT_TIMER}');"
            )
            db.commit()
            cur.close()
            db.close()
            await ctx.reply(
                f"Set the timer length for this guild to: `{length if length else DEFAULT_TIMER}`."
            )
        else:
            cur.execute(
                f"UPDATE timers SET timer='{length if length else DEFAULT_TIMER}' WHERE guild_id='{ctx.guild.id}';"
            )
            db.commit()
            cur.close()
            db.close()
            await ctx.reply(
                f"Updated the timer length for this guild to `{length if length else DEFAULT_TIMER}`."
            )
    except Exception as e:
        await ctx.reply(
            f"There was an error with your inputted length.\nOnly 1 time setting can be used at this time (ex. `30m` or `1w` or `2 days`).\n\nSupported time units are:\n- s, sec, secs, second, seconds\n- m, min, mins, minute, minutes\n- h, hour, hours\n- d, day, days\n- w, week, weeks\n- y, year, years"
        )


async def check_timers():
    db = sqlite3.connect(TIMERS_FILE)
    cur = db.cursor()
    guilds = cur.execute("SELECT guild_id,timer FROM timers;").fetchall()
    cur.close()
    db.close()
    if guilds:
        for guild in guilds:
            guild_id = guild[0]
            length = parse_timespan(guild[1])
            working_guild = bot.get_guild(guild_id)
            for member in working_guild.members:
                if member.joined_at + timedelta(seconds=length) < datetime.now(
                    tz=TIMEZONE
                ):
                    # timer has passed
                    if len(member.roles) == 1:
                        # only 1 role
                        await working_guild.ban(
                            user=member, reason="Only 1 role - autoban"
                        )
    else:
        return


@bot.event
async def on_ready():
    scheduler = AsyncIOScheduler()
    timers = IntervalTrigger(seconds=MINIMUM_TIMER)
    scheduler.add_job(check_timers, trigger=timers)
    scheduler.start()
    print(f"Bot is up and running as {bot.user}.")


bot.run(TOKEN)
