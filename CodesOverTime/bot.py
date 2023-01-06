#https://www.reddit.com/r/Discord_Bots/comments/100opw1/looking_for_a_bot_i_can_upload_game_codes_to_that/

import os
import sqlite3
from typing import Optional

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from humanfriendly import parse_timespan

## EDIT TO YOUR VALUES
PREFIX = "?keys "
TOKEN = os.getenv("REDDIT_REQUESTS")
DEFAULT_LENGTH = '1 hour'
## DON'T EDIT BELOW

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

activity = discord.Activity(name=f'{PREFIX}help', type=discord.ActivityType.playing)
bot = commands.Bot(command_prefix=PREFIX, intents=intents, description="Sends codes in channel over time", activity=activity)

scheduler = AsyncIOScheduler()

async def send_key(channel):
    db = sqlite3.connect('keys.db')
    cur = db.cursor()
    key = cur.execute(f"SELECT key_val FROM keys WHERE guild_id={channel.guild.id};").fetchone()
    if key:
        await channel.send(f'{key[0]}')
        cur.execute(f"DELETE FROM keys WHERE key_val='{key[0]}' AND guild_id={channel.guild.id};")
        db.commit()
        db.close()
    else:
        scheduler.pause()
        scheduler.remove_all_jobs()
        await channel.send(f'No keys found, timer stopped.  Please have an administrator use `{PREFIX}add` to get more added.')

@bot.event
async def on_ready():
    db = sqlite3.connect('keys.db')
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS keys(id INTEGER PRIMARY KEY AUTOINCREMENT, key_val VARCHAR UNIQUE NOT NULL, guild_id INTEGER NOT NULL);")
    cur.close()
    print(f'Bot is up and running as {bot.user}.')

@bot.command(name='add')
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def add(ctx, file: discord.Attachment):
    '''Type this command, drag a text file into discord, then send
    '''
    lines = await file.read()
    await ctx.message.delete()
    lines = lines.decode()
    lines = lines.split('\n')
    db = sqlite3.connect('keys.db')
    for line in lines:
        uq_key = line.strip()
        cur = db.cursor()
        cur.execute(f"INSERT OR IGNORE INTO keys(key_val, guild_id) VALUES('{uq_key}', '{ctx.guild.id}');")
        db.commit()
        cur.close()
    db.close()
    await ctx.channel.send('Keys updated!')

@bot.command(name='start')
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def start(ctx, length: Optional[str]):
    '''Starts the auto-posting in the channel the command is run
    '''
    try:
        if length is None:
            length = DEFAULT_LENGTH
        await ctx.reply(f'Sending a key every `{length}`.')
        length = parse_timespan(length)
        timer = IntervalTrigger(seconds=length)
        channel = bot.get_channel(ctx.channel.id)
        scheduler.add_job(send_key, trigger=timer, args=[channel])
        if scheduler.running:
            scheduler.resume()
        else:
            scheduler.start()
    except Exception as e:
        await ctx.reply(f'There was an error with your inputted length.\nOnly 1 time setting can be used at this time (ex. `30m` or `1w` or `2 days`).\n\nSupported time units are:\n- s, sec, secs, second, seconds\n- m, min, mins, minute, minutes\n- h, hour, hours\n- d, day, days\n- w, week, weeks\n- y, year, years')

@bot.command(name='stop')
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def stop(ctx):
    '''Stops the auto-posting in the channel the command is run
    '''
    try:
        scheduler.pause()
        scheduler.remove_all_jobs()
        await ctx.reply(f'Keys no longer sending.')
    except Exception as e:
        await ctx.reply(f'{e}')

@add.error
async def add_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send(f'❌ {ctx.author.mention}, you do not have permission to add new keys. ❌')
    else:
        await ctx.channel.send(f'{ctx.author.mention}, there was an error with the command you sent.  Please try again.\n`{error}`')


bot.run(TOKEN)