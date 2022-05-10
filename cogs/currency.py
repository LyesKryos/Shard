# currency v.1.01
from ShardBot import Shard
from discord.ext import commands
import discord
from customchecks import CurrencyCheck


class Currency(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot

    @commands.command(usage='[currency name] [worth] <symbol> <backed by> <nation of origin> '
                            '\nRemember that multiple word names must be enclosed by quotation marks.')
    @commands.guild_only()
    # @CurrencyCheck()
    async def add_currency(self, ctx, currencyname: str, worth: float, symbol: str = '', backed: str = '',
                           nation_of_origin: str = ''):
        # connects to the database
        conn = self.bot.pool
        # establishes the author
        author = ctx.author
        # gets all existing currencies and ensures uniqueness
        currencies = await conn.fetch('''SELECT name FROM currency WHERE server_id = $1;''', ctx.guild.id)
        currencies = [c['name'] for c in currencies]
        if currencyname in currencies:
            await ctx.send("That currency name already exists. Please use another!")
            return
        # if the worth number is a negative number, it will trigger this message
        if worth < 0:
            await ctx.send(f"You have input a worth of {worth}. The ledger does not accept negative numbers.")
            return
        try:
            await conn.execute('''INSERT INTO currency VALUES($1,$2,$3,$4,$5,$6,$7);''',
                               currencyname, worth, author.id, symbol, backed, ctx.guild.id, nation_of_origin)
            await ctx.send(f"Added currency {currencyname.title()} to the ledger!")
        except Exception as error:
            await ctx.send(error)
            self.bot.logger.warning(error)

    @commands.command(usage="[currency name] [worth] <symbol> <backed by> <nation>"
                            "\nRemember that multiple word names must be enclosed by quotation marks.")
    @commands.guild_only()
    # @CurrencyCheck()
    async def edit_currency(self, ctx, currencyname: str, worth: float, symbol: str = "", backed: str = '',
                            nation_of_origin: str = ''):
        # connects to the database
        conn = self.bot.pool
        # establishes the author
        author = ctx.author
        # gets all existing currencies and ensures uniqueness
        currencies = await conn.fetch('''SELECT name FROM currency WHERE server_id = $1;''', ctx.guild.id)
        currencies = [c['name'].lower() for c in currencies]
        if currencyname.lower() not in currencies:
            await ctx.send("That currency does not exist. Use `$ledger` to see all currencies.")
            return
        # ensures that the user owns the currency they are editing
        user = await conn.fetchrow('''SELECT userid FROM currency WHERE lower(name) = $1 AND server_id = $2;''',
                                   currencyname.lower(), ctx.guild.id)
        if user['userid'] != author.id:
            if not await self.bot.is_owner(author):
                await ctx.send("You are not authorized to edit that currency.")
                return
        # if the worth number is a negative number, it will trigger this message
        if worth < 0:
            await ctx.send(f"You have input a worth of {worth}. The ledger does not accept negative numbers.")
            return
        try:
            await conn.execute(
                '''UPDATE currency SET worth = $1, symbol = $2, backed = $4, nation = $5 WHERE lower(name) = $3;''',
                worth, symbol, currencyname.lower(), backed, nation_of_origin)
            await ctx.send(f"{currencyname} successfully updated!")
        except Exception as error:
            await ctx.send(error)
            self.bot.logger.warning(error)

    @commands.command(usage="[currency name]")
    @commands.guild_only()
    # @CurrencyCheck()
    async def remove_currency(self, ctx, currencyname: str):
        # connects to the database
        conn = self.bot.pool
        # establishes the author
        author = ctx.author
        # gets all existing currencies and ensures uniqueness
        currencies = await conn.fetch('''SELECT name FROM currency WHERE server_id = $1;''', ctx.guild.id)
        currencies = [c['name'].lower() for c in currencies]
        if currencyname.lower() not in currencies:
            await ctx.send("That currency does not exist. Use `$ledger` to see all currencies.")
            return
        # ensures that the user owns the currency they are editing
        user = await conn.fetchrow('''SELECT userid FROM currency WHERE lower(name) = $1 AND server_id = $2;''',
                                   currencyname.lower(), ctx.guild.id)
        if user['userid'] != author.id:
            if not await self.bot.is_owner(author):
                await ctx.send("You are not authorized to remove that currency.")
                return
        # removes currency
        try:
            await conn.execute('''DELETE FROM currency WHERE lower(name) = $1;''', currencyname.lower())
            await ctx.send(f"{currencyname} successfully removed from the ledger.")
        except Exception as error:
            await ctx.send(error)
            self.bot.logger.warning(error)

    @commands.command(usage="[currency name]")
    @commands.guild_only()
    # @CurrencyCheck()
    async def currency(self, ctx, currency_string: str):
        currency = currency_string.lower()
        # connects to the database
        conn = self.bot.pool
        # gets all existing currencies and ensures uniqueness
        currencies = await conn.fetch('''SELECT name FROM currency WHERE server_id = $1;''', ctx.guild.id)
        currencies = [c['name'].lower() for c in currencies]
        if currency not in currencies:
            await ctx.send("That currency does not exist. Use `$ledger` to see all currencies.")
            return
        try:
            currencydata = await conn.fetchrow('''SELECT * FROM currency WHERE lower(name) = $1;''', currency)
            if currencydata['symbol'] != '':
                symbol = f" ({currencydata['symbol']})"
            else:
                symbol = ''
            if currencydata['backed'] != '':
                backed = f"This currency is backed by {currencydata['backed']}."
            else:
                backed = ''
            if currencydata['nation'] != '':
                nation = f"This currency belongs to {currencydata['nation']}."
            else:
                nation = ''
            await ctx.send(
                f"The {currencydata['name']}{symbol} is worth {currencydata['worth']} grams of gold per unit (AUG). "
                f"{backed} {nation}")
        except Exception as error:
            await ctx.send(error)
            self.bot.logger.warning(error)

    @commands.command(usage="[currency] [currency] [amount]")
    @commands.guild_only()
    # @CurrencyCheck()
    async def exchange(self, ctx, firstcurrencyraw: str, secondcurrencyraw: str, amount: float):
        # connects to the database
        conn = self.bot.pool
        # if the worth amount is negative, then the syntax message is triggered
        if amount < 0:
            raise commands.UserInputError
        firstcurrency = firstcurrencyraw.lower()
        secondcurrency = secondcurrencyraw.lower()
        # creates the embed object
        embed = discord.Embed(title="The International Bank of Shard: Exchange", color=discord.Color.gold(),
                              description=f"Exchanging {amount} {firstcurrency.title()}s to {secondcurrency.title()}s")
        # sets the embed image
        embed.set_thumbnail(url="https://i.ibb.co/sVWJ0Vz/image.png")
        currencies = await conn.fetch('''SELECT name FROM currency WHERE server_id = $1;''', ctx.guild.id)
        currencies = [c['name'].lower() for c in currencies]
        # if either the first currency or the second currency are not present, one of these messages will trigger
        if (firstcurrency not in currencies) and (secondcurrency not in currencies):
            await ctx.send(
                f"Neither {firstcurrency.title()} nor {secondcurrency.title()} are found in the ledger. Check "
                f"your records.")
            return
        elif firstcurrency not in currencies:
            await ctx.send(f"{firstcurrency.title()} not found in the ledger. Check your records.")
            return
        elif secondcurrency not in currencies:
            await ctx.send(f"{secondcurrency.title()} not found in the ledger. Check your records.")
            return
        # fetches currency information
        currencyinfo1 = await conn.fetchrow('''SELECT * FROM currency WHERE lower(name) = $1;''', firstcurrency)
        currencyinfo2 = await conn.fetchrow('''SELECT * FROM currency WHERE lower(name) = $1;''', secondcurrency)
        firstworth = currencyinfo1['worth']
        secondworth = currencyinfo2['worth']
        # rate calculation
        rate = firstworth / secondworth
        # output formatted with money format
        output = f"{currencyinfo2['symbol']}{round(amount * rate, 2):,.2f}"
        # adds embed fields for the calculated numbers
        embed.add_field(name=f"{firstcurrency.title()} worth", value=f"{firstworth:,.2f} AUG",
                        inline=True)
        embed.add_field(name=f"{secondcurrency.title()} worth", value=f"{secondworth:,.2f} AUG",
                        inline=True)
        embed.add_field(name="Exchange Rate", value=str(rate), inline=False)
        embed.add_field(name="Exchange Amount In",
                        value="{}{:,.2f}".format(currencyinfo1['symbol'], amount), inline=True)
        embed.add_field(name="Exchange Amount Out", value=output, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    # @CurrencyCheck()
    async def ledger(self, ctx):
        # connects to the database
        conn = self.bot.pool
        # creates the embed object
        ledger_embed = discord.Embed(title="The International Bank of Shard: Ledger", color=discord.Color.gold(), )
        # sets the embed image
        ledger_embed.set_thumbnail(url="https://i.ibb.co/sVWJ0Vz/image.png")
        # fetches currency information
        ledger = await conn.fetch('''SELECT * FROM currency WHERE server_id = $1;''', ctx.guild.id)
        if ledger is None:
            await ctx.send("This server has no ledger.")
            return
        # generates embed objects for every currency in the ledger
        for currency in ledger:
            currency_name = currency['name']
            if currency['symbol'] != '':
                symbol = f" ({currency['symbol']})"
            else:
                symbol = ""
            worth = currency['worth']
            ledger_embed.add_field(name=f"{currency_name}{symbol}", value=f"{worth} AUG", inline=True)
        await ctx.send(embed=ledger_embed)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def currency_blacklist(self, ctx, *, args):
        user = args
        user = await commands.converter.MemberConverter().convert(ctx, user)
        conn = self.bot.pool
        try:
            await conn.execute('''INSERT INTO blacklist(user_id, system) VALUES($1, $2);''', user.id, "currency")
            await ctx.send(f"{user.display_name}{user.discriminator} blacklisted from the Currency Exchange.")
        except Exception as error:
            await ctx.send(f"Error: {error}")
            self.bot.logger.warning(msg=error)


def setup(bot):
    bot.add_cog(Currency(bot))
