import discord
from discord.ext import commands

## PLEASE EDIT THESE WITH THE CORRECT VALUES
PREFIX = '.'
TOKEN = ''
ROLE_ASSIGN_CHANNEL_ID = 1234 # Replace with just the ROLE_ASSIGN_CHANNEL_ID
GUILD_ID = 1234 # Replace with just the GUILD_ID

## YOU CAN ADD OR CHANGE THE NAMES OF THESE IF YOU WANT
## ANYTHING YOU CHANGE/ADD HERE, MAKE SURE YOU UPDATE THE CODE BELOW.  FIND+REPLACE IS YOUR FRIEND
YELLOW_ROLE_COUNT = 0
RED_ROLE_COUNT = 0


intents =  discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(command_prefix=PREFIX, intents=intents, description='Role counting bot')


@bot.event
async def on_member_update(before, after):
    global YELLOW_ROLE_COUNT
    global RED_ROLE_COUNT
    before_roles = set([role.name.lower() for role in before.roles])
    after_roles = set([role.name.lower() for role in after.roles])
    if 'yellow' in before_roles and 'yellow' not in after_roles:
        YELLOW_ROLE_COUNT -= 1
    elif 'yellow' not in before_roles and 'yellow' in after_roles:
        YELLOW_ROLE_COUNT += 1
    if 'red' in before_roles and 'red' not in after_roles:
        RED_ROLE_COUNT -= 1
    elif 'red' not in before_roles and 'red' in after_roles:
        RED_ROLE_COUNT += 1
    msg_channel = bot.get_channel(ROLE_ASSIGN_CHANNEL_ID)
    edit_msg = await msg_channel.fetch_message(role_msg.id)
    await edit_msg.edit(content=f'We have {YELLOW_ROLE_COUNT} users with the Yellow Role\nWe have {RED_ROLE_COUNT} users with the Red Role')


@bot.event
async def on_ready( ):
    global YELLOW_ROLE_COUNT
    global RED_ROLE_COUNT
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    guild = bot.get_guild(GUILD_ID)
    for member in guild.members:
        for role in member.roles:
            if role.name.lower() == "yellow":
                YELLOW_ROLE_COUNT +=1
            elif role.name.lower() == "red":
                RED_ROLE_COUNT +=1
    global role_msg
    channel = bot.get_channel(ROLE_ASSIGN_CHANNEL_ID)
    role_msg = await channel.send(f'We have {YELLOW_ROLE_COUNT} users with the Yellow Role\nWe have {RED_ROLE_COUNT} users with the Red Role')


bot.run(TOKEN)