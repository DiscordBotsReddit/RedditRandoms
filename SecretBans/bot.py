#https://www.reddit.com/r/discordbots/comments/zxg1a5/i_had_the_valkyrja_bot_used_for_silent_bans/

import discord
from discord.ext import commands
from discord.ext.commands import MissingPermissions
import os
import sqlite3

## EDIT TO YOUR VALUES
PREFIX = "."
TOKEN = os.getenv("REDDIT_REQUESTS")
BAN_REASON = 'Automatically banned by the 🐱‍👤NINJA BAN BOT🐱‍👤!'
## DON'T EDIT BELOW


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

activity = discord.Activity(name='🐱‍👤 Ban Bot', type=discord.ActivityType.playing)
bot = commands.Bot(command_prefix=PREFIX, intents=intents, description="Ninja ban bot", activity=activity)
db = sqlite3.connect('pending_bans.db')

@bot.event
async def on_ready():
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS pending_bans(id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR UNIQUE NOT NULL, banned BOOL NOT NULL DEFAULT False);")
    db.commit()
    cur.close()
    print(f'Bot is up and running as {bot.user}.')

@bot.event
async def on_member_join(member):
    cur = db.cursor()
    ban_check = cur.execute(f"SELECT id, username, banned FROM pending_bans WHERE username='{member}';").fetchone()
    if ban_check:
        await member.send('You have been automatically banned from that server.')
        await member.ban(reason=BAN_REASON)
        cur.execute(f"DELETE FROM pending_bans WHERE id={ban_check[0]};")
        cur.execute(f"INSERT INTO pending_bans(username, banned) VALUES ('{member}', 1);")
        db.commit()
        print(f'Banned: {member}')
    cur.close()

@bot.command(name='ban')
@commands.guild_only()
@commands.has_permissions(ban_members=True)
async def ban(ctx, user):
    user_id = None
    if user.startswith("<@"):
        user_id = int(user.split("<@")[1].split(">")[0])
    else:
        guild_user = ctx.guild.get_member_named(user)
        if guild_user is not None:
            user_id = guild_user.id
    if user_id is None:
        cur = db.cursor()
        cur.execute(f"INSERT INTO pending_bans(username) VALUES('{user}');")
        db.commit()
        cur.close()
        await ctx.send(f'{ctx.author.mention}, `{user}` was added to the pending bans DB and will be banned if they join.')
    else:
        user = ctx.guild.get_member(user_id)
        await ctx.guild.ban(user, reason=BAN_REASON)
        print(f'Banned: {user}')
        await ctx.send(f'{ctx.author.mention}, `{user}` was in this server already and banned.')

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.channel.send(f'❌ {ctx.author.mention}, you do not have permission to ban users. ❌')
    else:
        await ctx.channel.send(f'{ctx.author.mention}, there was an error with the command you sent.  Please try again.\n`{error}`')

bot.run(TOKEN)