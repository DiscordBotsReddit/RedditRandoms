# https://www.reddit.com/r/Discord_Bots/comments/u3uprh/bot_to_manage_virtual_airline/

import os
import sqlite3

import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

TOKEN = os.getenv("REDDIT_REQUESTS")
PREFIX = "?"
DISPATCH_CHANNEL = "dispatch"

intents = discord.Intents.default()
intents.message_content = True

activity = discord.Activity(name=f"{PREFIX}help", type=discord.ActivityType.competing)
bot = commands.Bot(
    command_prefix=when_mentioned_or(PREFIX),
    intents=intents,
    description="Aircraft dispatch bot",
    activity=activity,
)


@bot.event
async def on_ready():
    print("Logged in as", bot.user)


@bot.command(name="setup")
async def setup_database(ctx):
    """Runs initial setup of the database"""
    db = sqlite3.connect("aircraft.db")
    cur = db.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS Aircraft(id INTEGER PRIMARY KEY AUTOINCREMENT, registration TEXT NOT NULL UNIQUE, type TEXT NOT NULL, airspace_id INTEGER NOT NULL, FOREIGN KEY (airspace_id) REFERENCES Airspace(id));"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS Airspace(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL);"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS Aircrew(id INTEGER PRIMARY KEY AUTOINCREMENT, discord_id INTEGER NOT NULL UNIQUE, aircraft_id INTEGER NOT NULL, FOREIGN KEY (aircraft_id) REFERENCES Aircraft(id));"
    )
    db.commit()
    cur.close()
    db.close()
    await ctx.reply("Setup complete!")


@bot.command(name="create_aircraft")
async def create_aircraft(ctx, registration: str, *, type: str):
    """create_aircraft registration type"""
    db = sqlite3.connect("aircraft.db")
    cur = db.cursor()
    airspace_id = cur.execute(
        f"SELECT id FROM Airspace WHERE guild_id='{ctx.guild.id}';"
    ).fetchone()
    if airspace_id is None:
        cur.execute(f"INSERT INTO Airspace(guild_id) VALUES({ctx.guild.id});")
        db.commit()
        airspace_id = cur.execute(
            f"SELECT id FROM Airspace WHERE guild_id='{ctx.guild.id}';"
        ).fetchone()
    aircraft_exists = cur.execute(
        f"SELECT * FROM Aircraft WHERE registration='{registration.upper()}' AND type='{type}';"
    ).fetchall()
    if len(aircraft_exists) > 0:
        await ctx.reply(
            f"`{type}` with registration `{registration.upper()}` already exists."
        )
        cur.close()
        db.close()
        return
    cur.execute(
        "INSERT INTO Aircraft(registration, type, airspace_id) VALUES(?,?,?);",
        (registration.upper(), type, airspace_id[0]),
    )
    db.commit()
    cur.close()
    db.close()
    channels = await ctx.guild.fetch_channels()
    for channel in channels:
        if channel.name.lower() == DISPATCH_CHANNEL.lower():
            channels = await ctx.guild.fetch_channels()
            for channel in channels:
                if channel.name.lower() == DISPATCH_CHANNEL.lower():
                    messages = [message async for message in channel.history()]
                    for message in messages:
                        if message.content.startswith(
                            f"Registration: `{registration.upper()}`\nType: `{type}`"
                        ):
                            await message.delete()
                            break
            await channel.send(
                f"Registration: `{registration.upper()}`\nType: `{type}`\n**Available for Use**"
            )
            await ctx.reply(
                "Aircraft created and set as available in the dispatch channel."
            )
            break


@bot.command(name="remove_aircraft")
async def remove_aircraft(ctx, registration: str):
    """remove_aircraft registration"""
    db = sqlite3.connect("aircraft.db")
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    aircraft_info = cur.execute(
        f"SELECT id, type FROM Aircraft WHERE registration='{registration.upper()}';"
    ).fetchone()
    if aircraft_info is not None:
        delete_aircrew = cur.execute(
            f"DELETE FROM Aircrew WHERE aircraft_id={aircraft_info['id']};"
        )
        delete_aircraft = cur.execute(
            f"DELETE FROM Aircraft WHERE registration='{registration.upper()}';"
        )
        db.commit()
        if delete_aircrew.rowcount > 0:
            await ctx.reply(
                f"Removed {delete_aircrew.rowcount} aircrew from their assignments."
            )
        if delete_aircraft.rowcount > 0:
            await ctx.reply(f"Removed {delete_aircraft.rowcount} aircraft from use.")
        channels = await ctx.guild.fetch_channels()
        for channel in channels:
            if channel.name.lower() == DISPATCH_CHANNEL.lower():
                channels = await ctx.guild.fetch_channels()
                for channel in channels:
                    if channel.name.lower() == DISPATCH_CHANNEL.lower():
                        messages = [message async for message in channel.history()]
                        for message in messages:
                            if message.content.startswith(
                                f"Registration: `{registration.upper()}`\nType: `{aircraft_info['type']}`"
                            ):
                                await message.delete()
                                break
    else:
        await ctx.reply(
            f"No aircraft with the registration **`{registration.upper()}`** found."
        )
        return


