# https://www.reddit.com/r/Discord_Bots/comments/102cc2s/a_bot_that_tracks_the_time_since_a_person_did/
import os
import sqlite3
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned
from humanfriendly import parse_timespan

## EDIT
TOKEN = os.getenv("REDDIT_REQUESTS")  # Replace with your token
DATABASE = "activity.db"
INACTIVE_TIME = "60 days"
## STOP EDIT

intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(
    command_prefix=when_mentioned,
    description="ActivityMonitorBot - Alerts the owner when a member is inactive for X amount of time",
    intents=intents,
)

db = sqlite3.connect(DATABASE)
cur = db.cursor()
cur.execute(
    f"CREATE TABLE IF NOT EXISTS activity_monitor(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, last_active DATETIME NOT NULL)"
)
cur.execute(
    f"CREATE TABLE IF NOT EXISTS inactive_length(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, length INTEGER NOT NULL)"
)
db.commit()
cur.close()
db.close()


@bot.command(name="set_inactive_time", aliases=["update_inactive_time"])
async def setup(ctx, *, length: str = parse_timespan(INACTIVE_TIME)):
    if ctx.guild:
        db = sqlite3.connect(DATABASE)
        cur = db.cursor()
        guild = cur.execute(
            f"SELECT * FROM inactive_length WHERE guild_id='{ctx.guild.id}';"
        ).fetchone()
        if guild:
            cur.execute(
                f"UPDATE inactive_length SET length={parse_timespan(length)} WHERE guild_id='{ctx.guild.id}';"
            )
            db.commit()
            cur.close()
            db.close()
            await ctx.send(
                f"Updated the inactivity timer for this guild/server to `{length}`."
            )
        else:
            cur.execute(
                f"INSERT INTO inactive_length(guild_id, length) VALUES('{ctx.guild.id}', {parse_timespan(length)});"
            )
            db.commit()
            cur.close()
            db.close()
            await ctx.send(
                f"Set the inactivity timer for this guild/server to `{length}`."
            )
    else:
        ctx.author.send("Please use that command in a guild.")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")


@bot.event
async def on_message(message):
    if message.guild:
        guild_owner = bot.get_user(message.guild.owner_id)
        user_id = message.author.id
        guild_id = message.guild.id
        timestamp = message.created_at
        db = sqlite3.connect(DATABASE)
        with db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            guild = cur.execute(
                f"SELECT * FROM inactive_length WHERE guild_id='{message.guild.id}';"
            ).fetchone()
            if not guild:
                cur.execute(
                    f"INSERT INTO inactive_length(guild_id, length) VALUES('{message.guild.id}', '{parse_timespan(INACTIVE_TIME)}');"
                )
                db.commit()
                guild = cur.execute(
                    f"SELECT * FROM inactive_length WHERE guild_id='{message.guild.id}';"
                ).fetchone()
            inactive_users = cur.execute(
                f"SELECT * FROM activity_monitor WHERE guild_id={guild_id};"
            ).fetchall()
            for user in inactive_users:
                last_active = datetime.strptime(
                    user["last_active"], "%Y-%m-%d %H:%M:%S.%f%z"
                )
                now_timestamp = datetime.utcnow()
                year = now_timestamp.year
                month = now_timestamp.month
                day = now_timestamp.day
                hour = now_timestamp.hour
                minute = now_timestamp.minute
                second = now_timestamp.second
                microsecond = now_timestamp.microsecond
                tzaware = datetime(
                    year,
                    month,
                    day,
                    hour,
                    minute,
                    second,
                    microsecond,
                    tzinfo=timezone.utc,
                )
                action_if_last_active_before_this_time = tzaware - timedelta(
                    seconds=guild["length"]
                )
                if last_active < action_if_last_active_before_this_time:
                    user = bot.get_user(user["user_id"])
                    if user.bot:
                        pass
                    else:
                        await guild_owner.send(
                            f"{user.mention} has been inactive for at least the time you specified (60 days is the default if you never changed it)."
                        )
            user = cur.execute(
                f"SELECT * FROM activity_monitor WHERE user_id={user_id} AND guild_id={guild_id};"
            ).fetchone()
            if user:
                cur.execute(
                    f"UPDATE activity_monitor SET last_active='{timestamp}' WHERE user_id={user_id} AND guild_id={guild_id};"
                )
                db.commit()
                cur.close()
            else:
                cur.execute(
                    f"INSERT INTO activity_monitor(user_id,guild_id,last_active) VALUES('{user_id}', '{guild_id}', '{timestamp}');"
                )
                db.commit()
                cur.close()
            await bot.process_commands(message)
    else:
        await bot.process_commands(message)


bot.run(TOKEN)
