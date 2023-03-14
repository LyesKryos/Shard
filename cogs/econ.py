# Shard Economy v2a
from __future__ import annotations
import asyncio
import math
import traceback
import typing
from datetime import datetime, timedelta
from random import randint, uniform
import discord
from dateutil.relativedelta import relativedelta
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from matplotlib import pyplot as plt
from matplotlib.dates import HourLocator, DateFormatter, DayLocator
from numpy import clip
from pytz import timezone
from ShardBot import Shard
from customchecks import SilentFail


class RegisterView(View):

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="I accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, accept_button: discord.Button):
        accept_button.label = "Accepted"
        self.decline.disabled = True
        accept_button.disabled = True
        # define thaler
        thaler = "\u20B8"
        # establish connection
        conn = interaction.client.pool
        # define user
        user = interaction.user
        # fetch general fund information
        general_fund_raw = await conn.fetchrow('''SELECT * FROM funds WHERE name = 'General Fund';''')
        general_fund = general_fund_raw['current_funds']
        # calculate starting gift, credit it towards the user, and remove thaler from fund
        registration_gift = round(general_fund * .001, 0)
        await conn.execute('''INSERT INTO rbt_users VALUES($1,$2);''',
                           user.id, registration_gift)
        await conn.execute('''UPDATE funds SET current_funds = current_funds - $1 WHERE name = 'General Fund';''',
                           registration_gift)
        await interaction.response.edit_message(view=self)
        return await interaction.followup.send(f"{user.name}#{user.discriminator} has been registered "
                                               f"as a new member of the Royal Bank of Thegye.\n"
                                               f"This new member has been given **{thaler}"
                                               f"{registration_gift:,.2f}** to get started."
                                               f"\nThe General Fund now contains "
                                               f"{thaler}{general_fund - registration_gift:,.2f}."
                                               , ephemeral=False)

    @discord.ui.button(label="I decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, decline_button: discord.Button):
        decline_button.label = "Declined"
        decline_button.disabled = True
        self.accept.disabled = True
        await interaction.response.edit_message(view=self)


class ContractSign(View):

    def __init__(self, m, contract_id):
        super().__init__(timeout=300)
        self.message = m
        self.contract_id = contract_id

    async def on_timeout(self) -> None:
        # for all buttons, disable
        for button in self.children:
            button.disabled = True
        self.message.edit(view=self)

    @discord.ui.button(label="I accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, accept_button: discord.Button):
        # defer interaction
        await interaction.response.defer(thinking=False)
        accept_button.label = "Accepted"
        self.decline.disabled = True
        accept_button.disabled = True
        # define thaler
        thaler = "\u20B8"
        # establish connection
        conn = interaction.client.pool
        # define user
        user = interaction.user
        # update contract
        await conn.execute('''UPDATE contracts SET signatories = signatories || $1 WHERE contract_id = $2;''',
                           [user.id], self.contract_id)
        await conn.execute('''INSERT INTO rbt_user_log VALUES ($1,$2,$3);''',
                           user.id, 'contract', f"Created and signed contract #{self.contract_id}.")
        return await self.message.edit(view=self)

    @discord.ui.button(label="I decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, decline_button: discord.Button):
        await interaction.response.defer(thinking=False)
        decline_button.label = "Declined"
        decline_button.disabled = True
        self.accept.disabled = True
        return await self.message.edit(view=self)


class FeedView(View):

    def __init__(self, bot: Shard, m):
        super().__init__(timeout=120)
        # define bot
        self.bot = bot
        # define page
        self.page = 1
        self.rank = 11
        # define thaler
        self.thaler = "\u20B8"
        # define space
        self.space = "\u200b"
        # message
        self.message = m

    async def on_timeout(self) -> None:
        # disable all buttons
        for button in self.children:
            button.disabled = True
        # edit view
        await self.message.edit(view=self)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.blurple, disabled=True, emoji="\u23ea")
    async def back(self, interaction: discord.Interaction, back_button: discord.Button):
        try:
            # defer response
            await interaction.response.defer()
            # set foward button on
            self.forward.disabled = False
            # establish connection
            conn = interaction.client.pool
            # subtract from page
            self.page -= 1
            self.rank = (self.page * 10) - 9
            # page cannot be less than 1
            if self.page <= 1:
                self.page = 1
                back_button.disabled = True
            # fetch all stocks
            stocks = await conn.fetch('''SELECT * FROM stocks ORDER BY value DESC;''')
            stock_string = ""
            for stock in stocks[(self.page * 10) - 10:self.page * 10]:
                this_string = f"``{self.rank}. {stock['name']} (#{stock['stock_id']}: " \
                              f"{self.thaler}{stock['value']:,.2f}"
                for space in range(0, 48 - len(this_string)):
                    this_string += " "
                if stock['trending'] == "up":
                    this_string += "``:chart_with_upwards_trend: +"
                else:
                    this_string += "``:chart_with_downwards_trend:"
                this_string += f"``{stock['change'] * 100:.2f}%``\n"
                stock_string += this_string
                self.rank += 1
            feed_embed = discord.Embed(title="Stocks by Share Price", description=stock_string)
            feed_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
            await self.message.edit(embed=feed_embed, view=self)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, close: discord.Button):
        try:
            # defer response
            await interaction.response.defer()
            # disable all buttons
            self.back.disabled = True
            self.forward.disabled = True
            close.disabled = True
            await self.message.edit(view=self)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, emoji="\u23e9")
    async def forward(self, interaction: discord.Interaction, forward_button: discord.Button):
        try:
            # defer response
            await interaction.response.defer()
            # enable back button
            self.back.disabled = False
            # establish connection
            conn = interaction.client.pool
            # subtract from page
            self.page += 1
            # fetch all stocks
            stocks = await conn.fetch('''SELECT * FROM stocks ORDER BY value DESC;''')
            stock_string = ""
            # disable forward on last page
            if (len(stocks[(self.page * 10) - 10:self.page * 10]) / 10) < 1:
                forward_button.disabled = True
            for stock in stocks[(self.page * 10) - 10:self.page * 10]:
                this_string = f"``{self.rank}. {stock['name']} (#{stock['stock_id']}: " \
                              f"{self.thaler}{stock['value']:,.2f}"
                for space in range(0, 48 - len(this_string)):
                    this_string += " "
                if stock['trending'] == "up":
                    this_string += "``:chart_with_upwards_trend: +"
                else:
                    this_string += "``:chart_with_downwards_trend:"
                this_string += f"``{stock['change'] * 100:.2f}%``\n"
                stock_string += this_string
                self.rank += 1
            feed_embed = discord.Embed(title="Stocks by Share Price", description=stock_string)
            feed_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
            await self.message.edit(embed=feed_embed, view=self)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")


