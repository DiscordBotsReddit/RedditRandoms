#https://www.reddit.com/r/Discord_Bots/comments/zvldef/simple_bot_to_be_started_locally/

import discord
from discord.ext import commands

## PLEASE EDIT THESE WITH THE CORRECT VALUES
PREFIX = '.'
TOKEN = 'your-token-here'
ROLE_NAME_TO_KICK = 'Poo poo head'

intents =  discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, description='Role kicking bot')

@bot.command()
@commands.has_permissions(kick_members=True)
async def rolekick(ctx):
    await ctx.message.delete()
    num_kicked = 0
    for member in ctx.guild.members:
        should_kick = False
        for role in member.roles:
            if role.name.lower() == ROLE_NAME_TO_KICK.lower():
                should_kick = True
        if should_kick == True:
            await ctx.guild.kick(member)
            num_kicked += 1
            print(f'Kicked {member.name}#{member.discriminator}')
    print(f'>> DONE!  KICKED {num_kicked} USERS <<')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}.  Ready for the kicks!')

bot.run(TOKEN)