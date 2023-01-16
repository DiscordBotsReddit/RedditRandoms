# https://www.reddit.com/r/discordbots/comments/109eu1y/is_there_a_bot_on_discord_that_logs_deleted/

import os
import sqlite3

import discord
from discord.ext import commands

TOKEN = os.getenv("REDDIT_REQUESTS")
DB_NAME = "ids_to_log.db"
PREFIX = "?"

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    description="Logs deleted messages from users specified",
)


@bot.event
async def on_ready():
    db = sqlite3.connect(DB_NAME)
    cur = db.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS Users(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, num_deleted INTEGER NOT NULL DEFAULT 0);"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS LogChannel(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL UNIQUE);"
    )
    db.commit()
    cur.close()
    db.close()
    print("Logged in as", bot.user)


@bot.command(name="add_user")
@commands.has_permissions(manage_guild=True)
async def start_logging_deleted_messages(ctx, member: discord.Member = None):
    """Adds the user mentioned to the watchlist"""
    if member is None:
        await ctx.reply("You must mention a member to log deleted messages from.")
        return
    else:
        db = sqlite3.connect(DB_NAME)
        cur = db.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO Users(user_id, guild_id) VALUES(?,?);",
            (member.id, ctx.guild.id),
        )
        db.commit()
        cur.close()
        db.close()
        await ctx.reply(f"{member.mention}'s deleted messages are now being logged.")


@bot.command(name="remove_user")
@commands.has_permissions(manage_guild=True)
async def stop_logging_deleted_messages(ctx, member: discord.Member = None):
    """Removes the member mentioned from the watchlist"""
    if member is None:
        await ctx.reply("You must mention a member to log deleted messages from.")
        return
    else:
        db = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        deleted = cur.execute(
            f"DELETE FROM Users WHERE user_id={member.id} AND guild_id={ctx.guild.id};"
        )
        db.commit()
        if deleted.rowcount > 0:
            await ctx.reply(
                f"{member.mention}'s deleted messages are no longer being logged."
            )
        else:
            await ctx.reply(
                f"{member.mention} was not in the database to have their messages logged."
            )


@bot.command(name="set_logs")
@commands.has_permissions(manage_guild=True)
async def set_logging_output_channel(ctx, channel: discord.TextChannel = None):
    """If ran with no channel mention supplied, uses the channel the command is run in"""
    if channel is None:
        channel = ctx.channel
    db = sqlite3.connect(DB_NAME)
    cur = db.cursor()
    existing_channel = cur.execute(
        f"SELECT channel_id FROM LogChannel WHERE guild_id={ctx.guild.id};"
    ).fetchone()
    if existing_channel:
        cur.execute(
            f"UPDATE LogChannel SET channel_id={channel.id} WHERE guild_id={ctx.guild.id};"
        )
        db.commit()
        cur.close()
        db.close()
        await ctx.reply(f"Your log output channel was updated to {channel.mention}.")
    else:
        cur.execute(
            f"INSERT INTO LogChannel(channel_id, guild_id) VALUES(?,?);",
            (channel.id, ctx.guild.id),
        )
        db.commit()
        cur.close()
        db.close()
        await ctx.reply(f"Your log output channel was set to {channel.mention}.")


@bot.event
async def on_raw_message_delete(payload):
    db = sqlite3.connect(DB_NAME)
    cur = db.cursor()
    output_channel = cur.execute(
        f"SELECT channel_id FROM LogChannel WHERE guild_id={payload.guild_id};"
    ).fetchone()
    if output_channel is None:
        cur.close()
        db.close()
        await message.guild.owner.send(
            f"Your deleted message log channel is not configured.  Use `{PREFIX}set_logs <channel: optional>` with either mentioning the channel in the command or with no channel option in the channel you want the logs to be posted."
        )
        return
    guild = bot.get_guild(payload.guild_id)
    output_channel = guild.get_channel(output_channel[0])
    if payload.cached_message is None:
        cur.close()
        db.close()
        await output_channel.send(
            "A message was deleted, however it was sent while the bot was offline and is not able to be logged."
        )
        return
    message = payload.cached_message
    watched_user = cur.execute(
        f"SELECT num_deleted FROM Users WHERE user_id={message.author.id} AND guild_id={message.guild.id};"
    ).fetchone()
    if watched_user:
        cur.execute(
            f"UPDATE Users SET num_deleted={watched_user[0]+1} WHERE user_id={message.author.id} AND guild_id={message.guild.id};"
        )
        db.commit()
        cur.close()
        db.close()
        embed = discord.Embed(
            color=discord.Color.random(),
            title=f"New deleted message from {message.author.display_name}",
        )
        embed.add_field(name="Message", value=message.content, inline=False)
        embed.add_field(
            name="Total Deleted Messages", value=watched_user[0], inline=False
        )
        await output_channel.send(embed=embed)
        return


bot.run(TOKEN)