class Economy(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.thaler = "\u20B8"
        self.announcement = "The Royal Exchange of Thegye has updated. Below is a summary of any important changes:\n"
        self.market_task = asyncio.create_task(self.market_updating())
        self.bank_task = asyncio.create_task(self.bank_updating())
        self.crash = False

    async def cog_unload(self) -> None:
        self.market_task.cancel()
        self.bank_task.cancel()

    async def cog_check(self, ctx) -> bool:
        # define Thegye role
        citizen_id = 674260547897917460
        # if the sender is the owner, return true
        if ctx.author.id == 293518673417732098:
            return True
        else:
            # if this is in DMs, check the user id on the Thegye server to ensure proper role
            if ctx.guild is None:
                aroles = list()
                thegye = ctx.bot.get_guild(674259612580446230)
                member = thegye.get_member(ctx.author.id)
                for ar in member.roles:
                    aroles.append(ar.id)
                if citizen_id not in aroles:
                    raise SilentFail
            # if this is a server, check to make sure the user has the right role and/or this is the right server
            elif ctx.guild is not None:
                aroles = list()
                if ctx.guild.id == 674259612580446230:
                    for ar in ctx.author.roles:
                        aroles.append(ar.id)
                    if citizen_id not in aroles:
                        raise SilentFail
                else:
                    raise SilentFail
            else:
                return True

    # creates rbt command group
    rbt = app_commands.Group(name="rbt", description="...")

    async def bank_updating(self):
        # wait for bot to be ready
        await self.bot.wait_until_ready()
        # define crash channel
        crashchannel = self.bot.get_channel(835579413625569322)
        # define bank channel
        bankchannel = self.bot.get_channel(855155865023021066)
        # set timezone
        eastern = timezone('US/Eastern')
        while True:
            try:
                # define now
                now = datetime.now(eastern)
                # sets the time to be midnight the next day
                next_run = now.replace(hour=0, minute=0, second=0)
                next_run += timedelta(days=1)
                # sends the next runtime
                await crashchannel.send(f"Bank update waiting until "
                                        f"{next_run.strftime('%d %b %Y at %H:%M %Z%z')}")
                # sleeps until runtime
                await discord.utils.sleep_until(next_run)
                # establish connection
                conn = self.bot.pool
                # GENERAL FUND CHECKS
                # check general fund for minting/refund
                general_fund = await conn.fetchrow('''SELECT * FROM funds WHERE name = 'General Fund';''')
                # if the general fund is near/overdrawn
                if general_fund['current_funds'] <= (.02 * general_fund['fund_limit']):
                    # set new fund to 150% of old fund
                    new_limit = general_fund['fund_limit'] * 1.5
                    additional_funds = general_fund['fund_limit'] * .5
                    # ADD MARKET INCREASES/DECREASES HERE
                    # update funds
                    await conn.execute('''UPDATE funds SET fund_limit = $1, current_funds = current_funds + $2 
                            WHERE name = 'General Fund';''', new_limit, additional_funds)
                # if the general fund is overfunded
                if general_fund['current_funds'] > general_fund['fund_limit']:
                    # ensure the general fund is more than 500,000 thaler
                    if general_fund['fund_limit'] > 500000:
                        # set the new fund limit to 50%
                        new_limit = general_fund['fund_limit'] * .5
                        # calculate refund and new current funds
                        new_funds = general_fund['fund_limit'] * .25
                        refund = general_fund['current_funds'] - general_fund['fund_limit']
                        await conn.execute('''UPDATE funds SET fund_limit = $1, current_funds = $2 
                                WHERE name = 'General Fund';''', new_limit, new_funds)
                        # count the number of investors
                        investor_count = await conn.fetchrow('''SELECT COUNT(DESTINCT user_id) 
                                FROM bank_ledger WHERE type = 'Investment';''')
                        # calculate how much each investor will receive
                        investor_cut = (refund * .25) / investor_count['count']
                        # count the number of premium members
                        premium_count = await conn.fetchrow('''SELECT COUNT(DESTINCT user_id) 
                                FROM rbt_users WHERE premeium_user = TRUE AND suspended = FALSE;''')
                        # calculate how much each premium user will receive
                        premium_cut = (refund * .25) / premium_count['count']
                        # count the number of recruiters who have sent more than 100 TGs this month
                        sender_count = await conn.fetchrow('''SELECT COUNT(DESTINCT user_id) 
                                FROM recruitment WHERE sent_this_month > 100;''')
                        # calculate sender cut
                        sender_cut = (refund * .25) / sender_count['count']
                        # count the number of registered members
                        member_count = await conn.fetchrow('''SELECT COUNT(DESTINCT user_id) 
                                FROM rbt_users WHERE suspended = FALSE;''')
                        # calculate the member cut
                        member_cut = (refund * .25) / member_count['count']
                        # credit premium group
                        await conn.execute('''UPDATE rbt_users SET funds = funds + $1 
                                WHERE premeium_user = TRUE AND suspended = FALSE;''', premium_cut)
                        # credit member group
                        await conn.execute('''UPDATE rbt_users SET funds = funds + $1 
                                WHERE suspended = FALSE;''', member_cut)
                        # credit investor group
                        investors = await conn.fetch('''SELECT * FROM bank_ledger WHERE type = 'investment';''')
                        for investor in investors:
                            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2
                                    AND suspended = FALSE;''', investor_cut, investor['user_id'])
                        # credit sender group
                        senders = await conn.fetch('''SELECT user_id FROM recruitment WHERE sent_this_month > 100;''')
                        for sender in senders:
                            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2
                                                    AND suspended = FALSE;''', sender_cut, sender['user_id'])
                        self.announcement += "***The Royal Bank of Thegye has issued a general refund!***"
                # INVESTMENT/LOAN UPDATES
                # fetch sum of all investments
                investment_sum_raw = await conn.fetchrow('''SELECT SUM(amount) FROM bank_ledger 
                WHERE type = 'Investment';''')
                if investment_sum_raw['sum'] is None:
                    investment_sum = 0
                else:
                    investment_sum = investment_sum_raw['sum']
                # increase investments by 2% for investors
                await conn.execute('''UPDATE bank_ledger SET amount = amount * 1.02 WHERE type = 'Investment';''')
                # increase investment fund by 2%
                await conn.execute(
                    '''UPDATE funds SET current_funds = current_funds * 1.02 WHERE name = 'Investment Fund';''')
                # pay 6% dividend to general fund
                await conn.execute(
                    '''UPDATE funds SET current_funds = current_funds + $1 WHERE name = 'General Fund';''',
                    (investment_sum * .06))
                # increase loan interest by 1.5%
                await conn.execute('''UPDATE bank_ledger SET amount = amount * 1.02 WHERE type = 'Loan';''')
                # payroll
                thegye = self.bot.get_guild(674259612580446230)
                official_role = thegye.get_role(674278988323225632)
                for official in official_role.members:
                    if datetime.now().weekday() <= 5:
                        await conn.execute('''UPDATE rbt_users SET funds = funds + 20 WHERE user_id = $1;''',
                                           official.id)
                        await conn.execute(
                            '''UPDATE funds SET general_fund = general_fund - 20 WHERE name = 'General Fund';''')
                await bankchannel.send("Royal Bank of Thegye updated.")
                continue
            except Exception as error:
                etype = type(error)
                trace = error.__traceback__
                lines = traceback.format_exception(etype, error, trace)
                traceback_text = ''.join(lines)
                self.bot.logger.warning(msg=f"{traceback_text}")

    @rbt.command(name="register", description="Registers a new member of the Royal Bank of Thegye.")
    async def register(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True, ephemeral=True)
        # ensure guild presence
        if interaction.guild is None:
            return await interaction.followup.send("I cannot run this command in DMs!")
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # check to see if user is previously registered
        registered_check = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                               user.id)
        # if the user is already registered, reject application
        if registered_check is not None:
            return await interaction.followup.send(f"You are already registered. "
                                                   f"\nTo check information about your "
                                                   f"account with the Royal Bank of Thegye, use ``/rbt info``.")
        else:
            # create button
            view = RegisterView()
            await interaction.followup.send("By becoming a member of the Royal Bank of "
                                            "Thegye, you agree to abide by the Terms of Service "
                                            "laid out here: https://www.nationstates.net/page=dispatch/id=1849820",
                                            view=view, ephemeral=True)

    @rbt.command(description="Displays Royal Bank of Thegye information about a specified member.",
                 name="info")
    @app_commands.describe(user="A Discord user.")
    async def info(self, interaction: discord.Interaction, user: discord.User = None):
        # defer response
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # gets user
        if user is None:
            user = interaction.user
        # fetches RBT member information
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)
        if rbt_member is None:
            return await interaction.followup.send(f"``{user}`` is not a registered member of "
                                                   f"the Royal Bank of Thegye.")
        else:
            # define membership type
            if rbt_member['premium_user'] is True:
                user_type = "Premium"
            else:
                user_type = "Standard"
            # create embed
            rbtm_embed = discord.Embed(title=f"{user.nick}", description=f"Information about the Royal Bank of Thegye"
                                                                         f" member {user.name}#{user.discriminator}.",
                                       color=discord.Color.gold())
            rbtm_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
            rbtm_embed.add_field(name="Thaler", value=f"{self.thaler}{rbt_member['funds']:,.2f}")
            rbtm_embed.add_field(name="Membership", value=f"{user_type}")
            return await interaction.followup.send(embed=rbtm_embed)

    @rbt.command(name="create_contract", description="Creates a new contract.")
    @app_commands.describe(terms="The terms of your contract.")
    async def create_contract(self, interaction: discord.Interaction,
                              terms: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # fetches RBT member information
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)
        if rbt_member is None:
            return await interaction.followup.send(f"You are not a registered member of "
                                                   f"the Royal Bank of Thegye.")
        # inserts pending contract
        await conn.execute('''INSERT INTO contracts VALUES($1,$2,$3,$4);''',
                           user.id, terms, [user.id], interaction.id)
        await conn.execute('''INSERT INTO rbt_user_log VALUES ($1,$2,$3);''',
                           user.id, 'contract', f"Created and signed contract #{interaction.id}.")
        return await interaction.followup.send(
            f"You have successfully created and signed contract #{interaction.id}. \n"
            f"Using the command `/rbt sign_contract`, any member of the RBT may sign this "
            f"contract by using the contract ID number.")

    @rbt.command(name="sign_contract", description="Signs a contract.")
    @app_commands.describe(contract_id="The contract ID you want to sign.")
    async def sign_contract(self, interaction: discord.Interaction, contract_id: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # turn string input into integer
        try:
            contract_id = int(contract_id)
        except ValueError:
            return await interaction.followup.send("That is not a valid contract ID. "
                                                   "Ensure you are using only numbers.")
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # fetches RBT member information
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)
        if rbt_member is None:
            return await interaction.followup.send(f"You are not a registered member of "
                                                   f"the Royal Bank of Thegye.")
        # fetches contract information
        contract = await conn.fetchrow('''SELECT * FROM contracts WHERE contract_id = $1;''',
                                       contract_id)
        if contract_id is None:
            return await interaction.followup.send(f"There is no contract with ID: `{contract_id}`.")
        # if the user is already a signatory, reject
        if user.id in contract['signatories']:
            return await interaction.followup.send("You are already a signatory on that contract.")
        # creates terms file
        with open(f"{contract_id}_terms.txt", "w+") as terms:
            terms.write(f"Contract ID: {contract_id}\n"
                        f"Signatories: {[s for s in contract['signatories']]}\n"
                        f"--Terms--\n"
                        f"{contract['terms']}")
        # sends contract terms file
        terms_message = await interaction.followup.send(file=discord.File(fp=f"{contract_id}_terms.txt"))
        # adds buttons
        await terms_message.edit(view=ContractSign(terms_message, contract_id))

    @rbt.command(name="view_contract", description="Displays a contract.")
    @app_commands.describe(contract_id="The ID of the contract to view. Must be an integer.")
    async def view_contract(self, interaction: discord.Interaction, contract_id: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # turn string input into integer
        try:
            contract_id = int(contract_id)
        except ValueError:
            return await interaction.followup.send("That is not a valid contract ID. "
                                                   "Ensure you are using only numbers.")
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # fetches RBT member information
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)
        if rbt_member is None:
            return await interaction.followup.send(f"You are not a registered member of "
                                                   f"the Royal Bank of Thegye.")
        # fetches contract information
        contract = await conn.fetchrow('''SELECT * FROM contracts WHERE contract_id = $1;''',
                                       contract_id)
        if contract_id is None:
            return await interaction.followup.send(f"There is no contract with ID: `{contract_id}`.")
        # creates terms file
        with open(f"{contract_id}_terms.txt", "w+") as terms:
            terms.write(f"Contract ID: {contract_id}\n"
                        f"Signatories: {[s for s in contract['signatories']]}\n"
                        f"--Terms--\n"
                        f"{contract['terms']}")
        # sends contract terms file
        return await interaction.followup.send(file=discord.File(fp=f"{contract_id}_terms.txt"))

    @rbt.command(name="fund_info", description="Displays information about a given fund.")
    @app_commands.describe(fund="The name of the fund.")
    async def fund_info(self, interaction: discord.Interaction,
                        fund: typing.Literal['General Fund', 'Investment Fund']):
        pass

    @rbt.command(name='log', description="Sends a log of all trades, buys, sells, signed contracts, "
                                         "and marketplace transactions.")
    @app_commands.describe(log_type="Input one of the choices to view your log")
    async def log(self, interaction: discord.Interaction,
                  log_type: typing.Literal['exchange', 'trade', 'contract', 'market', 'all']):
        # defer response
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # defines user
        user = interaction.user
        # fetches RBT member information
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)
        if rbt_member is None:
            return await interaction.followup.send(f"You are not a registered member of the Royal Bank of Thegye.")
        # fetch logs
        if log_type != 'all':
            logs = await conn.fetch('''SELECT * FROM rbt_user_log WHERE user_id = $1 AND action = $2 
            ORDER BY timestamp DESC;''', user.id, log_type)
        else:
            logs = await conn.fetch('''SELECT * FROM rbt_user_log WHERE user_id = $1 
                        ORDER BY timestamp DESC;''', user.id)
        with open(rf"{user.id}_exchange_log.txt", "w+", encoding="UTF-8") as exchange_log:
            exchange_log.write("Note that transactions are ordered by most recent.\n")
            for log in logs:
                exchange_log.write(f"[{log['timestamp']}] {log['description']}\n")
        return await interaction.followup.send(file=discord.File(fp=f"{user.id}_exchange_log.txt",
                                                                 filename=f"{user.id}_exchange_log.txt"))

    # creates exchange subgroup
    exchange = app_commands.Group(name="exchange", description="...", guild_only=True)

    async def market_updating(self):
        try:
            # wait for bot to be ready
            await self.bot.wait_until_ready()
            # define crash channel
            crashchannel = self.bot.get_channel(835579413625569322)
            # define bank channel
            bankchannel = self.bot.get_channel(855155865023021066)
            # set timezone
            eastern = timezone('US/Eastern')
            while True:
                # define now
                now = datetime.now(eastern)
                # set the run to be the next hour
                next_run = now.replace(minute=0, second=0)
                next_run += timedelta(hours=1)
                # sends the next runtime
                await crashchannel.send(f"Stock market update waiting until "
                                        f"{next_run.strftime('%d %b %Y at %H:%M %Z%z')}")
                # sleep until then
                await discord.utils.sleep_until(next_run)
                # establish connection
                conn = self.bot.pool
                # define announcement string
                new_shares = 0
                # STOCK MARKET UPDATING
                # fetch all stock info
                stocks = await conn.fetch('''SELECT * FROM stocks;''')
                # for each stock, update information
                for stock in stocks:
                    # define trending
                    trending = "up"
                    # define value
                    value = float(float(stock['value']))
                    # calculate trending course if up
                    if stock['trending'] == "up":
                        # if the d100 rolls less than the appropriate percent, change
                        change_chance = randint(1, 100)
                        if change_chance <= 5 * stock['risk']:
                            trending = "down"
                        else:
                            trending = "up"
                    # calculate trending course if down
                    elif stock['trending'] == "down":
                        # if the d100 rolls less than the appropriate percent, change
                        change_chance = randint(1, 100)
                        if change_chance <= 7 * stock['risk']:
                            trending = "up"
                        else:
                            trending = "down"
                    value_roll = uniform(1, 7 * stock['risk'])
                    # if the trend is up, increase stock based on risk
                    if trending == "up":
                        value = (value +
                                 (((value_roll / 100) + (stock['outstanding'] / stock['issued'] * 10))
                                  * value))
                        change = round(1 - (int(stock['value']) / value), 4)
                    else:
                        value = (value -
                                 (((value_roll / 100) + (stock['outstanding'] / stock['issued'] * 10))
                                  * value))
                        change = round(1 - (int(stock['value']) / value), 4)

                    # if the outstanding shares is between 25 and 50 shares away from the total issued shares,
                    # increase by half and dilute by (5 * risk to 10 * risk)% capped at 23%
                    if stock['issued'] - stock['outstanding'] < randint(25, 50):
                        # royal bonds are immune to automatic dilution
                        if stock['stock_id'] != 1:
                            new_shares = stock['issued'] / 5
                            dilution = round(uniform(5 * stock['risk'], 10 * stock['risk']), 2)
                            diluted_value = value * (clip(dilution, 0, 23) / 100)
                            self.announcement += f"{stock['name']} has been diluted. Issued shares have increased to {new_shares}," \
                                                 f" and the diluted value is now {self.thaler}{diluted_value} per share.\n"
                    # update stock information
                    await conn.execute('''UPDATE stocks SET value = ROUND($1,2), issued = issued + $2, trending = $3, 
                    change = $4 WHERE stock_id = $5;''', value, new_shares, trending, change, stock['stock_id'])
                # calculate value of stocks
                stock_sum = await conn.fetchrow('''SELECT SUM(value) FROM stocks;''')
                # fetch stock count
                stock_count = await conn.fetchrow('''SELECT COUNT(*) FROM stocks;''')
                # calculate market crash chance
                if self.crash is True:
                    recovery_chance = uniform(1, 20)
                    if recovery_chance <= 8:
                        self.crash = False
                        self.announcement += "The Royal Bank of Thegye announces the end of the **Exchange Crash**.\n" \
                                             "Stock prices have recovered by 25%.\n "
                        await conn.execute('''UPDATE stocks SET value = ROUND((value*.1.25)::numeric, 2);''')
                    else:
                        await conn.execute('''UPDATE stocks SET value = ROUND((value * .25)::numeric, 2);''')
                        self.announcement += "The Royal Bank of Thegye is observing an **Exchange Crash**. " \
                                             "All stock values are decreased by 75%.\n "
                crash_chance = uniform(1, 100)
                if crash_chance <= 9:
                    if self.crash is False:
                        if stock_sum['sum'] > 10 * stock_count['count']:
                            await conn.execute('''UPDATE stocks SET value = round((value * .25)::numeric, 2);''')
                            self.announcement += "The Royal Bank of Thegye has observed an **Exchange Crash**. " \
                                                 "All stock values are decreased by 75%.\n "
                            self.crash = True
                # ensure no stock drops below 6 - risk thaler (max at 5 thaler)
                await conn.execute('''UPDATE stocks SET value = 6-risk WHERE value < 5-risk;''')
                # update stocks' value tracker
                await conn.execute('''INSERT INTO exchange_log(stock_id, value, trend)
                SELECT stock_id, value, trending FROM stocks;''')
                # announce
                await bankchannel.send(content=self.announcement)
                self.announcement = \
                    "The Royal Exchange of Thegye has updated. Below is a summary of any important changes:\n"
                continue
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

    @commands.command()
    @commands.is_owner()
    async def force_market_update(self, ctx):
        crashchannel = ctx
        # establish connection
        conn = self.bot.pool
        # define announcement string
        new_shares = 0
        # STOCK MARKET UPDATING
        # fetch all stock info
        stocks = await conn.fetch('''SELECT * FROM stocks;''')
        # for each stock, update information
        for stock in stocks:
            # define trending
            trending = "up"
            # define value
            value = float(float(stock['value']))
            # calculate trending course if up
            if stock['trending'] == "up":
                # if the d100 rolls less than the appropriate percent, change
                change_chance = randint(1, 100)
                if change_chance <= 5 * stock['risk']:
                    trending = "down"
                else:
                    trending = "up"
            # calculate trending course if down
            elif stock['trending'] == "down":
                # if the d100 rolls less than the appropriate percent, change
                change_chance = randint(1, 100)
                if change_chance <= 7 * stock['risk']:
                    trending = "up"
                else:
                    trending = "down"
            value_roll = uniform(1, 7 * stock['risk'])
            # if the trend is up, increase stock based on risk
            if trending == "up":
                value = (value +
                         (((value_roll / 100) + (stock['outstanding'] / stock['issued'] * 10))
                          * value))
                change = round(1 - (int(stock['value']) / value), 4)
            else:
                value = (value -
                         (((value_roll / 100) + (stock['outstanding'] / stock['issued'] * 10))
                          * value))
                change = round(1 - (int(stock['value']) / value), 4)

            # if the outstanding shares is between 25 and 50 shares away from the total issued shares,
            # increase by half and dilute by (5 * risk to 10 * risk)% capped at 23%
            if stock['issued'] - stock['outstanding'] < randint(25, 50):
                # royal bonds are immune to automatic dilution
                if stock['stock_id'] != 1:
                    new_shares = stock['issued'] / 5
                    dilution = round(uniform(5 * stock['risk'], 10 * stock['risk']), 2)
                    diluted_value = value * (clip(dilution, 0, 23) / 100)
                    self.announcement += f"{stock['name']} has been diluted. Issued shares have increased to {new_shares}," \
                                         f" and the diluted value is now {self.thaler}{diluted_value} per share.\n"
            # update stock information
            await conn.execute('''UPDATE stocks SET value = ROUND($1,2), issued = issued + $2, trending = $3, 
                            change = $4 WHERE stock_id = $5;''', value, new_shares, trending, change, stock['stock_id'])
        # calculate value of stocks
        stock_sum = await conn.fetchrow('''SELECT SUM(value) FROM stocks;''')
        # fetch stock count
        stock_count = await conn.fetchrow('''SELECT COUNT(*) FROM stocks;''')
        # calculate market crash chance
        if self.crash is True:
            recovery_chance = uniform(1, 20)
            if recovery_chance <= 8:
                self.crash = False
                self.announcement += "The Royal Bank of Thegye announces the end of the **Exchange Crash**.\n" \
                                     "Stock prices have recovered by 25%.\n "
                await conn.execute('''UPDATE stocks SET value = ROUND((value*.1.25)::numeric, 2);''')
            else:
                await conn.execute('''UPDATE stocks SET value = ROUND((value * .25)::numeric, 2);''')
                self.announcement += "The Royal Bank of Thegye is observing an **Exchange Crash**. " \
                                     "All stock values are decreased by 75%.\n "
        crash_chance = uniform(1, 100)
        if crash_chance <= 9:
            if self.crash is False:
                if stock_sum['sum'] > 10 * stock_count['count']:
                    await conn.execute('''UPDATE stocks SET value = round((value * .25)::numeric, 2);''')
                    self.announcement += "The Royal Bank of Thegye has observed an **Exchange Crash**. " \
                                         "All stock values are decreased by 75%.\n "
                    self.crash = True
        # ensure no stock drops below 6 - risk thaler (max at 5 thaler)
        await conn.execute('''UPDATE stocks SET value = 6-risk WHERE value < 5-risk;''')
        # update stocks' value tracker
        await conn.execute('''INSERT INTO exchange_log(stock_id, value, trend)
                        SELECT stock_id, value, trending FROM stocks;''')
        # announce
        await crashchannel.send(content=self.announcement)
        self.announcement = \
            "The Royal Exchange of Thegye has updated. Below is a summary of any important changes:\n"

    @exchange.command(description="Displays information about a specified stock.", name="stock")
    @app_commands.describe(stock_id="The name or ID of the stock")
    async def stock(self, interaction: discord.Interaction, stock_id: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # fetches stock information
        stock = await conn.fetchrow('''SELECT * FROM stocks WHERE lower(name) = $1;''', stock_id.lower())
        # if stock does not exist, return message
        if stock is None:
            try:
                stock = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''', int(stock_id))
            except ValueError:
                return await interaction.followup.send(f"``{stock_id}`` does not exist on the Exchange.")
        # if it does, send information
        if stock is not None:
            if stock['risk'] == 1:
                risk = "Stable"
            elif stock['risk'] == 2:
                risk = "Moderate"
            else:
                risk = "Volatile"
            stock_embed = discord.Embed(title=f"{stock['name']}",
                                        description=f"Information about publicly traded stock #{stock['stock_id']}.",
                                        color=discord.Color.gold())
            stock_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
            stock_embed.add_field(name="Description", value=stock['description'], inline=False)
            stock_embed.add_field(name="Value per share", value=f"{self.thaler}{float(stock['value']):,.2f}",
                                  inline=False)
            stock_embed.add_field(name="Outstanding Shares", value=f"{stock['outstanding']}")
            stock_embed.add_field(name="Issued Shares", value=f"{stock['issued']}")
            stock_embed.add_field(name="\u200b", value="\u200b")
            stock_embed.add_field(name="Trend", value=f"{stock['trending'].title()}")
            stock_embed.add_field(name="Risk Type", value=f"{risk}")
            stock_embed.add_field(name="\u200b", value="\u200b")
            return await interaction.followup.send(embed=stock_embed)

    @exchange.command(description="Purchases a specified amount of a stock's shares.", name="buy")
    @app_commands.describe(stock_id="The name or ID of the stock", amount="A whole number amount")
    async def buy(self, interaction: discord.Interaction, stock_id: str, amount: app_commands.Range[int, 1, None]):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # if the amount is less than 0
        if amount <= 0:
            return await interaction.followup.send(f"Positive whole numbers only!")
        # fetches stock information
        stock = await conn.fetchrow('''SELECT * FROM stocks WHERE lower(name) = $1;''', stock_id.lower())
        # if stock does not exist, return message
        if stock is None:
            try:
                stock = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''', int(stock_id))
            except ValueError:
                return await interaction.followup.send(f"``{stock_id}`` does not exist on the Exchange.")
        # if the stock would become overdrawn, notify user
        if amount + stock['outstanding'] > stock['issued']:
            return await interaction.followup.send(f"Purchasing {amount} shares of {stock['name']} would cause it to "
                                                   f"be overdrawn. Either purchase an appropriate number of issued"
                                                   f"shares or notify a Director to increase the number of shares of"
                                                   f"this company.")
        # fetches user information
        user = interaction.user
        # fetches RBT member information
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)
        if rbt_member is None:
            return await interaction.followup.send(f"You are not a registered member of the Royal Bank of Thegye.")
        # define transaction cost
        base_price = round(float(stock['value']) * amount, 2)
        tax = math.ceil(base_price * .005)
        transaction = round(base_price + tax, 2)
        # check for sufficient funds and return if not
        if transaction > rbt_member['funds']:
            return await interaction.followup.send(f"You do not have enough funds to purchase that amount of shares.\n"
                                                   f"{amount:,.2f} shares of **{stock['name']}** cost "
                                                   f"**{self.thaler}{transaction:,.2f}**, meaning a deficit of "
                                                   f"**{self.thaler}{round(transaction - rbt_member['funds'], 2):,.2f}**.")
        else:
            # remove appropriate funds from user
            await conn.execute('''UPDATE rbt_users SET funds = ROUND(funds::numeric - $1, 2) WHERE user_id = $2;''',
                               transaction, user.id)
            # update stock
            await conn.execute('''UPDATE stocks SET outstanding = outstanding + $1 WHERE stock_id = $2;''',
                               amount, stock['stock_id'])
            # add to ledger
            register = await conn.fetchrow('''SELECT * FROM ledger WHERE stock_id = $1 and user_id = $2;''',
                                           stock['stock_id'], user.id)
            if register is not None:
                await conn.execute('''UPDATE ledger SET amount = amount + $1 WHERE stock_id = $2 and user_id = $3;''',
                                   amount, stock['stock_id'], user.id)
            else:
                await conn.execute('''INSERT INTO ledger VALUES($1,$2,$3,$4);''',
                                   user.id, stock['stock_id'], amount, stock['name'])
            # credit to fund
            await conn.execute('''UPDATE funds SET current_funds = ROUND(current_funds::numeric + $1, 2)
             WHERE name = 'General Fund';''', transaction)
            # log buy
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'exchange', f'Bought {amount} {stock["name"]} (id: {stock["stock_id"]}) @ '
                                                    f'{self.thaler}{stock["value"]} for {self.thaler}{transaction}.')
            return await interaction.followup.send(
                f"You have successfully purchased {amount} shares of {stock['name']} for "
                f"{self.thaler}{transaction:,.2f} at {self.thaler}{float(stock['value']):,.2f} per share.\n"
                f"{self.thaler}{base_price:,.2f} + {self.thaler}{tax:,.2f} (transaction fee) = "
                f"{self.thaler}{transaction:,.2f}")

    @exchange.command(description="Sells a specified amount of a stock's shares.",
                      name="sell")
    @app_commands.describe(stock_id="The name or ID of the stock", amount="A whole number amount")
    async def sell(self, interaction: discord.Interaction, stock_id: str, amount: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        if amount.lower() != "all":
            amount = int(amount)
            # if the amount is less than 0
            if amount <= 0:
                return await interaction.followup.send(f"Positive whole numbers only!")
        else:
            amount = "all"
        # fetches stock information
        stock = await conn.fetchrow('''SELECT * FROM stocks WHERE lower(name) = $1;''', stock_id.lower())
        # if stock does not exist, return message
        if stock is None:
            stock = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''', int(stock_id))
            if stock is None:
                return await interaction.followup.send(f"``{stock_id}`` does not exist on the Exchange.")
        # fetches user information
        user = interaction.user
        # fetches RBT member information
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)
        # if the user is not a member
        if rbt_member is None:
            return await interaction.followup.send(f"You are not a registered member of the Royal Bank of Thegye.")
        # fetch share information
        shares = await conn.fetchrow('''SELECT * FROM ledger WHERE stock_id = $1 and user_id = $2;''',
                                     stock['stock_id'], user.id)
        # if the user does not own the proper amount of stock, return a negative
        if shares is None:
            return await interaction.followup.send(f"You do not own any shares of {stock['name']}.")
        # if the amount is not all, check to make sure they own the requested amount
        if amount != "all":
            if shares['amount'] < amount:
                return await interaction.followup.send(f"You do not own {amount} shares of {stock['name']}")
        # if the amount is all, set amount to the number of owned shares
        elif amount == "all":
            amount = shares['amount']
        # calculate transaction
        base_price = round(float(stock['value']) * amount, 2)
        tax = math.ceil(base_price * .005)
        transaction = round(base_price - tax, 2)
        # ADD FUND MINTING CHECK LATER
        # remove stock from ledger
        await conn.execute('''UPDATE ledger SET amount = amount - $1 WHERE stock_id = $2 and user_id = $3;''',
                           amount, stock['stock_id'], user.id)
        # remove any 0-share holdings
        await conn.execute('''DELETE FROM ledger WHERE amount = 0;''')
        # credit funds to user's account
        await conn.execute('''UPDATE rbt_users SET funds = ROUND(funds::numeric + $1, 2) WHERE user_id = $2;''',
                           transaction, user.id)
        # log sale
        await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                           user.id, 'exchange', f'Sold {amount} {stock["name"]} (id: {stock["stock_id"]}) @ '
                                                f'{self.thaler}{stock["value"]} for {self.thaler}{transaction}.')
        return await interaction.followup.send(f"You have successfully sold {amount} shares of {stock['name']} for "
                                               f"{self.thaler}{transaction:,.2f} at "
                                               f"{self.thaler}{float(stock['value'])} per share.\n"
                                               f"{self.thaler}{base_price:,.2f} - {self.thaler}{tax:,.2f} "
                                               f"(transaction fee) = {self.thaler}{transaction:,.2f}")

    @exchange.command(description="Exchanges stock between two parties.", name="trade")
    @app_commands.describe(recipient="A Discord user you wish to trade with.",
                           stock_id="The name or ID of the stock",
                           amount="A whole number amount")
    async def trade(self, interaction: discord.Interaction, recipient: discord.User, stock_id: str,
                    amount: app_commands.Range[int, 1, None]):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # ensure user is a member
        author = interaction.user
        author_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''', author.id)
        if author_info is None:
            return await interaction.followup.send("You are not a member of the Bank.")
        recipient_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                             recipient.id)
        if recipient_info is None:
            return await interaction.followup.send(f"``{recipient.name}`` is not a member of the Bank.")

        # fetches stock information
        stock = await conn.fetchrow('''SELECT * FROM stocks WHERE lower(name) = $1;''', stock_id.lower())
        # if stock does not exist, return message
        if stock is None:
            try:
                stock = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''', int(stock_id))
            except ValueError:
                return await interaction.followup.send(f"``{stock_id}`` does not exist on the Exchange.")
        # fetch share information
        shares = await conn.fetchrow('''SELECT * FROM ledger WHERE stock_id = $1 and user_id = $2;''',
                                     stock['stock_id'], author.id)
        # if the user does not own the proper amount of stock, return a negative
        if shares is None:
            return await interaction.followup.send(f"You do not own any shares of {stock['name']}.")
        # check to make sure they own the requested amount
        if shares['amount'] < amount:
            return await interaction.followup.send(f"You do not own {amount} shares of {stock['name']}")
        # remove stock from ledger of author
        await conn.execute('''UPDATE ledger SET amount = amount - $1 WHERE stock_id = $2 and user_id = $3;''',
                           amount, stock['stock_id'], author.id)
        # remove any 0-share holdings
        await conn.execute('''DELETE FROM ledger WHERE amount = 0;''')
        # add to ledger of recipient
        register = await conn.fetchrow('''SELECT * FROM ledger WHERE stock_id = $1 and user_id = $2;''',
                                       stock['stock_id'], recipient.id)
        if register is not None:
            await conn.execute('''UPDATE ledger SET amount = amount + $1 WHERE stock_id = $2 and user_id = $3;''',
                               amount, stock['stock_id'], recipient.id)
        else:
            await conn.execute('''INSERT INTO ledger VALUES($1,$2,$3,$4);''',
                               recipient.id, stock['stock_id'], amount, stock['name'])
        # log trade
        await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                           author.id, 'trade', f'Traded {amount} {stock["name"]} (id: {stock["stock_id"]}) to '
                                               f'{recipient.name}#{recipient.discriminator} ({recipient.id}) @ '
                                               f'{self.thaler}{stock["value"]}.')

    @exchange.command(name='portfolio', description='Displays information about all owned shares and stocks.')
    @app_commands.describe(user="A Discord user.")
    async def portfolio(self, interaction: discord.Interaction, user: discord.User = None):
        # defer response
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # gets user
        if user is None:
            user = interaction.user
        # fetches RBT member information
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)

        if rbt_member is None:
            return await interaction.followup.send(f"``{user}`` is not a registered member of "
                                                   f"the Royal Bank of Thegye.")
        else:
            # create embed for user portfolio
            portfolio_embed = discord.Embed(title=f"Portfolio of {user.nick}",
                                            description=f"Value information of Royal Bank of Thegye member "
                                                        f"{user.name}#{user.discriminator}.")
            portfolio_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
            portfolio_embed.add_field(name="Current Thaler", value=f"{self.thaler}{rbt_member['funds']:,.2f}")
            # fetch all ledger information
            ledger_info = await conn.fetch('''SELECT * FROM ledger WHERE user_id = $1;''', user.id)
            ledger_string = ""
            stock_value = 0
            for shares in ledger_info:
                stock = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''', shares['stock_id'])
                this_string = f"{shares['name']} (#{shares['stock_id']}): " \
                              f"{shares['amount']} @ {self.thaler}{stock['value']:,.2f}"
                if stock['trending'] == "up":
                    this_string += " :chart_with_upwards_trend: +"
                else:
                    this_string += " :chart_with_downwards_trend: "
                this_string += f"{stock['change'] * 100:.2f}%\n" \
                               f"> Sale value: {self.thaler}" \
                               f"{round(float(shares['amount']) * float(stock['value']), 2):,.2f}\n"
                ledger_string += this_string
                stock_value += float(shares['amount']) * float(stock['value'])
            portfolio_embed.add_field(name="Stock Value", value=f"{self.thaler}{stock_value:,.2f}")
            portfolio_embed.add_field(name="Net Worth",
                                      value=f"{self.thaler}"
                                            f"{round(float(stock_value) + float(rbt_member['funds']), 2):,.2f}")
            portfolio_embed.add_field(name=f"Stocks and Shares", value=ledger_string)
            await interaction.followup.send(embed=portfolio_embed)

    @exchange.command(name="graph_stock_price", description="Displays a graph of a stock's price.")
    @app_commands.describe(stock_id="Input the name or ID of the stock.",
                           start_date="Input a valid date in day/month/year format. "
                                      "Also accepts \"today\", \"forever\", \"week\", and \"month\".",
                           end_date="Input a valid date in day/month/year format. If left blank, defaults to today.")
    async def graph_stock_price(self, interaction: discord.Interaction, stock_id: str, start_date: str,
                                end_date: str = None):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # fetches stock information
        stock = await conn.fetchrow('''SELECT * FROM stocks WHERE lower(name) = $1;''', stock_id.lower())
        # if stock does not exist, return message
        if stock is None:
            try:
                stock = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''', int(stock_id))
            except ValueError:
                return await interaction.followup.send(f"``{stock_id}`` does not exist on the Exchange.")
        # get datetime objects
        # if start_date is today, set for today
        if start_date.lower() == "today":
            start_date = datetime.now().replace(hour=0)
        elif start_date.lower() == "forever":
            start_date = datetime.now().replace(year=2000)
        elif start_date.lower() == "week":
            start_date = datetime.now() - timedelta(weeks=1)
        elif start_date.lower() == "month":
            start_date = datetime.now() - relativedelta(months=1)
        else:
            try:
                start_date = datetime.strptime(start_date, "%d/%m/%Y")
            except ValueError:
                return await interaction.followup.send(f"``{start_date}`` is not a properly formatted date.\n"
                                                       f"Dates should be formatted day/month/year. For example: "
                                                       f"9/1/2020.\n"
                                                       f"This command also accepts `today`, `week`, `month`, "
                                                       f"and `forever` as acceptable arguments.")
        # if the end date is none, get the time now
        if end_date is None:
            end_date = datetime.now()
        # otherwise, get the end date
        else:
            end_date = datetime.strptime(end_date, "%d/%m/%Y")
        # get all data from the specified stock
        stock_data = await conn.fetch('''SELECT * FROM exchange_log WHERE (timestamp BETWEEN $1 AND $2) 
        AND stock_id = $3 ORDER BY timestamp ASC;''', start_date, end_date, stock['stock_id'])
        print(stock_data)
        if not stock_data:
            return await interaction.followup.send(f"Unfortunately, I cannot find any data between"
                                                   f"`{start_date.date().strftime('%d/%m/%Y')}` and "
                                                   f"`{end_date.date().strftime('%d/%m/%Y')}`.")
        stock_prices = [s['value'] for s in stock_data]
        dates = [d['timestamp'] for d in stock_data]
        fig, ax = plt.subplots()
        ax.plot(dates, stock_prices)
        ax.xaxis.set_major_locator(DayLocator(interval=1))
        ax.xaxis.set_minor_locator(HourLocator(interval=1))
        ax.xaxis.set_major_formatter(DateFormatter("%m/%d/%y"))
        fig.autofmt_xdate()
        if start_date.day - end_date.day >= 3:
            plt.grid(True, which="major")
        else:
            plt.grid(True, which="major")
            plt.grid(True, which="minor")
        plt.title(f"{stock['name']}")
        plt.ylabel("Value")
        plt.xlabel("Time")
        plt.savefig(r"C:\Users\jaedo\OneDrive\Pictures\graph.png")
        return await interaction.followup.send(file=discord.File(fp=r"C:\Users\jaedo\OneDrive\Pictures\graph.png",
                                                                 filename=f"Graph of {stock['name']} share price.png",
                                                                 description=f"A graph representing the share prices of"
                                                                             f" {stock['name']}"))

    @exchange.command(name="feed", description="Displays share price and information about all stocks on the exchange.")
    async def feed(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # define space
        space = "\u200b"
        # define rank
        rank = 1
        # establish connection
        conn = self.bot.pool
        # fetch all stocks
        stocks = await conn.fetch('''SELECT * FROM stocks ORDER BY value DESC;''')
        stock_string = " "
        for stock in stocks[0:10]:
            this_string = f"``{rank}. {stock['name']} (#{stock['stock_id']}): " \
                          f"{self.thaler}{stock['value']:,.2f}"
            for space in range(0, 48 - len(this_string)):
                this_string += " "
            if stock['trending'] == "up":
                this_string += "``:chart_with_upwards_trend: ``+"
            else:
                this_string += "``:chart_with_downwards_trend: ``"
            this_string += f"{stock['change'] * 100:.2f}%``\n"
            rank += 1
            stock_string += this_string
        # create embed
        feed_embed = discord.Embed(title="Stocks by Share Price", description=stock_string)
        feed_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
        embed_message = await interaction.followup.send(embed=feed_embed)
        await embed_message.edit(view=FeedView(self.bot, embed_message))


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = Economy(bot)
    await bot.add_cog(cog)
