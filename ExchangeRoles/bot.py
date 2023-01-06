import os

import discord
from discord import app_commands

## PLEASE EDIT THESE WITH THE CORRECT VALUES
PREFIX = '.'
TOKEN = os.getenv('REDDIT_REQUESTS') # 'your-token-here'
GUILD_ID = discord.Object(id=123456789) # Replace with just the GUILD_ID
REACTION = ':yellow_heart:'


class RoleExchangeBot(discord.Client):
    def __init__(self):
        super().__init__(intents =  discord.Intents.default())
        self.intents.message_content = True
        self.intents.members = True

    async def on_ready(self):
        await tree.sync(guild=GUILD_ID)
        bot_user = bot.user.name+"#"+bot.user.discriminator
        print(f'Logged in as {bot_user} (ID: {bot.user.id})')

bot = RoleExchangeBot()
tree = app_commands.CommandTree(bot)

@tree.command(name='drop_role', description='Puts up the given role for someone to take', guild=GUILD_ID)
async def drop_role(interaction: discord.Interaction, role: discord.Role):
    has_role = False
    for user_role in interaction.user.roles:
        if user_role == role:
            has_role = True
            break
    if has_role:
        await interaction.user.remove_roles(role)
        await interaction.response.send_message(f'You put up {role.mention}.', ephemeral=True, delete_after=60)
        await interaction.channel.send(f'{interaction.user.mention} has put their {role.mention} up for grabs! First one to react with {REACTION} gets the role!')
    else:
        await interaction.response.send_message(f'You dont have the {role.mention} role to drop.', ephemeral=True, delete_after=10)

@bot.event
async def on_reaction_add(reaction, user):
    if f'First one to react with {REACTION} gets the role!' in reaction.message.content and reaction.message.author == bot.user:
        role_to_add = reaction.message.guild.get_role(int(reaction.message.content.split(" ")[4].split("<@&")[1].split(">")[0]))
        await reaction.message.delete()
        await user.add_roles(role_to_add)
        await reaction.message.channel.send(f'{user.mention} got the {role_to_add.mention} role!  Better luck next time!')
    else:
        return

bot.run(TOKEN)