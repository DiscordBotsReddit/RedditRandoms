import os
from typing import Literal

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

DB = os.path.join(os.getcwd(), "house_points.db")

intents = discord.Intents.none()
intents.guilds = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("hp>"), intents=intents)


@bot.event
async def on_ready():
    if not os.path.exists(DB):
        with open(DB, "w") as f:
            f.write("")
    async with aiosqlite.connect(DB) as db:
        async with db.cursor() as cur:
            await cur.execute(
                "CREATE TABLE IF NOT EXISTS team_members(id INTEGER PRIMARY KEY AUTOINCREMENT,guild_id INTEGER NOT NULL,user_id INTEGER NOT NULL,team_id INTEGER NOT NULL,FOREIGN KEY (team_id) REFERENCES house_team (team_id));"
            )
            await cur.execute(
                "CREATE TABLE IF NOT EXISTS teams(team_id INTEGER PRIMARY KEY AUTOINCREMENT,guild_id INTEGER NOT NULL,team_name TEXT NOT NULL,leader_id INTEGER NOT NULL,cur_points INTEGER NOT NULL DEFAULT 0,icon TEXT);"
            )
            await db.commit()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}.")


#########################################
### Modify points, points leaderboard ###
#########################################


@bot.tree.command(name="points", description="Modifies the points of the team.")
@app_commands.describe(name="Team name")
@app_commands.describe(points="Use a negative number to remove points.")
async def give_points(interaction: discord.Interaction, name: str, points: int):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.cursor() as cur:
            team_exists_check = await cur.execute(
                f"SELECT * FROM teams WHERE guild_id={interaction.guild_id} AND team_name='{name.lower()}';"
            )
            team_exists_check = await team_exists_check.fetchone()
            if team_exists_check is None:
                return await interaction.response.send_message(
                    f"The team `{name}` does not exist on this server.",
                    ephemeral=True,
                )
            else:
                new_points = team_exists_check["cur_points"] + points
                if new_points < 0:
                    new_points = 0
                await cur.execute(
                    f"UPDATE teams SET cur_points={new_points} WHERE team_id={team_exists_check['team_id']};"
                )
                await db.commit()
    if points < 0:
        embed_title = f"Points Removed from Team {name.capitalize()}!"
        embed_color = (255, 0, 0)
    else:
        embed_title = f"Points Awarded to Team {name.capitalize()}!"
        embed_color = (255, 223, 0)
    points_embed = discord.Embed(
        title=embed_title,
        color=discord.Color.from_rgb(*embed_color),
        description=f"Points modified by {interaction.user.mention}",
    )
    if team_exists_check["icon"] is not None:
        points_embed.set_thumbnail(url=team_exists_check["icon"])
    points_embed.add_field(name="Points Change", value=points)
    points_embed.add_field(name="Total Points", value=new_points)
    await interaction.response.send_message(embed=points_embed)


@bot.tree.command(name="leaderboard", description="Shows the top 25 teams by points")
async def leaderboard(interaction: discord.Interaction):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.cursor() as cur:
            top_25 = await cur.execute(
                f"SELECT * FROM teams WHERE guild_id={interaction.guild_id} ORDER BY cur_points DESC LIMIT 25;"
            )
            top_25 = await top_25.fetchall()
    if top_25 is None:
        return await interaction.response.send_message(
            "No teams created yet.", ephemeral=True, delete_after=20
        )
    lb_embed = discord.Embed(
        title=f"{interaction.guild.name} - Teams Leaderboard",
        color=discord.Color.random(),
    )
    if interaction.guild.icon.url is not None:
        lb_embed.set_thumbnail(url=interaction.guild.icon.url)
    for team in top_25:
        lb_embed.add_field(
            name=str(team["team_name"]).capitalize(),
            value=f'{team["cur_points"]:,}',
            inline=False,
        )
    await interaction.response.send_message(embed=lb_embed)


######################################################
### New team, join team, leave team, discband team ###
######################################################


