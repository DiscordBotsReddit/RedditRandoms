# https://www.reddit.com/r/Discord_Bots/comments/107jo3x/automated_scheduled_polls/

import os
from zoneinfo import ZoneInfo

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

##EDIT
USER_ID = int(os.getenv("DISCORD_USER_ID"))
TOKEN = os.getenv("REDDIT_REQUESTS")  # Change with your own token
PREFIX = "?"

CHANNEL_NAME = "game-night"
DAYS_TO_RUN = "mon,tue,wed,thu,fri,sat,sun"
HOUR_TO_RUN = 8
MINUTE_TO_RUN = 0
TIMEZONE = ZoneInfo("US/Eastern")
##STOP EDIT

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True

activity = discord.Activity(name=f"for {PREFIX}", type=discord.ActivityType.watching)
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(PREFIX),
    intents=intents,
    description="Polls the channel for game availablity",
    activity=activity,
)


async def post_poll():
    for channel in bot.get_all_channels():
        if channel.name.lower() == CHANNEL_NAME.lower():
            poll = await channel.send(
                "**Availabiltiy for Game Tonight**\n✅ - Yes\n\n⛔ - No\n\n❔ - Maybe\n"
            )
            await poll.add_reaction("✅")
            await poll.add_reaction("⛔")
            await poll.add_reaction("❔")
            break


@bot.event
async def on_ready():
    if os.path.exists("./cogs"):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")
    scheduler = AsyncIOScheduler()
    trigger = CronTrigger(
        day_of_week=DAYS_TO_RUN,
        hour=HOUR_TO_RUN,
        minute=MINUTE_TO_RUN,
        timezone=TIMEZONE,
    )
    scheduler.add_job(post_poll, trigger=trigger)
    scheduler.start()
    print("Logged in as", bot.user)


@bot.command(hidden=True)
async def logout(ctx):
    """Logs the bot out and closes the script"""
    if ctx.message.author.id == USER_ID:
        print(f"Logout command {ctx.message.author}.")
        await ctx.reply("Logging out...")
        await bot.close()
    else:
        await ctx.message.delete()
        await ctx.author.send("Sorry, but you cannot use the logout command.")
        print(f"{ctx.author} tried to log the bot out in {ctx.guild}.")


@bot.command(hidden=True)
@commands.has_permissions(manage_guild=True)
async def reload(ctx, extension):
    """Reloads the cog specified"""
    await ctx.message.delete()
    await bot.reload_extension(f"cogs.{extension}")


bot.run(TOKEN)
