#https://www.reddit.com/r/Discord_Bots/comments/zxkzgg/bot_that_sends_free_serial_key/

import discord
from discord.ext import commands
from discord.ext.commands import MissingPermissions
import os
import sqlite3
from random import choice

## EDIT TO YOUR VALUES
PREFIX = "."
TOKEN = os.getenv("REDDIT_REQUESTS")
KEYS_FILENAME = 'keys.txt'
## DON'T EDIT BELOW

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True

activity = discord.Activity(name='Free Serial Keys!', type=discord.ActivityType.playing)
bot = commands.Bot(command_prefix=PREFIX, intents=intents, description="Serial key provider bot", activity=activity)
db = sqlite3.connect('keys.db')

@bot.event
async def on_ready():
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS keys(id INTEGER PRIMARY KEY AUTOINCREMENT, key_val VARCHAR UNIQUE NOT NULL, used BOOL NOT NULL DEFAULT False, user_id INTEGER);")
    for filename in os.listdir('./'):
        if filename == KEYS_FILENAME:
            with open(filename) as f:
                lines = f.readlines()
            for line in lines:
                uq_key = line.strip()
                in_cur = db.cursor()
                in_cur.execute(f"INSERT OR IGNORE INTO keys(key_val) VALUES('{uq_key}');")
                db.commit()
                in_cur.close()
    cur.close()
    db.close()
    print(f'Bot is up and running as {bot.user}.')

@bot.command(name='add')
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def add(ctx):
    '''(Admin only) Loads in the keys file to the database
    '''
    for filename in os.listdir('./'):
        if filename == KEYS_FILENAME:
            with open(filename) as f:
                lines = f.readlines()
            for line in lines:
                uq_key = line.strip()
                cur = db.cursor()
                cur.execute(f"INSERT OR IGNORE INTO keys(key_val) VALUES('{uq_key}');")
                db.commit()
                cur.close()
    await ctx.channel.send('Keys updated!')

@add.error
async def add_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send(f'❌ {ctx.author.mention}, you do not have permission to add new keys. ❌')
    else:
        await ctx.channel.send(f'{ctx.author.mention}, there was an error with the command you sent.  Please try again.\n`{error}`')

@bot.command(name='key')
async def send_key(ctx):
    '''Sends the user a random key if they don't have one assigned
    '''
    cur = db.cursor()
    used = cur.execute(f"SELECT key_val FROM keys WHERE user_id='{ctx.author.id}';").fetchone()
    if used:
        await ctx.author.send(f'You have already claimed your free key.\nIf you forgot, your key is: `{used[0]}`\n\nIf you believe you got this message in error, please contact the admins.')
    else:
        available_keys = cur.execute("SELECT key_val FROM keys WHERE used=0;").fetchall()
        key = choice(available_keys)[0]
        await ctx.author.send(f'Your free key is: `{key}`\nPlease don\'t share this with anyone!')
        cur.execute(f"DELETE FROM keys where key_val='{key}';")
        cur.execute(f"INSERT INTO keys(key_val, used, user_id) VALUES('{key}', 1, '{ctx.author.id}');")
        db.commit()
    cur.close()

@bot.command(name='remove')
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def remove(ctx, user: discord.User):
    '''(Admin only) Removes a key from the database and unassigns the user
    '''
    cur = db.cursor()
    rem_key = cur.execute(f"SELECT key_val FROM keys WHERE user_id='{ctx.author.id}';").fetchone()
    if rem_key:
        cur.execute(f"DELETE FROM keys WHERE user_id='{user.id}';")
        db.commit()
        await ctx.channel.send(f'Removed key from {user.mention}.')
        await user.send(f'Your key `{rem_key[0]}` was removed and is no longer valid.')
    else:
        await ctx.channel.send(f'{user.mention} has no valid keys.')
    cur.close()

@remove.error
async def remove_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send(f'❌ {ctx.author.mention}, you do not have permission to remove keys. ❌')
    else:
        await ctx.channel.send(f'{ctx.author.mention}, there was an error with the command you sent.  Please try again.\n`{error}`')

bot.run(TOKEN)