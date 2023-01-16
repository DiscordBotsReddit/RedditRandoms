import discord
from discord import app_commands
from discord.ext import commands

class Valorant(commands.Cog):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name='ping', description='Pings roles +/- 3 (where able) of you to start a game')
    async def ping(self, interaction: discord.Interaction):
        v_ranks_allowed = ['Gold', 'Platinum', 'Diamond', 'Ascendant', 'Immortal', 'Radiant']
        v_ranks_disallowed = ['Iron', 'Bronze', 'Silver']
        guild_roles = {}
        for role in interaction.guild.roles:
            if role.name.split()[0] in v_ranks_allowed or role.name.split()[0] == 'Silver':
                guild_roles[role.position] = role.id
        for role in interaction.user.roles:
            if role.name.split()[0] in v_ranks_disallowed:
                await interaction.response.send_message("Sorry, you must be Gold rank or higher to use this command.", ephemeral=True, delete_after=30)
                break
            if role.name.split()[0] in v_ranks_allowed:
                keys_list = sorted(guild_roles.keys())
                ping_set = set()
                for i, v in enumerate(keys_list):
                    if v == role.position:
                        ping_set.add(interaction.guild.get_role(guild_roles[keys_list[i]]).mention)
                        for x in range(1,4):
                            try:
                                ping_set.add(interaction.guild.get_role(guild_roles[keys_list[i-x]]).mention)
                                ping_set.add(interaction.guild.get_role(guild_roles[keys_list[i+x]]).mention)
                            except:
                                pass
                ping_set = sorted(ping_set)
                await interaction.response.send_message(f'{"|".join(ping_set)}: {interaction.user.display_name} is looking for a game!')
                break

async def setup(bot):
	await bot.add_cog(Valorant(bot))
	print(f'cogs > {__name__[5:]} cog loaded')

async def teardown(bot):
	await bot.remove_cog(Valorant(bot))
	print(f'cogs > {__name__[5:]} cog unloaded')