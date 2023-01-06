#https://www.reddit.com/r/discordbots/comments/100so0g/looking_for_a_bot_to_track_individual_stats_for/

import os
import sqlite3
from datetime import datetime
from typing import Literal, Optional

import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from discord.ext.commands import CommandOnCooldown, MissingRequiredArgument
from tzlocal import get_localzone

## PLEASE EDIT THESE WITH THE CORRECT VALUES
PREFIX = '?poo '
TOKEN = os.getenv('REDDIT_REQUESTS') # 'your-token-here'
TIMEZONE = get_localzone()
## STOP EDITING

db = sqlite3.connect('poo.db')
cur = db.cursor()
cur.execute(f"CREATE TABLE IF NOT EXISTS poos(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, date DATETIME NOT NULL);")
db.commit()
cur.close()
db.close()

intents =  discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.members = True

activity = discord.Activity(name=f'you {PREFIX}', type=discord.ActivityType.watching)
bot = commands.Bot(command_prefix=PREFIX, intents=intents, description='Tracking your 💩 stats', activity=activity)

@bot.event
async def on_message(message):
    if message.content.lower() == "pooping":
        await add_poo(message)
    else:
        await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")

@bot.command(name='add')
async def add_poo(ctx):
    '''Add an instance to your tracker
    '''
    db = sqlite3.connect('poo.db')
    cur = db.cursor()
    cur.execute("INSERT INTO poos(user_id, guild_id, date) VALUES(?, ?, ?);", (ctx.author.id, ctx.guild.id, datetime.now(tz=TIMEZONE)))
    db.commit()
    cur.close()
    db.close()
    await ctx.reply('Added your 💩 to the tracker!')

@bot.command(name='info')
async def poo_info(ctx, type: Optional[Literal["mine", "server"]] = 'mine'):
    '''Run with 'mine' or 'server' for 💩 info!
    '''
    db = sqlite3.connect('poo.db')
    cur = db.cursor()
    if type == 'mine':
        results = cur.execute(f"SELECT * FROM poos WHERE user_id={ctx.author.id};").fetchall()
        cur.close()
        db.close()
        await ctx.reply(f'You have {len(results)} 💩\'s logged!')
    elif type == 'server':
        results = cur.execute(f"SELECT * FROM poos WHERE guild_id={ctx.guild.id};").fetchall()
        cur.close()
        db.close()
        await ctx.reply(f'The server has {len(results)} 💩\'s logged!')
    else:
        await ctx.reply('You must pick "mine" or "server" when using this command.')
    pass

@bot.command(name='leaderboard')
@commands.cooldown(1, 30, BucketType.guild)
async def poo_leaderboard(ctx):
    '''Display the current leaderboard (30s cooldown)
    '''
    poo_dict = {}
    leaderboard_em = discord.Embed(title='💩 LEADERBOARD 💩', color=discord.Color.from_str('#794f0e'))
    db = sqlite3.connect('poo.db')
    cur = db.cursor()
    leaderboard = cur.execute(f"SELECT user_id, COUNT(*) as count FROM poos WHERE guild_id={ctx.guild.id} GROUP BY user_id ORDER BY count DESC LIMIT 5;").fetchall()
    cur.close()
    db.close()
    if len(leaderboard) == 0:
        await ctx.send('💩 leaderboard is currently empty.')
        return
    leader = ctx.guild.get_member(leaderboard[0][0])
    await ctx.send(f"💩 **CURRENT POO LEADER IS {leader.mention}!** 💩")
    if leader.avatar is not None:
        leaderboard_em.set_thumbnail(url=leader.avatar.url)
    for user in leaderboard:
        username = ctx.guild.get_member(user[0]).display_name
        num_poos = user[1]
        poo_dict[username] = num_poos
    for leader in poo_dict.items():
        leaderboard_em.add_field(name=leader[0], value=leader[1], inline=False)
    await ctx.send(embed=leaderboard_em)

@bot.command(name='reset')
@commands.has_permissions(manage_guild=True)
async def flush_poo(ctx):
    '''Admins can clear the leaderboard
    '''
    db = sqlite3.connect('poo.db')
    cur = db.cursor()
    cur.execute(f'DELETE FROM poos WHERE guild_id={ctx.guild.id};')
    db.commit()
    cur.close()
    db.close()
    await ctx.send(f'{ctx.author.mention} cleared the 💩 leaderboard.')

@bot.event
async def on_command_error(ctx, exc):
	if isinstance(exc, MissingRequiredArgument):
		await ctx.send('One or more required arguments are missing.')
	elif isinstance(exc, CommandOnCooldown):
		retry_secs = int(exc.retry_after)
		if retry_secs >= 60 and retry_secs <= 3599:
			duration = 'minute(s)'
			retry_secs = int(retry_secs/60)
		elif retry_secs >= 3600:
			duration = 'hour(s)'
			retry_secs = int(retry_secs/3600)
		else:
			duration = 'seconds'
		await ctx.send(f'{ctx.author.mention}, that command is on cooldown for ~{str(retry_secs)} {duration}.')

bot.run(TOKEN)