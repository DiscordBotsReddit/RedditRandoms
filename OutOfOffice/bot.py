import discord
from discord.ext import commands
from datetime import datetime


## PLEASE EDIT THESE WITH THE CORRECT VALUES
PREFIX = '!'
START_TIME = '09:00' # 24 hour time
END_TIME = '17:00' # 24 hour time
RESPONSE = 'What you want the bot to say.'
TOKEN = 'YOUR-TOKEN-HERE'
## STOP EDITING


intents =  discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, description='Auto reply bot')

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        pass
    else:
        if START_TIME < datetime.strftime(datetime.now(), '%H:%M') < END_TIME:
            await message.reply(RESPONSE)

@bot.event
async def on_ready():
	print(f'Logged in as {bot.user} (ID: {bot.user.id})')

bot.run(TOKEN)