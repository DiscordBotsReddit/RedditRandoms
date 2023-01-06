import os
import time

import discord
from discord import app_commands


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        async for guild in bot.fetch_guilds():
            sync_guild = discord.Object(id=guild.id)
            self.tree.clear_commands(guild=sync_guild)
            self.tree.copy_global_to(guild=sync_guild)
            synced = await self.tree.sync(guild=sync_guild)
            print(f'> Synced {len(synced)} commands to {guild.name}.')

intents = discord.Intents.default()
intents.guilds = True
intents.guild_scheduled_events = True
intents.members = True
bot = MyClient(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.tree.command(description='Pings users who are interested in an event but not in the event channel')
@app_commands.describe(event_name='Case insensitive as long as spelling is right')
async def evping(interaction: discord.Interaction, event_name: str):
    start = time.perf_counter()
    found = False
    interested_users = set()
    await interaction.response.send_message('Please wait, this takes ~11 seconds due to Discord API limits.', ephemeral=True)
    events = await interaction.guild.fetch_scheduled_events()
    for event in events:
        if event.name.lower() == event_name.lower():
            found = True
            if event.creator == interaction.user:
                async for user in event.users():
                    if user not in event.channel.members:
                        interested_users.add(user.mention)
                interested_users = sorted(interested_users)
                await interaction.channel.send(content=f'{"|".join(interested_users)}: {interaction.user.display_name}\'s event is starting and you aren\'t in the channel yet!')
                break
            else:
                await interaction.edit_original_response('Only the event creator can ping the missing members.')
    if found == False:
        await interaction.edit_original_response(content='No event with that name found')
    end = time.perf_counter()
    await interaction.edit_original_response(content=f'Event ping completed in {end - start:0.2f} seconds.')

bot.run(os.getenv("REDDIT_REQUESTS"))