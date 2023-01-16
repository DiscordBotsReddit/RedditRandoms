# https://www.reddit.com/r/Discord_Bots/comments/106wndy/webhook_integration_addremove_user_role/

import os
from typing import Literal, Optional

import discord
from cogs.wheel import WheelView
from discord.ext import commands
from discord.ext.commands import Context, Greedy
from discord.ext.commands.errors import MissingPermissions

##EDIT
USER_ID = int(
    os.getenv("DISCORD_USER_ID")
)  # Change with your own user ID - USER_ID = 123456
TOKEN = os.getenv(
    "REDDIT_REQUESTS"
)  # Change with your own token - TOKEN = 'your-token'
PREFIX = "?dev "  # only used for the reload, logout, and sync commands
SERVER_STATS = "📊 Servers: "
USER_STATS = "📈 Users: "
STAT_CHANNEL = 12345
USERS_CHANNEL = 12345
##STOP EDIT

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.guilds = True

activity = discord.Activity(name=f"{PREFIX}help", type=discord.ActivityType.playing)
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(PREFIX),
    intents=intents,
    description="Wheel of Roles - Spin the wheel, win a role!",
    activity=activity,
)
bot.remove_command("help")


@bot.event
async def on_guild_join(guild):
    if bot.user.name == "RedditRequests":
        return
    else:
        stat_channel = bot.get_channel(STAT_CHANNEL)
        await stat_channel.edit(name=f"{SERVER_STATS}{len(bot.guilds)-1}")
        users_channel = bot.get_channel(USERS_CHANNEL)
        num_members = 0
        for member in bot.get_all_members():
            if member.bot or member.guild.name == "DiscoBots":
                pass
            else:
                num_members += 1
        await users_channel.edit(name=f"{USER_STATS}{num_members}")


@bot.event
async def on_guild_remove(guild):
    if bot.user.name == "RedditRequests":
        return
    else:
        stat_channel = bot.get_channel(STAT_CHANNEL)
        await stat_channel.edit(name=f"{SERVER_STATS}{len(bot.guilds)-1}")
        users_channel = bot.get_channel(USERS_CHANNEL)
        num_members = 0
        for member in bot.get_all_members():
            if member.bot or member.guild.name == "DiscoBots":
                pass
            else:
                num_members += 1
        await users_channel.edit(name=f"{USER_STATS}{num_members}")


@bot.event
async def on_ready():
    if bot.user.name == "RedditRequests":
        pass
    else:
        stat_channel = bot.get_channel(STAT_CHANNEL)
        await stat_channel.edit(name=f"{SERVER_STATS}{len(bot.guilds)-1}")
        users_channel = bot.get_channel(USERS_CHANNEL)
        num_members = 0
        for member in bot.get_all_members():
            if member.bot or member.guild.name == "DiscoBots":
                pass
            else:
                num_members += 1
        await users_channel.edit(name=f"{USER_STATS}{num_members}")
    if os.path.exists("./cogs"):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")
    bot.add_view(WheelView())
    print("Logged in as", bot.user)


@bot.command(hidden=True)
async def logout(ctx):
    """Logs the bot out and closes the script"""
    if ctx.author.id == USER_ID:
        print(f"Logout command {ctx.author}.")
        await ctx.reply("Logging out...")
        await bot.close()
    else:
        await ctx.message.delete()
        await ctx.author.send("Sorry, but you cannot use the logout command.")
        print(
            f"{ctx.author} ({ctx.author.id}) tried to log the bot out in {ctx.guild}."
        )


@bot.command(hidden=True)
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def sync(
    ctx: Context,
    guilds: Greedy[discord.Object],
    spec: Optional[Literal["~", "*", "^"]] = None,
) -> None:
    if not guilds:
        if spec == "~":  # "!sync ~" - sync current guild
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif (
            spec == "*"
        ):  # "!sync *" - copies all global app commands to current guild and syncs
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif (
            spec == "^"
        ):  # "!sync ^" - clears all commands from the current guild target and syncs (removes guild commands)
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:  # "!sync" - global sync
            synced = await ctx.bot.tree.sync()
        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return
    ret = 0
    # "!sync guild_id_1 guild_id_2" - syncs guilds with id_1 and id_2
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1
    await ctx.send(f"Synced the tree to {ret}/{len(guilds)} guilds.")


@bot.command(hidden=True)
async def reload(ctx, extension):
    """Reloads the cog specified"""
    if ctx.author.id == USER_ID:
        await ctx.message.delete()
        await bot.reload_extension(f"cogs.{extension}")
    else:
        await ctx.message.delete()
        await ctx.author.send("You don't have permission to reload cogs.")


bot.run(TOKEN)
