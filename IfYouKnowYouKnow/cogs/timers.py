import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands

## UPDATE THE TIMEZONE
TIMEZONE = ZoneInfo("US/Eastern")
ROLE_NAME = "Controller"


class Timer(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    group = app_commands.Group(name="timer", description="commands to manage timers")

    @group.command(name="new", description="starts a new timer for a user")
    async def new(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        years: Optional[int] = 0,
        months: Optional[int] = 0,
        weeks: Optional[int] = 0,
        days: Optional[int] = 0,
        hours: Optional[int] = 0,
        minutes: Optional[int] = 0,
        seconds: Optional[int] = 0,
    ):
        """years(365), months(30), and weeks(7) are converted to days at the rate listed.
        seconds(60) are converted to minutes at the rate listed.
        """
        db = sqlite3.connect("iykyk.db")
        cur = db.cursor()
        db_entry = cur.execute(
            f"SELECT timer_user_id, creator_user_id, time_end FROM iykyk WHERE timer_user_id={user.id}"
        ).fetchone()
        if db_entry is None:
            days = days + (years * 365) + (months * 30) + (weeks * 7)
            minutes = minutes + (seconds / 60)
            ends = datetime.now(tz=TIMEZONE) + timedelta(
                days=days, minutes=minutes, hours=hours
            )
            data = [
                user.id,
                interaction.user.id,
                ends,
            ]  # timer_user_id INTEGER, creator_user_id INTEGER, time_end DATETIME
            cur.execute(
                "INSERT INTO iykyk(timer_user_id, creator_user_id, time_end) VALUES(?,?,?)",
                data,
            )
            db.commit()
            await interaction.response.send_message(
                f'Started a timer for {user.mention} that ends {discord.utils.format_dt(ends, style="R")}.'
            )
        else:
            ends = datetime.strptime(db_entry[2], "%Y-%m-%d %H:%M:%S.%f%z")
            creator = self.bot.get_user(int(db_entry[1]))
            await interaction.response.send_message(
                f'{user.mention} already has a timer that ends {discord.utils.format_dt(ends, style="R")} that was started by {creator.mention}.'
            )
        cur.close()
        db.close()

    @group.command(name="end", description="ends a timer for a user")
    async def end(self, interaction: discord.Interaction, user: discord.User):
        controller = False
        db = sqlite3.connect("iykyk.db")
        cur = db.cursor()
        db_entry = cur.execute(
            f"SELECT creator_user_id, time_end FROM iykyk WHERE timer_user_id={user.id}"
        ).fetchone()
        if db_entry is not None:
            for role in interaction.user.roles:
                if role.name.lower() == ROLE_NAME.lower():
                    controller = True
            if int(db_entry[0]) == interaction.user.id or controller:
                ends = datetime.strptime(db_entry[1], "%Y-%m-%d %H:%M:%S.%f%z")
                cur.execute(f"DELETE FROM iykyk WHERE timer_user_id={user.id}")
                db.commit()
                await interaction.response.send_message(
                    f'{interaction.user.mention} ended the timer for {user.mention} early!  It was supposed to end {discord.utils.format_dt(ends, style="R")}.'
                )
            else:
                await interaction.response.send_message(
                    "You did not start that timer, so you cannot end it early.",
                    ephemeral=True,
                    delete_after=60,
                )
        else:
            await interaction.response.send_message(
                "That user has no active timers.", ephemeral=True, delete_after=60
            )
        cur.close()
        db.close()

    @group.command(name="edit", description="updates a timer for a user")
    async def edit(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        years: Optional[int] = 0,
        months: Optional[int] = 0,
        weeks: Optional[int] = 0,
        days: Optional[int] = 0,
        hours: Optional[int] = 0,
        minutes: Optional[int] = 0,
        seconds: Optional[int] = 0,
    ):
        controller = False
        db = sqlite3.connect("iykyk.db")
        cur = db.cursor()
        db_entry = cur.execute(
            f"SELECT creator_user_id, time_end FROM iykyk WHERE timer_user_id={user.id}"
        ).fetchone()
        if db_entry is not None:
            for role in interaction.user.roles:
                if role.name.lower() == ROLE_NAME.lower():
                    controller = True
            if int(db_entry[0]) == interaction.user.id or controller:
                days = days + (years * 365) + (months * 30) + (weeks * 7)
                minutes = minutes + (seconds / 60)
                ends = datetime.now(tz=TIMEZONE) + timedelta(
                    days=days, minutes=minutes, hours=hours
                )
                cur.execute(f"DELETE FROM iykyk WHERE timer_user_id={user.id}")
                data = [
                    user.id,
                    interaction.user.id,
                    ends,
                ]  # timer_user_id INTEGER, creator_user_id INTEGER, time_end DATETIME
                cur.execute(
                    "INSERT INTO iykyk(timer_user_id, creator_user_id, time_end) VALUES(?,?,?)",
                    data,
                )
                db.commit()
                await interaction.response.send_message(
                    f'{interaction.user.mention} has updated {user.mention}\'s timer to end {discord.utils.format_dt(ends, style="R")}!'
                )
            else:
                await interaction.response.send_message(
                    "You did not start that timer, so you cannot edit it.",
                    ephemeral=True,
                    delete_after=60,
                )
        else:
            await interaction.response.send_message(
                "That user has no active timers.", ephemeral=True, delete_after=60
            )
        cur.close()
        db.close()

    @group.command(name="remind", description="reminds a user of their timer")
    async def remind(self, interaction: discord.Interaction, user: discord.User):
        db = sqlite3.connect("iykyk.db")
        cur = db.cursor()
        db_entry = cur.execute(
            f"SELECT time_end FROM iykyk WHERE timer_user_id={user.id}"
        ).fetchone()
        if db_entry is not None:
            ends = datetime.strptime(db_entry[0], "%Y-%m-%d %H:%M:%S.%f%z")
            await interaction.response.send_message(
                f'Wow {user.mention}, looks like you are allowed to be free {discord.utils.format_dt(ends, style="R")}!'
            )
        else:
            await interaction.response.send_message(
                "That user has no active timers.", ephemeral=True, delete_after=60
            )
        cur.close()
        db.close()


async def setup(bot):
    await bot.add_cog(Timer(bot))
    print(f"{__name__[5:]} cog loaded")


async def teardown(bot):
    await bot.remove_cog(Timer(bot))
    print(f"{__name__[5:]} cog unloaded")