@bot.tree.command(
    name="new_team", description="Create a new team with yourself as the leader."
)
@app_commands.describe(icon="An image file that is the icon for your team.")
@app_commands.describe(name="Your team's name.")
async def create_new_team(
    interaction: discord.Interaction, name: str, icon: discord.Attachment = None
):
    if icon is not None and not icon.content_type.startswith("image/"):
        return await interaction.response.send_message(
            "`icon` must be an image file.", ephemeral=True, delete_after=20
        )
    icon_upload = await icon.to_file(
        filename=f"{name}-icon.png", description=f"Team icon for {name}"
    )
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.cursor() as cur:
            current_team_leader = await cur.execute(
                f"SELECT team_name FROM teams WHERE guild_id={interaction.guild_id} AND leader_id={interaction.user.id};"
            )
            current_team_leader = await current_team_leader.fetchone()
            if current_team_leader is not None:
                return await interaction.response.send_message(
                    f"You are already the leader of `{current_team_leader['team_name']}`.",
                    ephemeral=True,
                    delete_after=20,
                )
            already_on_team = await cur.execute(
                f"SELECT team_id FROM team_members WHERE guild_id={interaction.guild_id} AND user_id={interaction.user.id};"
            )
            already_on_team = await already_on_team.fetchone()
            if already_on_team is not None:
                return await interaction.response.send_message(
                    "You are already on a team.  Leave that team before creating a new one.",
                    ephemeral=True,
                    delete_after=20,
                )
            team_exists = await cur.execute(
                f"SELECT * FROM teams WHERE guild_id={interaction.guild_id} AND team_name='{name.lower()}'"
            )
            team_exists = await team_exists.fetchone()
            if team_exists is not None:
                return await interaction.response.send_message(
                    f"A team named `{name.lower()}` already exists on this server.  Please try again with a new name.",
                    ephemeral=True,
                    delete_after=20,
                )
            await cur.execute(
                f"INSERT INTO teams(guild_id,team_name,leader_id) VALUES({interaction.guild_id}, '{name.lower()}', {interaction.user.id});"
            )
            await db.commit()
            team_id = await cur.execute(
                f"SELECT team_id FROM teams WHERE guild_id={interaction.guild_id} AND leader_id={interaction.user.id};"
            )
            team_id = await team_id.fetchone()
            await interaction.response.send_message(
                f"{interaction.user.mention} is now the leader of `{name}`!",
                file=icon_upload,
            )
            async for msg in interaction.channel.history(limit=1):
                if len(msg.attachments) > 0:
                    await cur.execute(
                        f"UPDATE teams SET icon='{msg.attachments[0]}' WHERE team_id={team_id['team_id']};"
                    )
            await cur.execute(
                f"INSERT INTO team_members(guild_id,user_id,team_id) VALUES({interaction.guild_id},{interaction.user.id},{team_id['team_id']});"
            )
            await db.commit()


@bot.tree.command(
    name="disband_team", description="Disbands the team if you are the leader."
)
@app_commands.describe(
    double_check="This operation deletes your team and all the points they have earned."
)
async def disband_team(
    interaction: discord.Interaction, double_check: Literal["no", "yes"]
):
    if double_check == "yes":
        async with aiosqlite.connect(DB) as db:
            db.row_factory = aiosqlite.Row
            async with db.cursor() as cur:
                team_id = await cur.execute(
                    f"SELECT team_id FROM teams WHERE guild_id={interaction.guild_id} AND leader_id={interaction.user.id};"
                )
                team_id = await team_id.fetchone()
                if team_id is None:
                    return await interaction.response.send_message(
                        "You don't have a team to disband.",
                        ephemeral=True,
                        delete_after=20,
                    )
                await cur.execute(
                    f"DELETE FROM teams WHERE guild_id={interaction.guild_id} AND leader_id={interaction.user.id};"
                )
                await cur.execute(
                    f"DELETE FROM team_members WHERE guild_id={interaction.guild_id} AND team_id={team_id['team_id']};"
                )
                await db.commit()
        await interaction.response.send_message(
            f"{interaction.user.mention} has disbanded their team and forfeit all their points."
        )
    else:
        await interaction.response.send_message(
            "No teams were disbaned.", ephemeral=True, delete_after=20
        )


