# Shard Economy v1a
from discord.ext import commands
from ShardBot import Shard


class Economy(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.pool = self.bot.pool

    async def cog_unload(self) -> None:
        pass

    # creates rbt command group
    @commands.group(invoke_without_command=True)
    async def rbt(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.invoked_with)

    @rbt.command(brief="Registers a new member of the Royal Bank of Thegye.")
    async def register(self, ctx):
        await ctx.send("Registered!")


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = Economy(bot)
    await bot.add_cog(cog)
