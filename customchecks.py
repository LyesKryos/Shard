from discord.ext import commands
import datetime


class CNCFail(commands.CheckFailure):
    pass


def CNCcheck():
    # custom check
    async def predicate(ctx):
        if ctx.author.id in [293518673417732098 or 285855888336486400 or 674285995021041677]:
            return True
        else:
            if ctx.guild is None:
                aroles = list()
                guild = ctx.bot.get_guild(674259612580446230)
                member = guild.get_member(ctx.author.id)
                for ar in member.roles:
                    aroles.append(ar.id)
                if 896886962710007808 not in aroles:
                    raise CNCFail("You do not have the right role for that!")
                return True
            # connects to the database
            conn = ctx.bot.pool
            blacklist = await conn.fetchrow('''SELECT * FROM blacklist WHERE user_id = $1 AND active = True;''',
                                            ctx.author.id)
            if blacklist is not None:
                if blacklist['end_time'] is None:
                    if blacklist['status'] == "mute":
                        raise CNCFail("You are muted.")
                    if blacklist['status'] == "ban":
                        raise CNCFail("You are banned.")
                if blacklist['end_time'] < datetime.datetime.now():
                    try:
                        await conn.execute(
                            '''UPDATE blacklist SET active = False WHERE user_id = $1 AND end_time = $2;''',
                            ctx.author.id, blacklist['end_time'])
                    except Exception as error:
                        await ctx.send(error)
                else:
                    raise CNCFail("You are muted.")

            aroles = list()
            for ar in ctx.author.roles:
                aroles.append(ar.id)
            if 896886962710007808 not in aroles:
                raise CNCFail("You do not have the right role for that!")
            elif ctx.channel.id != 896887449089867806:
                raise CNCFail("This is the wrong channel for that command!")
            return True

    return commands.check(predicate)


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
        elif ctx.author.id == 275497677481836545:
            return True
        else:
            userroles = [role.id for role in ctx.author.roles]
            if (674339578102153216 not in userroles) or (603002913639628810 not in userroles):
                raise RecruitmentCheckFail(
                    f"You are not authorized to use this command. Use `{ctx.bot.command_prefix}recruiter "
                    f"to get the required role.")
            elif (ctx.channel.id != 674342850296807454) or (ctx.channel.id != 603003000667111454):
                raise RecruitmentCheckFail(
                    f"This is the wrong channel for that. Please make sure you are using only the"
                    f"#recruitment channel")
            return True

    return commands.check(recruitmentcheck)

