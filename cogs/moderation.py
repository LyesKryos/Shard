# dispatch cog v 1.4
from datetime import datetime, timedelta
import discord
from ShardBot import Shard
import asyncio
from discord.ext import commands
import re
from pytz import timezone
from ratelimiter import Ratelimiter
from customchecks import SilentFail

class Moderation(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.eastern = timezone('US/Eastern')

    async def cog_check(self, ctx) -> bool:
        if ctx.author.id == ctx.bot.owner_id:
            return True
        moderation_roles = [798416884462387220, 674278353204674598]
        aroles = list()
        for ar in ctx.author.roles:
            aroles.append(ar.id)
        if not any(i in moderation_roles for i in aroles):
            raise SilentFail

    @commands.command(brief="Mutes the specified user. Time should be specified in hour, "
                            "minute, second format. Example: 1h,2m,3s")
    @commands.guild_only()
    async def mute(self, ctx, user: discord.Member, mutetime: str):
        # sets mute time
        basetime = 0
        mutetime = mutetime.split(',')
        now = datetime.now(tz=self.eastern)
        mute_datetime = now
        for t in mutetime:
            if t.endswith('s'):
                mute_datetime = mute_datetime + timedelta(seconds=int(t[:-1]))
            elif t.endswith('m'):
                mute_datetime = mute_datetime + timedelta(minutes=int(t[:-1]))
            elif t.endswith('h'):
                mute_datetime = mute_datetime + timedelta(hours=int(t[:-1]))
            elif t.endswith('d'):
                mute_datetime = mute_datetime + timedelta(days=int(t[:-1]))
            elif len(mutetime) > 4:
                raise commands.UserInputError
            else:
                raise commands.UserInputError
        await user.timeout(mute_datetime, reason=None)
        await ctx.send(f"{user.name}{user.discriminator} muted until "
                       f"{mute_datetime.strftime('%d %b %Y at %H:%M:%S %Z%z')}. "
                       f"Relative time: <t:{round(mute_datetime.timestamp())}:f>")

    @commands.command(brief="Unmutes a previously muted user.")
    @commands.guild_only()
    async def unmute(self, ctx, user: discord.Member):
        # if the member hasn't been muted, cannot unmute
        if user.timed_out_until is None:
            return await ctx.send(f"{user.name}{user.discriminator} cannot be unmuted, as they are not muted.")
        # otherwise, unmute!
        await user.edit(timed_out_until=None)
        # double check
        if user.timed_out_until is None:
            return await ctx.send(f"{user.name}{user.discriminator} unmuted.")
        else:
            return await ctx.send(f"Unmute not successful.")

    @commands.command(brief="Kicks a specified user.")
    @commands.guild_only()
    async def kick(self, ctx, *, args):
        # fetch the guild
        thegye_server = await self.bot.fetch_guild(728444080908140575)
        # check if the user is in the server
        member = await commands.MemberConverter().convert(ctx, args)
        # kick user
        await thegye_server.kick(member)
        return await ctx.send(f"{member.mention} kicked.")

    @commands.command(brief="Bans a specified user.")
    @commands.guild_only()
    async def ban(self, ctx, *, args):
        # fetch the guild
        thegye_server = await self.bot.fetch_guild(674259612580446230)
        # ban user
        try:
            user = await commands.MemberConverter().convert(ctx, args)
            await thegye_server.ban(user)
            return await ctx.send(f"{user.mention} banned.")
        except commands.MemberNotFound:
            user = await commands.UserConverter().convert(ctx, args)
            await thegye_server.ban(user)
            return await ctx.send(f"Non-server member {user.id} banned.")

    @commands.command(brief="Bans a specified user.")
    @commands.guild_only()
    async def unban(self, ctx, *, args):
        # fetch the guild
        thegye_server = await self.bot.fetch_guild(674259612580446230)
        # unban user
        user = await commands.UserConverter().convert(ctx, args)
        await thegye_server.unban(user)
        return await ctx.send(f"Non-server member {user.id} unbanned.")


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = Moderation(bot)
    await bot.add_cog(cog)







