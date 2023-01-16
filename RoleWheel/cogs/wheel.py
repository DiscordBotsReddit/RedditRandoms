import sqlite3
from random import choice

import discord
from discord import app_commands
from discord.ext import commands

DB_NAME = "role_wheel.db"


class WheelView(discord.ui.View):

    timeout = None
    spin_pressed: bool = None

    @discord.ui.button(
        label="🟢 Spin the Wheel!",
        style=discord.ButtonStyle.success,
        custom_id="spin-btn",
    )
    async def spin_wheel_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        db = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        role_amt = cur.execute(
            f"SELECT * FROM RoleWheelRoles WHERE guild_id={interaction.guild.id} AND channel_id={interaction.channel.id};"
        ).fetchall()
        if len(role_amt) == 0:
            await interaction.response.send_message(
                "Your wheel has no roles to win right now.  Please check back later.",
                ephemeral=True,
                delete_after=60,
            )
            await interaction.guild.owner.send(
                f"{interaction.user.mention} tried to spin the wheel, but there are no roles added!"
            )
            return
        spins_allowed = cur.execute(
            f"SELECT spins_allowed FROM RoleWheelOptions WHERE guild_id={interaction.guild.id};"
        ).fetchone()
        spins_left = cur.execute(
            f"SELECT spins_left FROM RoleWheelUser WHERE guild_id={interaction.guild.id} and user_id={interaction.user.id} AND channel_id={interaction.channel.id};"
        ).fetchone()
        if spins_allowed:  # check the guild has set the allowed spin limit
            if spins_left:  # user in the db already
                if spins_left["spins_left"] > 0:  # user has spins left
                    await interaction.response.send_message("Spinning!", ephemeral=True)
                    spins_left = max(spins_left["spins_left"] - 1, 0)
                    cur.execute(
                        f"UPDATE RoleWheelUser SET spins_left={spins_left} WHERE user_id={interaction.user.id} AND guild_id={interaction.guild.id};"
                    )
                    db.commit()
                    roles = cur.execute(
                        f"SELECT role_id FROM RoleWheelRoles WHERE guild_id={interaction.guild.id} AND channel_id={interaction.channel.id};"
                    ).fetchall()
                    roles = [role["role_id"] for role in roles]
                    role_id = choice(roles)
                    role_obj = interaction.guild.get_role(role_id)
                    await interaction.user.add_roles(role_obj)
                    await interaction.channel.send(
                        f"Congrats {interaction.user.mention}, you won the {role_obj.mention} role!"
                    )
                    await interaction.edit_original_response(
                        content=f"Spin complete.  You have {spins_left} left."
                    )
                else:
                    await interaction.response.send_message(
                        "You have no spins left.", ephemeral=True
                    )
            else:
                await interaction.response.send_message("Spinning!", ephemeral=True)
                cur.execute(
                    f"INSERT INTO RoleWheelUser(user_id,guild_id,spins_left) VALUES({interaction.user.id}, {interaction.guild.id}, {spins_allowed['spins_allowed']});"
                )
                db.commit()
                roles = cur.execute(
                    f"SELECT role_id FROM RoleWheelRoles WHERE guild_id={interaction.guild.id} AND channel_id={interaction.channel.id};"
                ).fetchall()
                roles = [role["role_id"] for role in roles]
                role_id = choice(roles)
                role_obj = interaction.guild.get_role(role_id)
                await interaction.user.add_roles(role_obj)
                await interaction.channel.send(
                    f"Congrats {interaction.user.mention}, you won the {role_obj.mention} role!"
                )
                await interaction.edit_original_response(
                    content=f"Spin complete.  You have {spins_allowed['spins_allowed']-1} left."
                )
        else:
            await interaction.response.send_message(
                f"{interaction.user.mention}, your admin team has not set the allowed spin number yet.  Have them use the `/setup set_spins` command and try again!\nOwner: {interaction.guild.owner.mention}"
            )
        cur.close()
        db.close()

    @discord.ui.button(
        label="Print Spins Left",
        style=discord.ButtonStyle.blurple,
        custom_id="spins-left-btn",
    )
    async def list_user_tries_left(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        db = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        spins_left = cur.execute(
            f"SELECT spins_left FROM RoleWheelUser WHERE guild_id={interaction.guild.id};"
        ).fetchone()
        spins_allowed = cur.execute(
            f"SELECT spins_allowed FROM RoleWheelOptions WHERE guild_id={interaction.guild.id};"
        ).fetchone()
        cur.close()
        db.close()
        if spins_left:
            await interaction.response.send_message(
                f"You have {spins_left['spins_left']} spin{'s' if spins_left['spins_left'] > 1 else ''} left{'!' if spins_left['spins_left'] > 0 else '.'}",
                ephemeral=True,
                delete_after=60,
            )
        elif spins_allowed:
            await interaction.response.send_message(
                f"Since you have not spun yet, you have {spins_allowed['spins_allowed']} spin{'s' if spins_allowed['spins_allowed'] > 1 else ''} left!",
                ephemeral=True,
                delete_after=60,
            )
        else:
            await interaction.response.send_message(
                f"You have not spun yet, and the admin team has not set the number of allowed spins in your guild/server yet.",
                ephemeral=True,
                delete_after=60,
            )


class RoleWheel(commands.Cog):
    """
    Manages the wheels in your guild/server\n_Optional parameters appear like [this]_
    """

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        db = sqlite3.connect(DB_NAME)
        cur = db.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS RoleWheelOptions(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, spins_allowed INTEGER NOT NULL DEFAULT 0, admin_role_allowed INTEGER NOT NULL DEFAULT 0);"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS RoleWheelUser(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL, user_id INTEGER NOT NULL, spins_left INTEGER NOT NULL);"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS RoleWheelRoles(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL, role_id INTEGER NOT NULL);"
        )
        db.commit()
        cur.close()
        db.close()

    rw_setup = app_commands.Group(
        name="wheel", description="Commands used to setup the RoleWheel bot"
    )

    @rw_setup.command(
        name="info",
        description="Shows the current roles and top 10 spins_left on the role wheel in the channel",
    )
    @commands.guild_only()
    async def rolewheel_info(
        self, interaction: discord.Interaction, channel: discord.TextChannel = None
    ):
        if channel is None:
            channel = interaction.channel
        db = sqlite3.connect(DB_NAME)
        cur = db.cursor()
        wheel_roles = cur.execute(
            f"SELECT role_id FROM RoleWheelRoles WHERE guild_id={interaction.guild.id} AND channel_id={channel.id};"
        ).fetchall()
        top_spins = cur.execute(
            f"SELECT user_id, spins_left FROM RoleWheelUser WHERE guild_id={interaction.guild.id} AND channel_id={channel.id} ORDER BY spins_left DESC LIMIT 10;"
        ).fetchall()
        cur.close()
        db.close()
        if len(wheel_roles) > 0:
            role_mentions = [
                interaction.guild.get_role(role[0]).mention for role in wheel_roles
            ]
            info_embed = discord.Embed(
                title=f"#{channel.name} Wheel Info", color=discord.Color.random()
            )
            info_embed.add_field(
                name="Roles to Win", value=", ".join(role_mentions), inline=False
            )
            info_embed.add_field(name="**Top # of Spins Left**", value="")
            for entry in top_spins:
                member = interaction.guild.get_member(entry[0])
                info_embed.add_field(
                    name=member.display_name, value=f"Spins: {entry[1]}", inline=False
                )
            await interaction.response.send_message(embed=info_embed)
        else:
            await interaction.response.send_message("Wheel currently empty.")

    @rw_setup.command(
        name="member", description="Gives the mentioned member extra spins"
    )
    @commands.guild_only()
    async def give_member_extra_spins(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        spins: int,
        channel: discord.TextChannel = None,
    ):
        if (
            interaction.user.guild_permissions.manage_guild
            or interaction.guild.name == "DiscoBots"
        ):
            if channel is None:
                channel = interaction.channel
            if spins is None or spins == 0:
                await interaction.response.send_message(
                    "You must specify the number of spins to add.",
                    ephemeral=True,
                    delete_after=20,
                )
                return
            if member is None:
                await interaction.response.send_message(
                    "You must specify a member to add spins to.",
                    ephemeral=True,
                    delete_after=20,
                )
                return
            await interaction.response.send_message(
                f"Adding {spins} spin{'s' if spins > 1 else ''} to {member.mention} in {channel.mention}."
            )
            db = sqlite3.connect(DB_NAME)
            cur = db.cursor()
            already_spun = cur.execute(
                f"SELECT spins_left FROM RoleWheelUser WHERE user_id={member.id} AND guild_id={interaction.guild.id} AND channel_id={channel.id};"
            ).fetchone()
            if already_spun:
                cur.execute(
                    f"UPDATE RoleWheelUser SET spins_left={already_spun[0]+spins} WHERE user_id={member.id} AND guild_id={interaction.guild.id} AND channel_id={channel.id};"
                )
            else:
                cur.execute(
                    f"INSERT INTO RoleWheelUser (user_id, guild_id, channel_id, spins_left) VALUES ({member.id}, {interaction.guild.id}, {channel.id}, {spins});"
                )
            db.commit()
            cur.close()
            db.close()
            await interaction.edit_original_response(
                content=f"{spins} spin{'s' if spins > 1 else ''} added to {member.mention} in {channel.mention}."
            )
        else:
            await interaction.response.send_message(
                f"You don't have permission to use the `{interaction.command.name}` command."
            )

    @rw_setup.command(name="role", description="Gives the mentioned role extra spins")
    @commands.guild_only()
    async def give_member_extra_spins(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        spins: int,
        channel: discord.TextChannel = None,
    ):
        if (
            interaction.user.guild_permissions.manage_guild
            or interaction.guild.name == "DiscoBots"
        ):
            if channel is None:
                channel = interaction.channel
            if spins is None or spins == 0:
                await interaction.response.send_message(
                    "You must specify the number of spins to add.",
                    ephemeral=True,
                    delete_after=20,
                )
                return
            if role is None:
                await interaction.response.send_message(
                    "You must specify a role to add spins to.",
                    ephemeral=True,
                    delete_after=20,
                )
                return
            await interaction.response.send_message(
                f"Adding {spins} spin{'s' if spins > 1 else ''} to {role.mention} in {channel.mention}."
            )
            db = sqlite3.connect(DB_NAME)
            cur = db.cursor()
            role_obj = interaction.guild.get_role(role.id)
            for member in role_obj.members:
                already_spun = cur.execute(
                    f"SELECT spins_left FROM RoleWheelUser WHERE user_id={member.id} AND guild_id={interaction.guild.id} AND channel_id={channel.id};"
                ).fetchone()
                if already_spun:
                    cur.execute(
                        f"UPDATE RoleWheelUser SET spins_left={already_spun[0]+spins} WHERE user_id={member.id} AND guild_id={interaction.guild.id} AND channel_id={channel.id};"
                    )
                else:
                    cur.execute(
                        f"INSERT INTO RoleWheelUser (user_id, guild_id, channel_id, spins_left) VALUES ({member.id}, {interaction.guild.id}, {channel.id}, {spins});"
                    )
                db.commit()
            cur.close()
            db.close()
            await interaction.edit_original_response(
                content=f"{spins} spin{'s' if spins > 1 else ''} added to {role.mention} in {channel.mention}."
            )
        else:
            await interaction.response.send_message(
                f"You don't have permission to use the `{interaction.command.name}` command."
            )

    @rw_setup.command(
        name="everyone",
        description="Gives the number of spins to everyone in the channel",
    )
    @commands.guild_only()
    async def set_everyones_spins(
        self,
        interaction: discord.Interaction,
        spins: int,
        channel: discord.TextChannel = None,
    ):
        if (
            interaction.user.guild_permissions.manage_guild
            or interaction.guild.name == "DiscoBots"
        ):
            if channel is None:
                channel = interaction.channel
            if spins is None or spins == 0:
                await interaction.response.send_message(
                    "You must specify the number of spins to add.",
                    ephemeral=True,
                    delete_after=20,
                )
                return
            await interaction.response.send_message(
                f"Adding {spins} spin{'s' if spins > 1 else ''} to everyone in this channel."
            )
            db = sqlite3.connect(DB_NAME)
            cur = db.cursor()
            for member in interaction.channel.members:
                has_spun = cur.execute(
                    f"SELECT spins_left FROM RoleWheelUser WHERE user_id={member.id} AND guild_id={interaction.guild.id} AND channel_id={channel.id};"
                ).fetchone()
                if has_spun:
                    cur.execute(
                        f"UPDATE RoleWheelUser SET spins_left={has_spun[0]+spins} WHERE user_id={member.id} AND guild_id={interaction.guild.id} AND channel_id={channel.id};"
                    )
                else:
                    cur.execute(
                        f"INSERT INTO RoleWheelUser (guild_id, user_id, channel_id, spins_left) VALUES ({interaction.guild.id}, {member.id}, {channel.id}, {spins});"
                    )
                db.commit()
            await interaction.edit_original_response(
                content=f"Added {spins} spin{'s' if spins > 1 else ''}  to everyone in this channel."
            )
        else:
            await interaction.response.send_message(
                f"You don't have permission to use the `{interaction.command.name}` command."
            )

    @rw_setup.command(name="set_spins", description="Set the number of spins allowed")
    @commands.guild_only()
    async def set_spins_allowed(self, interaction: discord.Interaction, spins: int = 0):
        if (
            interaction.user.guild_permissions.manage_guild
            or interaction.guild.name == "DiscoBots"
        ):
            db = sqlite3.connect(DB_NAME)
            cur = db.cursor()
            spins_set = cur.execute(
                f"SELECT spins_allowed FROM RoleWheelOptions WHERE guild_id={interaction.guild.id};"
            ).fetchone()
            if spins_set is None:
                cur.execute(
                    f"INSERT INTO RoleWheelOptions(guild_id, spins_allowed) VALUES({interaction.guild.id}, {spins});"
                )
                await interaction.response.send_message(
                    f"Set the number of spins allowed to {spins}.",
                    ephemeral=True,
                    delete_after=10,
                )
            else:
                cur.execute(
                    f"UPDATE RoleWheelOptions SET spins_allowed={spins} WHERE guild_id={interaction.guild.id};"
                )
                await interaction.response.send_message(
                    f"Updated the number of spins allowed to {spins}.",
                    ephemeral=True,
                    delete_after=10,
                )
            db.commit()
            cur.close()
            db.close()
        else:
            await interaction.response.send_message(
                f"You don't have permission to use the `{interaction.command.name}` command."
            )

    @rw_setup.command(
        name="admin_role",
        description="Allows/disallows the addition of roles with administrator permission to the wheel.",
    )
    @app_commands.choices(
        admin=[
            discord.app_commands.Choice(name="ALLOW", value=1),
            discord.app_commands.Choice(name="DISALLOW", value=0),
        ]
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def set_admin_role_opt(
        self, interaction: discord.Interaction, admin: discord.app_commands.Choice[int]
    ):
        db = sqlite3.connect(DB_NAME)
        cur = db.cursor()
        if admin.value == 1:
            opts = cur.execute(
                f"SELECT * FROM RoleWheelOptions WHERE guild_id={interaction.guild.id};"
            ).fetchone()
            if opts:
                cur.execute(
                    f"UPDATE RoleWheelOptions SET admin_role_allowed=1 WHERE guild_id={interaction.guild.id};"
                )
                await interaction.response.send_message(
                    "Roles with administrator permission are now **ALLOWED** on the wheel."
                )
            else:
                cur.execute(
                    f"INSERT INTO RoleWheelOptions(guild_id,admin_role_allowed) VALUES({interaction.guild.id},1);"
                )
                await interaction.response.send_message(
                    "Roles with administrator permission are now **ALLOWED** on the wheel."
                )
        elif admin.value == 0:
            opts = cur.execute(
                f"SELECT * FROM RoleWheelOptions WHERE guild_id={interaction.guild.id};"
            ).fetchone()
            if opts:
                cur.execute(
                    f"UPDATE RoleWheelOptions SET admin_role_allowed=0 WHERE guild_id={interaction.guild.id};"
                )
            else:
                cur.execute(
                    f"INSERT INTO RoleWheelOptions(guild_id,admin_role_allowed) VALUES({interaction.guild.id},0);"
                )
            await interaction.response.send_message(
                "Roles with administrator permission are now **DISALLOWED** on the wheel."
            )
        db.commit()
        cur.close()
        db.close()

    @rw_setup.command(name="add_role", description="Adds a role to the wheel.")
    @commands.guild_only()
    async def add_role_to_wheel(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        channel: discord.TextChannel = None,
    ):
        if (
            interaction.user.guild_permissions.manage_guild
            or interaction.guild.name == "DiscoBots"
        ):
            if channel is None:
                channel = interaction.channel
            db = sqlite3.connect(DB_NAME)
            cur = db.cursor()
            db.row_factory = sqlite3.Row
            admin_allowed = cur.execute(
                f"SELECT admin_role_allowed FROM RoleWheelOptions WHERE guild_id={interaction.guild.id};"
            ).fetchone()
            if admin_allowed and admin_allowed[0] == 0:
                if role.permissions.administrator or role.permissions.manage_guild:
                    await interaction.response.send_message(
                        f"{role.mention} has administrator permissions and that is disabled in your guild's settings.  Enable it with `/wheel_setup admin_role` and add the role again."
                    )
                    return
            if admin_allowed is None:
                cur.execute(
                    f"INSERT INTO RoleWheelOptions (guild_id, admin_role_allowed) VALUES ({interaction.guild.id}, 0);"
                )
                db.commit()
                await interaction.response.send_message(
                    f"{role.mention} has administrator permissions and that is disabled by default.  Enable it with `/wheel_setup admin_role` and add the role again."
                )
                cur.close()
                db.close()
                return
            existing_role = cur.execute(
                f"SELECT * FROM RoleWheelRoles WHERE guild_id={interaction.guild.id} AND role_id={role.id} AND channel_id={channel.id};"
            ).fetchone()
            if existing_role is None:
                cur.execute(
                    f"INSERT INTO RoleWheelRoles(guild_id, role_id, channel_id) VALUES({interaction.guild.id}, {role.id}, {channel.id});"
                )
                db.commit()
                await interaction.response.send_message(
                    f"{role.mention} added to the wheel."
                )
            else:
                await interaction.response.send_message(
                    f"{role.mention} was already on the wheel."
                )
            cur.close()
            db.close()
            messages = [message async for message in channel.history()]
            for message in messages:
                if (
                    "https://i.pinimg.com/originals/94/cc/d5/94ccd56f2a24d1eb9486d86fcee0b3b1.gif"
                    in message.content
                    and message.author == self.bot.user
                ):
                    await message.edit(
                        content="https://i.pinimg.com/originals/94/cc/d5/94ccd56f2a24d1eb9486d86fcee0b3b1.gif"
                    )
        else:
            await interaction.response.send_message(
                f"You don't have permission to use the `{interaction.command.name}` command."
            )

    @rw_setup.command(name="remove_role", description="Removes a role from the wheel.")
    @commands.guild_only()
    async def remove_role_from_wheel(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        channel: discord.TextChannel = None,
    ):
        if (
            interaction.user.guild_permissions.manage_guild
            or interaction.guild.name == "DiscoBots"
        ):
            if channel is None:
                channel = interaction.channel
            db = sqlite3.connect(DB_NAME)
            cur = db.cursor()
            db.row_factory = sqlite3.Row
            existing_role = cur.execute(
                f"SELECT * FROM RoleWheelRoles WHERE guild_id={interaction.guild.id} AND role_id={role.id} AND channel_id={channel.id};"
            ).fetchone()
            if existing_role is not None:
                cur.execute(
                    f"DELETE FROM RoleWheelRoles WHERE guild_id={interaction.guild.id} AND role_id={role.id} AND channel_id={channel.id};"
                )
                db.commit()
                await interaction.response.send_message(
                    f"{role.mention} removed from the wheel in {channel.mention}."
                )
            else:
                await interaction.response.send_message(
                    f"{role.mention} was not on the wheel in {channel.mention}."
                )
            cur.close()
            db.close()
        else:
            await interaction.response.send_message(
                f"You don't have permission to use the `{interaction.command.name}` command."
            )

    @rw_setup.command(name="send_wheel", description="Sends the wheel to the channel.")
    @commands.guild_only()
    async def send_wheel_message_to_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel = None
    ):
        if (
            interaction.user.guild_permissions.manage_guild
            or interaction.guild.name == "DiscoBots"
        ):
            if channel is None:
                channel = interaction.channel
            db = sqlite3.connect(DB_NAME)
            cur = db.cursor()
            roles = cur.execute(
                f"SELECT * FROM RoleWheelRoles WHERE guild_id={interaction.guild.id} AND channel_id={channel.id};"
            ).fetchall()
            cur.close()
            db.close()
            wheel_gif = "https://i.pinimg.com/originals/94/cc/d5/94ccd56f2a24d1eb9486d86fcee0b3b1.gif"
            view = WheelView()
            if len(roles) > 0:
                await channel.send(view=view, content=wheel_gif)
            else:
                await channel.send(
                    view=view, content="⛔ WHEEL CURRENTLY HAS NO ROLES ⛔\n" + wheel_gif
                )
            await interaction.response.send_message(
                f"Wheel sent to {channel.mention}.", ephemeral=True, delete_after=10
            )
        else:
            await interaction.response.send_message(
                f"You don't have permission to use the `{interaction.command.name}` command."
            )

    @rw_setup.command(
        name="clear", description="Clears all roles and spins in the channel."
    )
    @commands.guild_only()
    async def clear_wheel(
        self, interaction: discord.Interaction, channel: discord.TextChannel = None
    ):
        if (
            interaction.user.guild_permissions.manage_guild
            or interaction.guild.name == "DiscoBots"
        ):
            if channel is None:
                channel = interaction.channel
            db = sqlite3.connect(DB_NAME)
            cur = db.cursor()
            cur.execute(
                f"DELETE FROM RoleWheelRoles WHERE guild_id={interaction.guild.id} AND channel_id={channel.id};"
            )
            cur.execute(
                f"DELETE FROM RoleWheelUser WHERE guild_id={interaction.guild.id} AND channel_id={channel.id};"
            )
            db.commit()
            cur.close()
            db.close()
            messages = [message async for message in channel.history()]
            for message in messages:
                if (
                    "https://i.pinimg.com/originals/94/cc/d5/94ccd56f2a24d1eb9486d86fcee0b3b1.gif"
                    in message.content
                    and message.author == self.bot.user
                ):
                    await message.edit(
                        content="⛔ WHEEL CURRENTLY OFFLINE ⛔\nhttps://i.pinimg.com/originals/94/cc/d5/94ccd56f2a24d1eb9486d86fcee0b3b1.gif"
                    )
            await interaction.response.send_message(
                "Cleared all spins and roles from the wheel in this channel."
            )
        else:
            await interaction.response.send_message(
                f"You don't have permission to use the `{interaction.command.name}` command."
            )


async def setup(bot):
    await bot.add_cog(RoleWheel(bot))
    print(f"cogs > {__name__[5:].upper()} loaded <")


async def teardown(bot):
    await bot.remove_cog(RoleWheel(bot))
    print(f"cogs > {__name__[5:].upper()} unloaded <")