@bot.command(name="assign")
async def assign_aircrew(ctx, registration: str, user: discord.Member):
    """assign member-mention"""
    db = sqlite3.connect("aircraft.db")
    cur = db.cursor()
    aircraft_id = cur.execute(
        f"SELECT id, type FROM Aircraft WHERE registration='{registration.upper()}';"
    ).fetchone()
    if aircraft_id is None:
        await ctx.reply(
            f"The aircraft with registration `{registration.upper()}` was not located."
        )
        cur.close()
        db.close()
        return
    else:
        already_aircrew = cur.execute(
            f"SELECT * FROM Aircrew WHERE discord_id='{user.id}';"
        ).fetchall()
        if len(already_aircrew) > 0:
            await ctx.reply(
                f"{user.mention} is already aircrew.  Remove them from their current aircraft and try again."
            )
            cur.close()
            db.close()
            return
        cur.execute(
            "INSERT INTO Aircrew(discord_id, aircraft_id) VALUES(?,?);",
            (user.id, aircraft_id[0]),
        )
        db.commit()
        channels = await ctx.guild.fetch_channels()
        for channel in channels:
            if channel.name.lower() == DISPATCH_CHANNEL.lower():
                messages = [message async for message in channel.history()]
                for message in messages:
                    if message.content.startswith(
                        f"Registration: `{registration.upper()}`\nType: `{aircraft_id[1]}`"
                    ):
                        aircrew = []
                        aircrew_query = cur.execute(
                            f"SELECT * FROM Aircrew WHERE aircraft_id={aircraft_id[0]};"
                        ).fetchall()
                        cur.close()
                        db.close()
                        for crew in aircrew_query:
                            member = await channel.guild.fetch_member(crew[1])
                            aircrew.append(member.mention)
                        await message.edit(
                            content=f"Registration: `{registration.upper()}`\nType: `{aircraft_id[1]}`\nIn Use: {', '.join(aircrew)}"
                        )
                        await ctx.reply(
                            f"{user.mention} assigned to **`{registration.upper()}`**."
                        )
                        break


@bot.command(name="unassign")
async def remove_aircrew(ctx, user: discord.Member):
    """unassign member-mention"""
    db = sqlite3.connect("aircraft.db")
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    aircraft_info = cur.execute(
        f"SELECT Aircraft.id, Aircraft.registration, Aircraft.type FROM Aircraft LEFT JOIN Aircrew ON Aircrew.aircraft_id=Aircraft.id WHERE Aircrew.discord_id='{user.id}';"
    ).fetchone()
    delete = cur.execute(f"DELETE FROM Aircrew WHERE discord_id={user.id};")
    db.commit()
    if delete.rowcount > 0:
        channels = await ctx.guild.fetch_channels()
        for channel in channels:
            if channel.name.lower() == DISPATCH_CHANNEL.lower():
                messages = [message async for message in channel.history()]
                for message in messages:
                    if user.mention in message.content:
                        aircrew = []
                        aircrew_query = cur.execute(
                            f"SELECT * FROM Aircrew WHERE aircraft_id={aircraft_info[0]};"
                        ).fetchall()
                        cur.close()
                        db.close()
                        if len(aircrew_query) > 0:
                            for crew in aircrew_query:
                                member = ctx.guild.get_member(crew[1])
                                aircrew.append(member.mention)
                            await message.edit(
                                content=f"Registration: `{aircraft_info[1]}`\nType: `{aircraft_info[2]}`\nIn Use: {', '.join(aircrew)}"
                            )
                        else:
                            await message.edit(
                                content=f"Registration: `{aircraft_info[1]}`\nType: `{aircraft_info[2]}`\n**Available for Use**"
                            )
    await ctx.channel.send(f"{user.mention} was removed from their aircrew spot.")


bot.run(TOKEN)
