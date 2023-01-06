#https://www.reddit.com/r/Discord_Bots/comments/100yvc9/i_want_to_make_a_discord_mod_that_ping_a_role/

import discord
import os
from discord.ext import commands

## EDIT TO YOUR VALUES
PREFIX = "." # Prefix for the init and help commands
TOKEN = os.getenv("REDDIT_REQUESTS") # REPLACE WITH YOUR TOKEN
TEXT_CHANNEL_TO_PING = 'testing'
VOICE_CHANNEL_TO_WATCH = 'watch this one'
ROLE_TO_WATCH = 'Tester'
## DON'T EDIT BELOW

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

activity = discord.Activity(name=f'{PREFIX}help', type=discord.ActivityType.playing)
bot = commands.Bot(command_prefix=PREFIX, intents=intents, description="VCMonitor - Sends a message in text chat when a user joins a VC", activity=activity)

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is None or len(after.channel.members) >= 2:
        return
    if after.channel.name.lower() == VOICE_CHANNEL_TO_WATCH.lower():
        for role in member.roles:
            if role.name.lower() == ROLE_TO_WATCH.lower():
                for channel in member.guild.text_channels:
                    if channel.name.lower() == TEXT_CHANNEL_TO_PING.lower():
                        await channel.send(f'{member.display_name} has joined the `{after.channel}` voice chat.')


bot.run(TOKEN)