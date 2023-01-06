# https://www.reddit.com/r/Discord_Bots/comments/103vhy3/is_there_a_bot_that_counts_your_messages_on_a/

import os
import discord
from discord.ext import commands

##EDIT
PREFIX = '?done '
TOKEN = os.getenv("REDDIT_REQUESTS")
#STOP

intents =  discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=discord.ext.commands.when_mentioned_or(PREFIX), intents=intents, description='Messages encouragement')

num_messages = {}

@bot.event
async def on_ready():
    print('Logged in as', bot.user)

@bot.event
async def on_message(message):
    if message.author.bot == True:
        await bot.process_commands(message)
        return
    user_id = message.author.id
    if user_id in num_messages.keys():
        num_messages[user_id] += 1
        if num_messages[user_id] == 3:
            await message.reply("Good job. This is a good start.")
        elif num_messages[user_id] == 5:
            await message.reply("Time for a ☕ break!")
        elif num_messages[user_id] == 10:
            await message.reply("Congratulations!  It's quitting time 🕔!")
    else:
        num_messages[user_id] = 1
    await bot.process_commands(message)

bot.run(TOKEN)