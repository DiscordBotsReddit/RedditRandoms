import os

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

## EDIT TO YOUR VALUES
PREFIX = "."  # Prefix for the init and help commands
TOKEN = os.getenv("REDDIT_REQUESTS")
ACTIVITY_NAME = (
    "AutoKickBot"  # What shows up under the bot's name, "Playing" then this string
)
ROLE_NAME = "zombie"
## DON'T EDIT BELOW

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

activity = discord.Activity(name=ACTIVITY_NAME, type=discord.ActivityType.playing)
bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    description="Kicks users with a certain role name on a cron schedule",
    activity=activity,
)


async def check_timers():
    for guild in bot.guilds:
        working_guild = bot.get_guild(guild.id)
        for member in working_guild.members:
            for role in member.roles:
                if role.name.lower() == ROLE_NAME.lower():
                    await working_guild.kick(
                        user=member, reason="Auto kick - Thursday 10am"
                    )
                    break


@bot.event
async def on_ready():
    scheduler = AsyncIOScheduler()
    timers = CronTrigger(day_of_week="thu", hour=10)
    scheduler.add_job(check_timers, trigger=timers)
    scheduler.start()
    print(f"Bot is up and running as {bot.user}.")


bot.run(TOKEN)
