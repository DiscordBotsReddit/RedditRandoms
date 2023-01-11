from asyncio import sleep
import sqlite3
from datetime import datetime

from asyncpraw import Reddit
import bot_secrets as BS
import discord
from discord import app_commands
from discord.ext import commands


class SubredditWatch(commands.Cog):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.MAX_SUBS = 25
        db = sqlite3.connect('watched_subs.db')
        cur = db.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS WatchedSubs(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, subreddit TEXT NOT NULL);")
        cur.execute("CREATE TABLE IF NOT EXISTS SubChannel(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL UNIQUE, channel_id INTEGER NOT NULL UNIQUE, running INTEGER NOT NULL DEFAULT 0);")
        db.commit()
        cur.execute("UPDATE SubChannel SET running=0 WHERE running=1;")
        db.commit()
        cur.close()
        db.close()

    rw_setup = app_commands.Group(name='setup', description='Commands used to setup the RedditWatch bot')

    @rw_setup.command(name='add', description='Adds the specified subreddit to the watchlist.')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def add_subreddit_to_watch(self, interaction: discord.Interaction, subreddit: str):
        multi = False
        async with Reddit(client_id=BS.REDDIT_ID, client_secret=BS.REDDIT_SECRET, user_agent=BS.USER_AGENT) as reddit:
            if "+" in subreddit:
                subreddit = subreddit.split("+")[0]
                multi = True
            db = sqlite3.connect('watched_subs.db')
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            watched_subs = cur.execute(f"SELECT * FROM WatchedSubs WHERE guild_id={interaction.guild.id};").fetchall()
            for sub in watched_subs:
                if sub['subreddit'].lower() == subreddit.lower():
                    await interaction.response.send_message(f'`r/{subreddit}` is already being watched.')
                    return
            try:
                check_if_sub_exists = await reddit.subreddit(subreddit)
                await check_if_sub_exists.load()
                if len(watched_subs) >= self.MAX_SUBS:
                    await interaction.response.send_message("Sorry, you have reached the limit of 5 subreddits to watch.")
                    return
                cur.execute("INSERT OR IGNORE INTO WatchedSubs(guild_id,subreddit) VALUES(?,?);",(interaction.guild.id, subreddit.lower()))
                db.commit()
                cur.close()
                db.close()
                if multi == False:
                    await interaction.response.send_message(f'Added `r/{subreddit}` to the watchlist.\n**{len(watched_subs)+1}/{self.MAX_SUBS} slots used.**')
                else:
                    await interaction.response.send_message(f'Multi-reddits are not supported.  First subreddit used.\nAdded `r/{subreddit}` to the watchlist.\n**{len(watched_subs)+1}/{self.MAX_SUBS} slots used.**')
                await reddit.close()
            except:
                await interaction.response.send_message(f'`r/{subreddit}` not a valid subreddit.')

    @rw_setup.command(name='remove', description='Removes the specified subreddit from the watchlist.')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def remove_subreddit_from_watch(self, interaction: discord.Interaction, subreddit: str):
        db = sqlite3.connect('watched_subs.db')
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        deleted = cur.execute(f"DELETE FROM WatchedSubs WHERE guild_id={interaction.guild.id} AND subreddit='{subreddit.lower()}';")
        db.commit()
        cur.close()
        db.close()
        if deleted.rowcount == 1:
            await interaction.response.send_message(f'`r/{subreddit}` was removed from the watchlist.')
        else:
            await interaction.response.send_message(f'`r/{subreddit}` was not being watched.')

    @rw_setup.command(name='list', description='Lists the currently watched subreddits in this guild.')
    async def list_watched_subs(self, interaction: discord.Interaction):
        db = sqlite3.connect('watched_subs.db')
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        watched_subs = cur.execute(f"SELECT * FROM WatchedSubs WHERE guild_id={interaction.guild.id};").fetchall()
        watched_subs_list = []
        for sub in watched_subs:
            watched_subs_list.append('`r/'+sub['subreddit']+'`')
        await interaction.response.send_message(f'Watched subreddits ({len(watched_subs)}/{self.MAX_SUBS}):\n{", ".join(watched_subs_list)}')

    @rw_setup.command(name='output', description='Sets the output forum channel. Make sure the name is the same as it shows on the sidebar.')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_output_channel(self, interaction: discord.Interaction, channel_name: str):
        channel_name = channel_name.replace(" ", "-")
        channels = await interaction.guild.fetch_channels()
        for channel in channels:
            if channel.name.lower() == channel_name.lower():
                db = sqlite3.connect('watched_subs.db')
                db.row_factory = sqlite3.Row
                cur = db.cursor()
                set_channel = cur.execute(f"SELECT * FROM SubChannel WHERE guild_id={interaction.guild.id};").fetchone()
                if set_channel is not None and set_channel['channel_id'] == channel.id:
                    await interaction.response.send_message(f'{channel.mention} is already set as the output channel.')
                elif set_channel is not None and set_channel['channel_id'] != channel.id:
                    cur.execute("UPDATE SubChannel SET channel_id=? WHERE guild_id=?;", (channel.id, interaction.guild.id))
                    db.commit()
                    await interaction.response.send_message(f'{channel.mention} has been updated to the output channel.')
                elif set_channel is None:
                    cur.execute(f"INSERT INTO SubChannel(guild_id,channel_id) VALUES(?,?);", (interaction.guild.id, channel.id))
                    db.commit()
                    await interaction.response.send_message(f'{channel.mention} has been set as the output channel.')
                cur.close()
                db.close()

    @app_commands.command(name='start', description='Starts watching your set subreddits.')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def start_watching_subreddit_streams(self, interaction: discord.Interaction):
        db = sqlite3.connect('watched_subs.db')
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        channel_id = cur.execute(f"SELECT channel_id, running FROM SubChannel WHERE guild_id={interaction.guild.id};").fetchone()
        watched_subs = cur.execute(f"SELECT * FROM WatchedSubs WHERE guild_id={interaction.guild.id};").fetchall()
        if len(watched_subs) == 0:
            await interaction.response.send_message("Please add subreddits using the `/setup add subreddit` command.")
            cur.close()
            db.close()
            return
        if channel_id is None:
            await interaction.response.send_message("Please setup an output channel using the `/setup output` command.")
            cur.close()
            db.close()
            return
        else:
            channel = interaction.guild.get_channel(channel_id['channel_id'])
            async with Reddit(client_id=BS.REDDIT_ID, client_secret=BS.REDDIT_SECRET, user_agent=BS.USER_AGENT) as reddit:
                await interaction.response.send_message("Starting to watch your subreddits.")
                cur.execute(f"UPDATE SubChannel SET running=1 WHERE guild_id={interaction.guild.id};")
                db.commit()
                cur.close()
                db.close()
                for sub in watched_subs:
                    subreddit = await reddit.subreddit(sub['subreddit'])
                    async for submission in subreddit.stream.submissions(pause_after=0):
                        db = sqlite3.connect('watched_subs.db')
                        db.row_factory = sqlite3.Row
                        cur = db.cursor()
                        running = cur.execute(f"SELECT running FROM SubChannel WHERE guild_id={interaction.guild.id};").fetchone()
                        cur.close()
                        db.close()
                        if running['running'] == 1:
                            if submission.thumbnail is not None:
                                if 'i.redd.it' in submission.url:
                                    created_at = datetime.fromtimestamp(int(submission.created_utc))
                                    submission.permalink = "https://www.reddit.com"+submission.permalink
                                    if len(submission.title) > 100: # Forum post titles can only be 100 characters or less
                                        submission.title = submission.title[:97]+"..."
                                    if len(channel.threads) > 0:
                                        names = [channel.name for channel in channel.threads]
                                        if submission.title in names:
                                            pass
                                        else:
                                            await channel.create_thread(name=submission.title, content=f'r/{submission.subreddit}\n{submission.url}')
                                            await sleep(5) # Discord rate limits
                                    else:
                                        await channel.create_thread(name=submission.title, content=f'r/{submission.subreddit}\n{submission.url}')
                                        await sleep(5) # Discord rate limits
                        elif running['running'] == 0:
                            return
        print('Done')
                            
    @app_commands.command(name='stop', description='Stops watching your set subreddits.')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def stop_watching_subreddit_streams(self, interaction: discord.Interaction):
        db = sqlite3.connect('watched_subs.db')
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        cur.execute(f"UPDATE SubChannel SET running=0 WHERE guild_id={interaction.guild.id};")
        db.commit()
        cur.close()
        db.close()
        await interaction.response.send_message('Stopped watching your desired subreddits.')

async def setup(bot):
	await bot.add_cog(SubredditWatch(bot))
	print(f'cogs > {__name__[5:].upper()} loaded <')

async def teardown(bot):
	await bot.remove_cog(SubredditWatch(bot))
	print(f'cogs > {__name__[5:].upper()} unloaded <')