@bot.tree.command(name="join", description="Request to join a team!")
@app_commands.describe(name="The name of the team you want to join (case insensitive).")
async def join_team(interaction: discord.Interaction, name: str):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.cursor() as cur:
            already_on_team = await cur.execute(
                f"SELECT team_id FROM team_members WHERE guild_id={interaction.guild_id} AND user_id={interaction.user.id};"
            )
            already_on_team = await already_on_team.fetchone()
            if already_on_team is not None:
                return await interaction.response.send_message(
                    "You are already on a team.  Leave that team before joining a new one.",
                    ephemeral=True,
                    delete_after=20,
                )
            already_team_leader = await cur.execute(
                f"SELECT leader_id FROM teams WHERE guild_id={interaction.guild_id} AND leader_id={interaction.user.id};"
            )
            already_team_leader = await already_team_leader.fetchone()
            if already_team_leader is not None:
                return await interaction.response.send_message(
                    "You are already a team leader.  Disband that team before joining a new one.",
                    ephemeral=True,
                    delete_after=20,
                )
            team_leader_id = await cur.execute(
                f"SELECT leader_id FROM teams WHERE guild_id={interaction.guild_id} AND team_name='{name.lower()}';"
            )
            team_leader_id = await team_leader_id.fetchone()

    if team_leader_id is not None:
        team_leader = await interaction.guild.fetch_member(
            int(team_leader_id["leader_id"])
        )

        class ManageRequestButtons(discord.ui.View):
            def __init__(self, team_leader: discord.Member, team_name: str):
                super().__init__()
                self.team_leader = team_leader
                self.team_name = team_name

            @discord.ui.button(  # type: ignore
                label="Approve", style=discord.ButtonStyle.green, emoji="✅"
            )
            async def approve_button(
                self, interaction: discord.Interaction, button: discord.Button
            ):
                if interaction.user == self.team_leader:
                    await interaction.message.delete()
                    for member in interaction.message.mentions:
                        if member != self.team_leader:
                            async with aiosqlite.connect(DB) as db:
                                db.row_factory = aiosqlite.Row
                                async with db.cursor() as cur:
                                    team_id = await cur.execute(
                                        f"SELECT team_id FROM teams WHERE guild_id={interaction.guild_id} AND leader_id={self.team_leader.id};"
                                    )
                                    team_id = await team_id.fetchone()
                                    await cur.execute(
                                        f"INSERT INTO team_members(guild_id,user_id,team_id) VALUES({interaction.guild_id},{member.id},{team_id['team_id']});"
                                    )
                                    await db.commit()
                            await interaction.response.send_message(
                                f"{member.mention} was added to your team.",
                                ephemeral=True,
                            )
                            return await member.send(
                                f"You were approved to join the `{self.team_name}` team!"
                            )
                else:
                    await interaction.response.send_message(
                        "You aren't the team leader.", ephemeral=True, delete_after=20
                    )

            @discord.ui.button(  # type: ignore
                label="Deny", style=discord.ButtonStyle.red, emoji="✖"
            )
            async def deny_button(
                self, interaction: discord.Interaction, button: discord.Button
            ):
                if interaction.user == self.team_leader:
                    await interaction.message.delete()
                    for member in interaction.message.mentions:
                        if member != self.team_leader:
                            await interaction.response.send_message(
                                f"{member.mention} was denied from joining your team.",
                                ephemeral=True,
                            )
                            return await member.send(
                                f"You were denied from joining the `{self.team_name}` team."
                            )
                else:
                    await interaction.response.send_message(
                        "You aren't the team leader.", ephemeral=True, delete_after=20
                    )

        manage_btns = ManageRequestButtons(team_leader, name.lower())
        await interaction.response.send_message(
            f"{interaction.user.mention} has requested to join `{name}` led by {team_leader.mention}.",
            view=manage_btns,
        )
    else:
        return await interaction.response.send_message(
            f"The team `{name}` does not exist.", ephemeral=True, delete_after=20
        )


@bot.tree.command(name="leave", description="Leave your current team.")
async def leave_team(
    interaction: discord.Interaction, double_check: Literal["no", "yes"]
):
    if double_check == "yes":
        async with aiosqlite.connect(DB) as db:
            db.row_factory = aiosqlite.Row
            async with db.cursor() as cur:
                await cur.execute(
                    f"DELETE FROM team_members WHERE user_id={interaction.user.id} AND guild_id={interaction.guild_id};"
                )
                await db.commit()
        await interaction.response.send_message(
            f"{interaction.user.mention} left their team!"
        )
    else:
        await interaction.response.send_message(
            "You did not leave your team.", ephemeral=True, delete_after=20
        )


bot.run(os.environ["BOT_TOKEN"])
