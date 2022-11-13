import asyncio

import discord.errors

from ShardBot import Shard
from discord.ext import commands
from customchecks import SilentFail


class Games(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def valheim(self, ctx):
        # establish pool
        conn = self.bot.pool
        bot = self.bot
        # check for an existing entry
        user_info = await conn.fetchrow('''SELECT * FROM games WHERE game = 'Valheim' AND user_id = $1;''',
                                        ctx.author.id)
        # fetch game information
        valheim_info = await conn.fetchrow('''SELECT * FROM games_info WHERE game_name = 'Valheim';''')
        if user_info is not None:
            # if the user already exists and is not banned, send them the port and password
            if user_info['banned'] is False:
                return await ctx.author.send(f"Server Name: {valheim_info['server_name']}\n"
                                             f"Server Port: {valheim_info['server_port']}\n"
                                             f"Server Password: ||{valheim_info['server_password']}||\n\n"
                                             f"**Remember that sharing server access information with others is against "
                                             f"the rules and can lead to a permanent ban.")
            elif user_info['banned'] is True:
                return await ctx.send("You are banned from playing Valheim in the Thegye server.")
            # get list of all Steam IDs
            steam_ids_raw = await conn.fetch('''SELECT steam_id FROM games;''')
            steam_ids = [sid['steam_id'] for sid in steam_ids_raw]
            # get the citizen role
            citizen = discord.utils.get(ctx.guild.roles, id=674260547897917460)
            if citizen not in ctx.author.roles:
                return await ctx.send("You must be a citizen in order to join Valheim.")
            else:
                # create the DM with the user
                author_dm = await ctx.author.create_dm()

                # check the message
                def authorcheck(message):
                    return ctx.author.id == message.author.id and message.guild is None

                # send the opening dialogue
                await author_dm.send("To join the Valheim server, please send your "
                                     "Steam ID to me in this DM. "
                                     "This will help me and the server admin identify your account.\n"
                                     "In order to get your Steam ID, log into Steam on your web browser at "
                                     "<https://steamcommunity.com/>. Your Steam ID will be the long string of numbers "
                                     "following `/profiles/`.")
                try:
                    steam_id_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
                except asyncio.TimeoutError:
                    return await author_dm.send("Timed out. Please answer me next time!")
                # parse the content. if the content is cancel, cancel
                steam_id = steam_id_reply.content
                if steam_id.lower() == 'cancel':
                    return await author_dm.send("Process cancelled.")
                # if the steam id provided already exists as a server user
                if steam_id in steam_ids:
                    return await author_dm.send("That ID is already associated with an existing account.")
                # send the second dialogue
                await author_dm.send(f"Your Steam ID has been recorded as: {steam_id}.\n"
                                     f"If this is not your Steam ID, reply with \"Cancel\" and retsart the process.\n\n"
                                     f"Please enter your Valheim character name for the Thegye server. "
                                     f"Keep in mind the server rules when creating your character.")
                try:
                    username_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
                except asyncio.TimeoutError:
                    return await author_dm.send("Timed out. Please answer me next time!")
                # parse the content. if the content is cancel, cancel
                username = username_reply.content
                if username.lower() == 'cancel':
                    return await author_dm.send("Process cancelled.")
                # add the user to the database
                await conn.execute('''INSERT INTO games(user_id, steam_id, game, game_username)
                 VALUES($1,$2,$3,$4);''', ctx.author.id, int(steam_id), 'Valheim', username)
                return await author_dm.send(f"Congratulations! You may now log into the Valheim server!\n"
                                            f"Server Name: {valheim_info['server_name']}\n"
                                            f"Server Port: {valheim_info['server_port']}\n"
                                            f"Server Password: ||{valheim_info['server_password']}||\n\n"
                                            f"**Remember that sharing server access information with others is against "
                                            f"the rules and can lead to a permanent ban.")


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = Games(bot)
    await bot.add_cog(cog)
