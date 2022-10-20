from discord.ext import commands
from discord.utils import get


class SilentFail(commands.CommandError):
    pass


class CNCFail(commands.CheckFailure):
    pass


class TooManyRequests(Exception):
    pass


def modcheck():
    # custom check
    def predicate(ctx):
        if ctx.author.id in [293518673417732098 or 285855888336486400 or 674285995021041677]:
            return True
        else:
            if ctx.guild is None:
                if not ctx.bot.is_owner():
                    return False
                else:
                    return True
            aroles = list()
            for ar in ctx.author.roles:
                aroles.append(ar.id)
            if 928889638888812586 not in aroles:
                raise CNCFail("You do not have the moderator role!")
            elif ctx.channel.id not in [896887449089867806, 674338490321862672]:
                raise CNCFail("This is the wrong channel for that command!")
            return True

    return commands.check(predicate)


class RecruitmentCheckFail(commands.CheckFailure):
    pass


def RecruitmentCheck():
    # custom check
    async def recruitmentcheck(ctx):
        if ctx.author.id == 293518673417732098:
            return True
        else:
            recruiter_role = get(ctx.guild.roles, id=674339578102153216)
            if recruiter_role not in ctx.author.roles:
                raise RecruitmentCheckFail(
                    f"You are not authorized to use this command. Use `{ctx.bot.command_prefix}recruiter` "
                    f"to get the required role.")
            elif ctx.channel.id != 674342850296807454:
                raise RecruitmentCheckFail(
                    f"This is the wrong channel for that. Please make sure you are using only the"
                    f"#recruitment channel")
            return True

    return commands.check(recruitmentcheck)


class CurrencyFail(commands.CheckFailure):
    pass


def CurrencyCheck():
    # custom check
    async def currency(ctx):
        conn = ctx.bot.pool
        blacklist = await conn.fetchrow('''SELECT * FROM blacklist WHERE user_id = $1 AND system = $2;''',
                                        ctx.user.id, 'currency')
        if blacklist:
            raise CurrencyFail()
        if ctx.guild.id in [674259612580446230, 549506142678548490, 728444080908140575]:
            return True
        else:
            raise CurrencyFail("This server is not registered for that command.")

    return commands.check(currency)


class WrongInput(commands.CommandInvokeError):
    pass
