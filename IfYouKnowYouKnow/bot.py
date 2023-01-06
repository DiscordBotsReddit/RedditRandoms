#https://www.reddit.com/r/Discord_Bots/comments/zw7z5w/looking_for_a_bot_to_do_a_specific_job/

## EDIT THIS SETTINGS TO YOUR LIKING
PREFIX = '.' #Just needed to put in the settings, not used for anything but the help command.
TOKEN = 'your-token-here'

# Channel that the bot will announce when timers run out organically.
CHANNEL_TO_ANNOUNCE = 123456789 ## You can get this by enabling developer tools and rightclicking on the channel and picking "Copy ID"

## DO NOT EDIT THIS IMPORT
from zoneinfo import ZoneInfo
## UPDATE THE TIMEZONE
TIMEZONE = ZoneInfo('US/Eastern') 


### DO NOT EDIT ANYTHING BELOW HERE IF YOU DON'T KNOW WHAT IT DOES ###
import os
import sqlite3
from datetime import datetime
from typing import Literal, Optional

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from discord.ext import commands
from discord.ext.commands import Context, Greedy

db = sqlite3.connect('iykyk.db')
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS iykyk(id INTEGER PRIMARY KEY AUTOINCREMENT, timer_user_id INTEGER NOT NULL UNIQUE, creator_user_id INTEGER NOT NULL, time_end DATETIME NOT NULL)")
cur.close()
db.close()

intents =  discord.Intents.default()
intents.members = True
intents.message_content = True

activity = discord.Activity(name='IYKYK Bot', type=discord.ActivityType.playing)
bot = commands.Bot(command_prefix=PREFIX, intents=intents, description='IYKYK Bot', activity=activity)

async def check_timers():
    db = sqlite3.connect('iykyk.db')
    cur = db.cursor()
    entries = cur.execute('SELECT timer_user_id, creator_user_id, time_end FROM iykyk').fetchall()
    for entry in entries:
        ends = datetime.strptime(entry[2], "%Y-%m-%d %H:%M:%S.%f%z")
        if ends < datetime.now(TIMEZONE):
            user = bot.get_user(int(entry[0]))
            creator = bot.get_user(int(entry[1]))
            channel = bot.get_channel(CHANNEL_TO_ANNOUNCE)
            await channel.send(f'**{user.mention}\'s TIMER FROM {creator.mention} HAS ENDED!**')
            cur.execute(f'DELETE FROM iykyk WHERE timer_user_id={user.id}')
            db.commit()
    cur.close()
    db.close()


def is_bot(m):
	return m.author == bot.user

async def delete_bot_messages():
	channel = bot.get_channel(CHANNEL_TO_ANNOUNCE)
	await channel.purge(check=is_bot)


@bot.event
async def on_ready():
	print(f'Logged in as {bot.user} (ID: {bot.user.id})')
	for filename in os.listdir('./cogs'):
		if filename.endswith('.py'):
			await bot.load_extension(f'cogs.{filename[:-3]}')
	sched = AsyncIOScheduler()
	timers = IntervalTrigger(seconds=10)
	purge = CronTrigger(hour=8)
	sched.add_job(check_timers, trigger=timers)
	sched.add_job(delete_bot_messages, trigger=purge)
	sched.start()


@bot.command(hidden=True)
async def reload(ctx, extension):
	''' Reloads the cog specified
	'''
	await ctx.message.delete()
	await bot.reload_extension(f'cogs.{extension}')


@bot.command(hidden=True)
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
	if not guilds:
		if spec == "~": #"!sync ~" - sync current guild
			synced = await ctx.bot.tree.sync(guild=ctx.guild)
		elif spec == "*": #"!sync *" - copies all global app commands to current guild and syncs
			ctx.bot.tree.copy_global_to(guild=ctx.guild)
			synced = await ctx.bot.tree.sync(guild=ctx.guild)
		elif spec == "^": #"!sync ^" - clears all commands from the current guild target and syncs (removes guild commands)
			ctx.bot.tree.clear_commands(guild=ctx.guild)
			await ctx.bot.tree.sync(guild=ctx.guild)
			synced = []
		else: #"!sync" - global sync
			synced = await ctx.bot.tree.sync()
		await ctx.send(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
		return
	ret = 0
	#"!sync guild_id_1 guild_id_2" - syncs guilds with id_1 and id_2
	for guild in guilds:
		try:
			await ctx.bot.tree.sync(guild=guild)
		except discord.HTTPException:
			pass
		else:
			ret += 1
	await ctx.send(f"Synced the tree to {ret}/{len(guilds)} guilds.")


bot.run(TOKEN)
