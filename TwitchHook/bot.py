# https://www.reddit.com/r/Discord_Bots/comments/106wndy/webhook_integration_addremove_user_role/

import os
from typing import Literal, Optional
import sqlite3

import discord
from discord.ext import commands
from discord.ext.commands import Context, Greedy

##EDIT
USER_ID = os.getenv("DISCORD_USER_ID")
TOKEN = os.getenv("REDDIT_REQUESTS") # Change with your own token
PREFIX = '?'
##STOP EDIT

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True

activity = discord.Activity(name=f'for {PREFIX}', type=discord.ActivityType.watching)
bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), intents=intents, description='Monitors the channel for webhook activity', activity=activity)

@bot.event
async def on_message(message):
    if message.webhook_id and message.guild is not None and type(message.channel) == discord.channel.TextChannel:
        await message.delete()
        db = sqlite3.connect('webhook_roles.db')
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        watched_channel = cur.execute("SELECT * FROM WebhookChannels WHERE guild_id=? and channel_id=?;", (message.guild.id, message.channel.id)).fetchone()
        if watched_channel:
            try:
                if "addrole" in message.content.lower():
                    member = message.guild.get_member(int(message.content.split()[1]))
                    role_name = message.content.split()[2]
                    guild_roles = await message.guild.fetch_roles()
                    for role in guild_roles:
                        if role.name.lower() == role_name.lower():
                            await member.add_roles(role, reason='Webhook automatic add')
                            await message.channel.send(f'(ADD) MEMBER: {member.mention}\nROLE: {role.mention}')
                            break
                elif "removerole" in message.content.lower():
                    member = message.guild.get_member(int(message.content.split()[1]))
                    role_name = message.content.split()[2]
                    guild_roles = await message.guild.fetch_roles()
                    for role in guild_roles:
                        if role.name.lower() == role_name.lower():
                            await member.remove_roles(role, reason='Webhook automatic add')
                            await message.channel.send(f'(REMOVE) MEMBER: {member.mention}\nROLE: {role.mention}')
                            break
            except Exception as error:
                await message.author.send(f"**There was an error in updating the role**:\n{error}")
    else:
        await bot.process_commands(message)

@bot.event
async def on_ready():
    if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await bot.load_extension(f'cogs.{filename[:-3]}')
    db = sqlite3.connect('webhook_roles.db')
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS WebhookChannels(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL UNIQUE, channel_id INTEGER NOT NULL UNIQUE);")
    cur.close()
    db.close()
    print('Logged in as', bot.user)

@bot.command(hidden=True)
async def logout(ctx):
    ''' Logs the bot out and closes the script
    '''
    if ctx.message.author.id == USER_ID:
        print(f"Logout command {ctx.message.author}.")
        await ctx.reply("Logging out...")
        await bot.close()
    else:
        await ctx.message.delete()
        await ctx.author.send("Sorry, but you cannot use the logout command.")
        print(f'{ctx.author} tried to log the bot out in {ctx.guild}.')

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

@bot.command(hidden=True)
@commands.has_permissions(manage_guild=True)
async def reload(ctx, extension):
	''' Reloads the cog specified
	'''
	await ctx.message.delete()
	await bot.reload_extension(f'cogs.{extension}')

bot.run(TOKEN)