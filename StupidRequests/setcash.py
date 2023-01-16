# https://www.reddit.com/r/discordbots/comments/108flh4/discord_bot_that_uses_setcash_to_update_the_total/

import os

import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

TOKEN = os.getenv("REDDIT_REQUESTS")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

money = 0

bot = commands.Bot(command_prefix=when_mentioned_or("/"), intents=intents)


@bot.event
async def on_ready():
    print("Logged in as", bot.user)


@bot.command(name="setcash")
async def setcash(ctx, amt: int):
    global money
    if amt is None:
        await ctx.reply("Please include an amount to add/remove.")
    else:
        money += amt
        await ctx.reply(f"Total amount of cash is currently `{money}`.")


bot.run(TOKEN)
