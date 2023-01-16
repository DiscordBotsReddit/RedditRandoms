import sqlite3

import discord
from discord import app_commands
from discord.ext import commands


class CampaignManagement(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.db = sqlite3.connect("dnd.db")
        self.cur = self.db.cursor()
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS Campaign(id INTEGER PRIMARY KEY AUTOINCREMENT, dm_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, title TEXT NOT NULL);"
        )
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS Player(id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER NOT NULL, campaign_id INTEGER UNIQUE NOT NULL, FOREIGN KEY (campaign_id) REFERENCES Campaign(id));"
        )
        self.cur.close()
        self.db.close()

    @app_commands.command(
        name="campaign-setup",
        description="Basic campaign setup.  Players are optional, but recommended.",
    )
    @app_commands.describe(
        player1="Discord mention for a player you want to add to the campaign."
    )
    @app_commands.describe(
        player2="Discord mention for a player you want to add to the campaign."
    )
    @app_commands.describe(
        player3="Discord mention for a player you want to add to the campaign."
    )
    @app_commands.describe(
        player4="Discord mention for a player you want to add to the campaign."
    )
    @app_commands.describe(
        player5="Discord mention for a player you want to add to the campaign."
    )
    @app_commands.describe(
        player6="Discord mention for a player you want to add to the campaign."
    )
    async def setup(
        self,
        interaction: discord.Interaction,
        title: str,
        player1: discord.Member = None,
        player2: discord.Member = None,
        player3: discord.Member = None,
        player4: discord.Member = None,
        player5: discord.Member = None,
        player6: discord.Member = None,
    ):
        players = set()
        self.db = sqlite3.connect("dnd.db")
        self.db.row_factory = sqlite3.Row
        if player1 is not None:
            players.add(player1)
        if player2 is not None:
            players.add(player2)
        if player3 is not None:
            players.add(player3)
        if player4 is not None:
            players.add(player4)
        if player5 is not None:
            players.add(player5)
        if player6 is not None:
            players.add(player6)
        if title is None:
            await interaction.response.send_message(
                "Please run the command again and enter a title for your campaign.",
                ephemeral=True,
                delete_after=60,
            )
        else:
            try:
                self.cur = self.db.cursor()
                campaign = self.cur.execute(
                    "SELECT * FROM Campaign WHERE guild_id=? AND lower(title)=?;",
                    (interaction.guild.id, title.lower()),
                ).fetchone()
                if campaign:
                    await interaction.response.send_message(
                        f"There is already a campaign on this server called `{campaign['title']}`.  Please choose another name and try again.",
                        ephemeral=True,
                        delete_after=60,
                    )
                    self.cur.close()
                else:
                    self.cur.execute(
                        "INSERT INTO Campaign(dm_id, guild_id, title) VALUES (?,?,?);",
                        (interaction.user.id, interaction.guild.id, title),
                    )
                    self.db.commit()
                    camp_embed = discord.Embed(
                        title=f"**{title}**", color=interaction.user.accent_color
                    )
                    camp_embed.set_thumbnail(url=interaction.guild.icon.url)
                    campaign = self.cur.execute(
                        "SELECT * FROM Campaign WHERE guild_id=? AND lower(title)=?;",
                        (interaction.guild.id, title.lower()),
                    ).fetchone()
                    if len(players) > 0:
                        for index, player in enumerate(players):
                            self.cur.execute(
                                "INSERT OR IGNORE INTO Player(player_id, campaign_id) VALUES(?,?);",
                                (player.id, campaign["id"]),
                            )
                            camp_embed.add_field(
                                name=f"Player #{index+1}",
                                value=player.mention,
                                inline=False,
                            )
                    self.cur.close()
                    await interaction.response.send_message(
                        embed=camp_embed,
                        content=f"{interaction.user.mention} started a new campaign!",
                    )
                    self.db.close()
            except Exception as e:
                await interaction.response.send_message(
                    f"There was an error setting up your campaign:\n{e}"
                )


async def setup(bot):
    await bot.add_cog(CampaignManagement(bot))
    print(f"cogs > {__name__[5:].upper()} cog loaded <")


async def teardown(bot):
    await bot.remove_cog(CampaignManagement(bot))
    print(f"cogs > {__name__[5:].upper()} cog unloaded <")
