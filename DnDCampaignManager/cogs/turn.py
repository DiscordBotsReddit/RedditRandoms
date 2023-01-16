import sqlite3

import discord
from discord import app_commands
from discord.ext import commands


class CampaignTurn(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.db = sqlite3.connect("dnd.db")
        self.db.row_factory = sqlite3.Row
        self.cur = self.db.cursor()
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS Timers(id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER UNIQUE NOT NULL, FOREIGN KEY (campaign_id) REFERENCES Campaign(id));"
        )
        self.cur.close()
        self.db.close()


async def setup(bot):
    await bot.add_cog(CampaignTurn(bot))
    print(f"cogs > {__name__[5:].upper()} cog loaded <")


async def teardown(bot):
    await bot.remove_cog(CampaignTurn(bot))
    print(f"cogs > {__name__[5:].upper()} cog unloaded <")
