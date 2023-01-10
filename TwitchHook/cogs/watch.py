import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

class WebhookWatch(commands.Cog):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name='watch', description='Sets the channel for the bot to watch for webhooks')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_channel(self, interaction: discord.Interaction):
        db = sqlite3.connect('webhook_roles.db')
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        current_channel = cur.execute(f"SELECT * FROM WebhookChannels WHERE guild_id='{interaction.guild.id}';").fetchone()
        if current_channel and current_channel['channel_id'] == interaction.channel.id:
            cur.close()
            db.close()
            await interaction.response.send_message('This channel is already set as the watched channel for the bot.', ephemeral=True, delete_after=120)
        elif current_channel and current_channel['channel_id'] != interaction.channel.id and current_channel['guild_id'] == interaction.guild.id:
            cur.execute("UPDATE WebhookChannels SET channel_id=? WHERE guild_id=?;", (interaction.channel.id, interaction.guild.id))
            db.commit()
            cur.close()
            db.close()
            await interaction.response.send_message(f'{interaction.channel.mention} updated as the watched channel for the bot.', ephemeral=True)
        else:
            cur.execute("INSERT INTO WebhookChannels(guild_id, channel_id) VALUES(?,?);", (interaction.guild.id, interaction.channel.id))
            db.commit()
            cur.close()
            db.close()
            await interaction.response.send_message(f'{interaction.channel.mention} was set as the watched channel for the bot.', ephemeral=True)

async def setup(bot):
	await bot.add_cog(WebhookWatch(bot))
	print(f'cogs > {__name__[5:].upper()} loaded <')

async def teardown(bot):
	await bot.remove_cog(WebhookWatch(bot))
	print(f'cogs > {__name__[5:].upper()} unloaded <')