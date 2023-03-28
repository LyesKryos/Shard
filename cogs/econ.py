# Shard Economy v2a
from __future__ import annotations
import asyncio
import math
import traceback
import typing
from datetime import datetime, timedelta
from random import randint, uniform, choice
import discord
import pandas as pd
from dateutil.relativedelta import relativedelta
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
from matplotlib import pyplot as plt
from matplotlib.dates import HourLocator, DateFormatter, DayLocator, YearLocator
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
        general_fund = float(general_fund_raw['current_funds'])
        # calculate starting gift, credit it towards the user, and remove thaler from fund
        registration_gift = round(float(general_fund_raw['fund_limit']) * .001, 0)
        await conn.execute('''INSERT INTO rbt_users VALUES($1,$2);''',
                           user.id, registration_gift)
        await conn.execute('''INSERT INTO casino_rank(user_id) VALUES($1);''',
                           user.id)
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
                this_string = f"``{self.rank}. {stock['name']} (#{stock['stock_id']}): " \
                              f"{self.thaler}{stock['value']:,.2f}"
                for space in range(0, 50 - len(this_string)):
                    this_string += " "
                if stock['trending'] == "up":
                    this_string += "``:chart_with_upwards_trend: ``"
                else:
                    this_string += "``:chart_with_downwards_trend: ``"
                if stock['change'] >= 0:
                    this_string += "+"
                this_string += f"{stock['change'] * 100:.2f}%``\n"
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
                this_string = f"``{self.rank}. {stock['name']} (#{stock['stock_id']}): " \
                              f"{self.thaler}{stock['value']:,.2f}"
                for space in range(0, 50 - len(this_string)):
                    this_string += " "
                if stock['trending'] == "up":
                    this_string += "``:chart_with_upwards_trend: ``"
                else:
                    this_string += "``:chart_with_downwards_trend: ``"
                if stock['change'] >= 0:
                    this_string += "+"
                this_string += f"{stock['change'] * 100:.2f}%``\n"
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


class BlackjackView(View):

    def __init__(self, author, bot: Shard, m, dealer_hand, player_hand, bet):
        super().__init__(timeout=120)
        # define user
        self.author = author
        # define bot
        self.bot = bot
        # message
        self.message = m
        # dealer hand
        self.dealer_hand = dealer_hand
        # player hand
        self.player_hand = player_hand
        # deck
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A'] * 4
        # bet
        self.bet = bet
        # thaler
        self.thaler = "\u20B8"

    async def on_timeout(self) -> None:
        # disable all buttons
        for button in self.children:
            button.disabled = True
        return await self.message.edit(view=self)

    @discord.ui.button(label="Fold", style=discord.ButtonStyle.danger)
    async def fold(self, interaction: discord.Interaction, fold_button: discord.Button):
        try:
            # defer response
            await interaction.response.defer(thinking=False)
            # define user
            user = interaction.user
            # establish connection
            conn = interaction.client.pool
            # define emojis
            dealer_hand_string = "".join([get_card_emoji(c) for c in self.dealer_hand])
            player_hand_string = "".join([get_card_emoji(c) for c in self.player_hand])
            # define totals
            player_total = 0
            for card in self.player_hand:
                # if the card is a face card, give it a value of 10
                if card == "J" or card == "Q" or card == "K":
                    card = 10
                # if the card is an ace, give it a value of 11
                elif card == "A":
                    card = 11
                player_total += card
            dealer_total = 0
            for card in self.dealer_hand:
                # if the card is a face card, give it a value of 10
                if card == "J" or card == "Q" or card == "K":
                    card = 10
                # if the card is an ace, give it a value of 11
                elif card == "A":
                    card = 11
                dealer_total += card
            # create embed
            blackjack_embed = discord.Embed(title="Blackjack", description="A game of blackjack at the Casino Royal.")
            blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{self.bet:,.2f}", inline=False)
            blackjack_embed.add_field(name="Dealer's Hand",
                                      value=f"{dealer_hand_string} (total: {dealer_total})")
            blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
            blackjack_embed.add_field(name="Result", value="***FOLD***", inline=False)
            winnings = self.bet
            blackjack_embed.set_footer(text=f"Your total winnings: -{self.thaler}{winnings:,.2f}")
            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                               -winnings, user.id)
            await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                               -winnings, user.id)
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'casino', f'Lost {self.thaler}{winnings:,.2f} at blackjack')

            for buttons in self.children:
                buttons.disabled = True
            return await self.message.edit(embed=blackjack_embed, view=self)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.gray)
    async def hit(self, interaction: discord.Interaction, hit: discord.Button):
        try:
            # defer response
            await interaction.response.defer()
            self.player_hand.append(choice(self.deck))
            dealer_total = 0
            for card in self.dealer_hand:
                # if the card is a face card, give it a value of 10
                if card == "J" or card == "Q" or card == "K":
                    card = 10
                # if the card is an ace, give it a value of 11
                elif card == "A":
                    card = 11
                dealer_total += card
            while dealer_total < 17:
                self.dealer_hand.append(choice(self.deck))
                dealer_total = 0
                for card in self.dealer_hand:
                    # if the card is a face card, give it a value of 10
                    if card == "J" or card == "Q" or card == "K":
                        card = 10
                    # if the card is an ace, give it a value of 11
                    elif card == "A":
                        card = 11
                    dealer_total += card
                await asyncio.sleep(.1)
            # define user
            user = interaction.user
            # define bust
            bust = False
            # establish connection
            conn = interaction.client.pool
            # define emojis
            real_dealer_hand_string = "".join([get_card_emoji(c) for c in self.dealer_hand])
            dealer_hand_string = f"{get_card_emoji(self.dealer_hand[0])}{get_card_emoji('back')}"
            player_hand_string = "".join([get_card_emoji(c) for c in self.player_hand])
            # define totals
            player_total = 0
            for card in self.player_hand:
                # if the card is a face card, give it a value of 10
                if card == "J" or card == "Q" or card == "K":
                    card = 10
                # if the card is an ace, give it a value of 11
                elif card == "A":
                    card = 11
                player_total += card
            dealer_total = 0
            for card in self.dealer_hand:
                # if the card is a face card, give it a value of 10
                if card == "J" or card == "Q" or card == "K":
                    card = 10
                # if the card is an ace, give it a value of 11
                elif card == "A":
                    card = 11
                dealer_total += card
            # if the total is more than 21, change aces
            if player_total > 21:
                if "A" in self.player_hand:
                    for ace in self.player_hand:
                        if ace == "A":
                            player_total -= 10
                        if player_total < 21:
                            break
                    if player_total > 21:
                        bust = True
                # otherwise, the player busts
                else:
                    bust = True
            if dealer_total > 21:
                if "A" in self.dealer_hand:
                    for ace in self.dealer_hand:
                        if ace == "A":
                            dealer_total -= 10
                        if dealer_total < 21:
                            break
            if player_total == 21:
                # create embed
                blackjack_embed = discord.Embed(title="Blackjack",
                                                description="A game of blackjack at the Casino Royal.")
                blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{self.bet:,.2f}", inline=False)
                blackjack_embed.add_field(name="Dealer's Hand",
                                          value=f"{real_dealer_hand_string} (total: {dealer_total})")
                blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
                if dealer_total != 21:
                    winnings = round((self.bet * 3) - self.bet, 2)
                    blackjack_embed.add_field(name="Result", value="**BLACKJACK**", inline=False)
                else:
                    winnings = self.bet - self.bet
                    blackjack_embed.add_field(name="Result", value="**PUSH**", inline=False)
                blackjack_embed.set_footer(text=f"Your winnings total: {self.thaler}{winnings:,.2f}")
                await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                                   winnings, user.id)
                await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                                   winnings, user.id)
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'casino', f'Won {self.thaler}{winnings:,.2f} at blackjack')
                # disable buttons
                for button in self.children:
                    button.disabled = True
                return await self.message.edit(embed=blackjack_embed, view=self)
            elif bust is True:
                # create embed
                blackjack_embed = discord.Embed(title="Blackjack",
                                                description="A game of blackjack at the Casino Royal.")
                blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{self.bet:,.2f}", inline=False)
                blackjack_embed.add_field(name="Dealer's Hand",
                                          value=f"{real_dealer_hand_string} (total: {dealer_total})")
                blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
                blackjack_embed.add_field(name="Result", value="***BUST***", inline=False)
                winnings = self.bet
                blackjack_embed.set_footer(text=f"Your total winnings: -{self.thaler}{winnings:,.2f}")
                await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                                   -winnings, user.id)
                await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                                   -winnings, user.id)
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'casino', f'Lost {self.thaler}{winnings:,.2f} at blackjack')

                # disable buttons
                for buttons in self.children:
                    buttons.disabled = True
                return await self.message.edit(embed=blackjack_embed, view=self)
            else:
                # create embed
                blackjack_embed = discord.Embed(title="Blackjack",
                                                description="A game of blackjack at the Casino Royal.")
                blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{self.bet:,.2f}", inline=False)
                blackjack_embed.add_field(name="Dealer's Hand",
                                          value=f"{dealer_hand_string}")
                blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
                await self.message.edit(embed=blackjack_embed, view=self)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.green)
    async def stand(self, interaction: discord.Interaction, hold: discord.Button):
        try:
            # defer response
            await interaction.response.defer()
            # define user
            user = interaction.user
            # establish connection
            conn = interaction.client.pool
            dealer_total = 0
            for card in self.dealer_hand:
                # if the card is a face card, give it a value of 10
                if card == "J" or card == "Q" or card == "K":
                    card = 10
                # if the card is an ace, give it a value of 11
                elif card == "A":
                    card = 11
                dealer_total += card
            while dealer_total < 17:
                self.dealer_hand.append(choice(self.deck))
                dealer_total = 0
                for card in self.dealer_hand:
                    # if the card is a face card, give it a value of 10
                    if card == "J" or card == "Q" or card == "K":
                        card = 10
                    # if the card is an ace, give it a value of 11
                    elif card == "A":
                        card = 11
                    dealer_total += card
                await asyncio.sleep(.1)
            # define emojis
            real_dealer_hand_string = "".join([get_card_emoji(c) for c in self.dealer_hand])
            player_hand_string = "".join([get_card_emoji(c) for c in self.player_hand])
            # define totals
            player_total = 0
            for card in self.player_hand:
                # if the card is a face card, give it a value of 10
                if card == "J" or card == "Q" or card == "K":
                    card = 10
                # if the card is an ace, give it a value of 11
                elif card == "A":
                    card = 11
                player_total += card
            dealer_total = 0
            for card in self.dealer_hand:
                # if the card is a face card, give it a value of 10
                if card == "J" or card == "Q" or card == "K":
                    card = 10
                # if the card is an ace, give it a value of 11
                elif card == "A":
                    card = 11
                dealer_total += card
            # if the total is more than 21, change aces
            if player_total > 21:
                if "A" in self.player_hand:
                    for ace in self.player_hand:
                        if ace == "A":
                            player_total -= 10
                        if player_total < 21:
                            break
            if dealer_total > 21:
                if "A" in self.dealer_hand:
                    for ace in self.dealer_hand:
                        if ace == "A":
                            dealer_total -= 10
                        if dealer_total < 21:
                            break
            if player_total > dealer_total:
                # create embed
                blackjack_embed = discord.Embed(title="Blackjack",
                                                description="A game of blackjack at the Casino Royal.")
                blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{self.bet:,.2f}", inline=False)
                blackjack_embed.add_field(name="Dealer's Hand",
                                          value=f"{real_dealer_hand_string} (total: {dealer_total})")
                blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
                blackjack_embed.add_field(name="Result", value="**WIN**", inline=False)
                winnings = round((self.bet * 1.5) - self.bet, 2)
                blackjack_embed.set_footer(text=f"Your winnings total: {self.thaler}{winnings:,.2f}")
                await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                                   winnings, user.id)
                await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                                   winnings, user.id)
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'casino', f'Won {self.thaler}{winnings:,.2f} at blackjack')
                # disable buttons
                for button in self.children:
                    button.disabled = True
                return await self.message.edit(embed=blackjack_embed, view=self)
            elif dealer_total == player_total:
                # create embed
                blackjack_embed = discord.Embed(title="Blackjack",
                                                description="A game of blackjack at the Casino Royal.")
                blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{self.bet:,.2f}", inline=False)
                blackjack_embed.add_field(name="Dealer's Hand",
                                          value=f"{real_dealer_hand_string} (total: {dealer_total})")
                blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
                blackjack_embed.add_field(name="Result", value="**PUSH**", inline=False)
                winnings = self.bet - self.bet
                blackjack_embed.set_footer(text=f"Your winnings total: {self.thaler}{winnings:,.2f}")
                await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                                   winnings, user.id)
                await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                                   winnings, user.id)
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'casino', f'Won {self.thaler}{winnings:,.2f} at blackjack')
                # disable buttons
                for button in self.children:
                    button.disabled = True
                return await self.message.edit(embed=blackjack_embed, view=self)
            elif dealer_total > 21:
                # create embed
                blackjack_embed = discord.Embed(title="Blackjack",
                                                description="A game of blackjack at the Casino Royal.")
                blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{self.bet:,.2f}", inline=False)
                blackjack_embed.add_field(name="Dealer's Hand",
                                          value=f"{real_dealer_hand_string} (total: {dealer_total})")
                blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
                blackjack_embed.add_field(name="Result", value="**WIN**", inline=False)
                winnings = round((self.bet * 1.5) - self.bet, 2)
                blackjack_embed.set_footer(text=f"Your winnings total: {self.thaler}{winnings:,.2f}")
                await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                                   winnings, user.id)
                await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                                   winnings, user.id)
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'casino', f'Won {self.thaler}{winnings:,.2f} at blackjack')
                # disable buttons
                for button in self.children:
                    button.disabled = True
                return await self.message.edit(embed=blackjack_embed, view=self)
            else:
                # create embed
                blackjack_embed = discord.Embed(title="Blackjack",
                                                description="A game of blackjack at the Casino Royal.")
                blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{self.bet:,.2f}", inline=False)
                blackjack_embed.add_field(name="Dealer's Hand",
                                          value=f"{real_dealer_hand_string} (total: {dealer_total})")
                blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
                blackjack_embed.add_field(name="Result", value="***LOSS***", inline=False)
                winnings = self.bet
                blackjack_embed.set_footer(text=f"Your total winnings: -{self.thaler}{winnings:,.2f}")
                await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                                   -winnings, user.id)
                await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                                   -winnings, user.id)
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'casino',
                                   f'Lost {self.thaler}{winnings:,.2f} at blackjack')  # disable buttons
                for buttons in self.children:
                    buttons.disabled = True
                return await self.message.edit(embed=blackjack_embed, view=self)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id


class MarketDropdown(discord.ui.Select):

    def __init__(self, message):
        # define bot
        self.bot = None
        # define message
        self.message = message
        # define page
        self.page = 1
        # define options
        options = [
            discord.SelectOption(label="General Market", description="The market for all general needs.",
                                 emoji="\U0001fa99"),
            discord.SelectOption(label="Minecraft Market", description="The market for Minecraft items.",
                                 emoji="<:diamond_pickaxe:1087876208634638458>"),
            discord.SelectOption(label="Open Market", description="Public market for entrepreneurs.",
                                 emoji="\U0001F9FE")
        ]

        super().__init__(placeholder="Choose the market you wish to view...",
                         min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            # defer interaction
            await interaction.response.defer(thinking=False)
            # define bot
            self.bot = interaction.client
            # establish connection
            conn = self.bot.pool
            # parse market
            if self.values[0] == 'General Market':
                market = 'general'
            elif self.values[0] == 'Minecraft Market':
                market = 'minecraft'
            else:
                market = 'open'
            # fetch market items
            market_items = await conn.fetch('''SELECT * FROM rbt_market WHERE market = $1 ORDER BY market_id;''',
                                            market)
            # create embed
            market_embed = discord.Embed(title=f"{self.values[0]}",
                                         description="A display of all items in this market.")
            # paginator if there are more than 25 items in a market
            if len(market_items) > 12:
                page = 1
                for m in market_items[(page * 12) - 12:page * 12]:
                    market_embed.add_field(name=f"{m['name']} (ID: {m['market_id']})",
                                           value=f"Price: {m['value']}")
                await self.message.edit(embed=market_embed, view=SubMarketView(market=market, message=self.message,
                                                                               values=self.values))
            else:
                page = 1
                for m in market_items[(page * 12) - 12:page * 12]:
                    market_embed.add_field(name=f"{m['name']} (ID: {m['market_id']})",
                                           value=f"Price: {m['value']}")
                await self.message.edit(embed=market_embed)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")


class SubMarketView(View):

    def __init__(self, message, values, market):
        self.message = message
        self.page = 1
        self.values = values
        self.market = market
        super().__init__(timeout=300)
        self.add_item(MarketDropdown(message))

    async def on_timeout(self) -> None:
        # remove dropdown
        for item in self.children:
            self.remove_item(item)
        return await self.message.edit(content="Market closed.", view=self)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.blurple, disabled=True, emoji="\u23ea")
    async def back(self, interaction: discord.Interaction, back_button: discord.Button):
        # define bot
        bot = interaction.client
        try:
            # defer response
            await interaction.response.defer()
            # set foward button on
            self.forward.disabled = False
            # establish connection
            conn = interaction.client.pool
            # subtract from page
            self.page -= 1
            # page cannot be less than 1
            if self.page <= 1:
                self.page = 1
                back_button.disabled = True
            # fetch market items
            market_items = await conn.fetch('''SELECT * FROM rbt_market WHERE market = $1 ORDER BY market_id;''',
                                            self.market)
            # create embed
            market_embed = discord.Embed(title=f"{self.values[0]}",
                                         description="A display of all items in this market.")
            # paginator if there are more than 25 items in a market
            for m in market_items[(self.page * 12) - 12:self.page * 12]:
                market_embed.add_field(name=f"{m['name']} (ID: {m['market_id']})",
                                       value=f"Price: {m['value']}")
            market_embed.set_footer(text=f"Page #{self.page}")
            await self.message.edit(embed=market_embed, view=self)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            bot.logger.warning(msg=f"{traceback_text}")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, close: discord.Button):
        # define bot
        bot = interaction.client
        try:
            # defer response
            await interaction.response.defer()
            # remove dropdown and buttons
            for item in self.children:
                self.remove_item(item)
            return await self.message.edit(content="Market closed.", view=self)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            bot.logger.warning(msg=f"{traceback_text}")

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, emoji="\u23e9")
    async def forward(self, interaction: discord.Interaction, forward_button: discord.Button):
        bot = interaction.client
        try:
            # defer response
            await interaction.response.defer()
            # enable back button
            self.back.disabled = False
            # establish connection
            conn = interaction.client.pool
            # add page
            self.page += 1
            # fetch market items
            market_items = await conn.fetch('''SELECT * FROM rbt_market WHERE market = $1 ORDER BY market_id;''',
                                            self.market)
            # set max
            max_page = math.ceil(len(market_items) / 12)
            # disable forward on last page
            if self.page == max_page:
                forward_button.disabled = True
            # create embed
            market_embed = discord.Embed(title=f"{self.values[0]}",
                                         description="A display of all items in this market.")
            # paginator if there are more than 25 items in a market
            for m in market_items[(self.page * 12) - 12:self.page * 12]:
                market_embed.add_field(name=f"{m['name']} (ID: {m['market_id']})",
                                       value=f"Price: {m['value']:,}")
            for space in range(12 - len(market_items[(self.page * 12) - 12:self.page * 12])):
                market_embed.add_field(name="\u200b", value="\u200b")
            market_embed.set_footer(text=f"Page #{self.page}")
            await self.message.edit(embed=market_embed, view=self)
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            bot.logger.warning(msg=f"{traceback_text}")


class MarketView(View):
    def __init__(self, message):
        self.message = message
        super().__init__(timeout=300)

        self.add_item(MarketDropdown(message=self.message))

    async def on_timeout(self) -> None:
        # remove dropdown
        for item in self.children:
            self.remove_item(item)
        return await self.message.edit(content="Market closed.", view=self)


class LoanDropdown(Select):

    def __init__(self, amount, user, message):
        # define thaler icon
        self.thaler = "\u20B8"
        # define stuff we need
        self.amount = amount
        self.user = user
        self.message = message
        # define weeks from now
        self.one_week = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=7)
        self.two_weeks = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=14)
        self.three_weeks = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=21)
        self.month = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + relativedelta(months=1)
        # define options
        options = [
            discord.SelectOption(label="One Week Loan",
                                 description=f"Loan due one week from today at midnight @ 10% interest per term"),
            discord.SelectOption(label="Two Week Loan",
                                 description=f"Loan due two weeks from today at midnight @ 8% interest per term"),
            discord.SelectOption(label="Three Week Loan",
                                 description=f"Loan due three weeks from today at midnight @ 6% interest per term"),
            discord.SelectOption(label="One Month Loan",
                                 description=f"Loan due one month from today at midnight @ 4% interest per term")
        ]

        super().__init__(placeholder="Choose the length of loan...",
                         min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=False)
        # disable dropdown
        self.view.remove_item(item=self)
        # parse interest
        if self.values[0] == "One Week Loan":
            interest = 10
            due = self.one_week
        elif self.values[0] == "Two Week Loan":
            interest = 8
            due = self.two_weeks
            if self.amount < 10000:
                return await interaction.followup.send(f"Two week loans must be more than {self.thaler}10,000.",
                                                       ephemeral=True)
        elif self.values[0] == "Three Week Loan":
            interest = 6
            due = self.three_weeks
            if self.amount < 50000:
                return await interaction.followup.send(f"Three week loans must be more than {self.thaler}50,000.",
                                                       ephemeral=True)
        else:
            interest = 4
            due = self.month
            if self.amount < 100000:
                return await interaction.followup.send(f"Month loans must be more than {self.thaler}100,000.",
                                                       ephemeral=True)
        # establish connection
        conn = interaction.client.pool
        # apply interest to amount
        self.amount = round(self.amount * (1 + (interest / 100)), 2)
        # remove funds from investment fund
        await conn.execute('''UPDATE funds SET current_funds = current_funds - $1 
            WHERE name = 'Investment Fund';''', self.amount)
        # create loan account
        await conn.execute('''INSERT INTO bank_ledger(user_id, account_id, amount, type, interest, due_date) 
        VALUES($1,$2,$3,$4,$5,$6);''', self.user.id, interaction.id, self.amount, 'loan', interest, due)
        # credit to user account and log
        await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                           self.amount, self.user.id)
        await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                           self.user.id, 'bank', f"Opened a new loan account (ID: {interaction.id}) "
                                                 f"with {self.thaler}{self.amount:,.2f}.")
        return await self.message.edit(content=f"You have successfully opened a loan account (ID:{interaction.id}) "
                                               f"with {self.thaler}{self.amount:,.2f}. This loan becomes due: "
                                               f"<t:{int(due.timestamp())}:f>.\n"
                                               f"Note that interest is applied to the principle proactively.",
                                       view=self.view)


class LoanView(View):
    def __init__(self, amount, user, message: discord.Message):
        self.message = message
        super().__init__(timeout=300)
        self.add_item(LoanDropdown(amount, user, message))

    async def on_timeout(self):
        # remove dropdown
        for item in self.children:
            self.remove_item(item)
        return await self.message.edit(content="Loans closed.", view=self)


def get_card_emoji(card):
    # define emoji strings for card
    K_card = '<:K_card:1085224694631907409>'
    Q_card = '<:Q_card:1085224695877603449>'
    J_card = '<:J_card:1085224693214228640>'
    A_card = '<:A_card:1085224623517483019>'
    ten_card = '<:10_card:1085225393616855120> '
    nine_card = '<:9_card:1085224621625839666>'
    eight_card = '<:8_card:1085224619960713236>'
    seven_card = '<:7_card:1085224619050553365>'
    six_card = '<:6_card:1085224617377009755>'
    five_card = '<:5_card:1085224615850291253>'
    four_card = '<:4_card:1085224614550057161>'
    three_card = '<:3_card:1085224612931047455>'
    two_card = '<:2_card:1085224612511629392>'
    back_card = '<:Back:1085224690857029734>'
    axolotl = '<:axolotl:1079750003729371176>'
    star = ':dizzy:'
    moon = ':crescent_moon:'
    bell = ':bell:'
    heart = ':hearts:'
    diamond = ':diamonds:'
    cherry = ':cherries:'
    clover = ":four_leaf_clover:"
    seven = ":seven:"
    gem = ":gem:"
    # return the card emoji string for the card called
    if card == "K":
        return K_card
    elif card == "Q":
        return Q_card
    elif card == "J":
        return J_card
    elif card == "A":
        return A_card
    elif card == 10:
        return ten_card
    elif card == 9:
        return nine_card
    elif card == 8:
        return eight_card
    elif card == 7:
        return seven_card
    elif card == 6:
        return six_card
    elif card == 5:
        return five_card
    elif card == 4:
        return four_card
    elif card == 3:
        return three_card
    elif card == 2:
        return two_card
    elif card == "back":
        return back_card
    elif card == 'axolotl':
        return axolotl
    elif card == 'star':
        return star
    elif card == 'moon':
        return moon
    elif card == 'bell':
        return bell
    elif card == "heart":
        return heart
    elif card == "diamond":
        return diamond
    elif card == "cherry":
        return cherry
    elif card == "clover":
        return clover
    elif card == "seven":
        return seven
    elif card == "gem":
        return gem
    elif card == "doubler":
        return '<:doubler:1085970114752557086>'
    elif card == "tripler":
        return '<:tripler:1085970117059428473>'


class Economy(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.announcement = "The Royal Exchange of Thegye has updated. Below is a summary of any important changes:\n"
        self.market_task = asyncio.create_task(self.market_updating())
        self.bank_task = asyncio.create_task(self.bank_updating())
        self.crash = False
        # define space
        self.space = "\u200b"
        # define logo
        self.logo = "https://i.ibb.co/BKFyd2G/RBT-logo.png"
        # define thaler icon
        self.thaler = "\u20B8"

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
                current_fund = float(general_fund['current_funds'])
                fund_limit = float(general_fund['fund_limit'])
                # if the general fund is near/overdrawn
                if current_fund <= (.02 * fund_limit):
                    # set new fund to 150% of old fund
                    new_limit = fund_limit * 1.5
                    additional_funds = fund_limit * .5
                    # update all market items in the general and minecraft market to increase by 25%
                    await conn.execute('''UPDATE rbt_market SET value = value * 1.25 
                    WHERE market != 'open' AND name = 'Wallet Expansion';''')
                    # update funds
                    await conn.execute('''UPDATE funds SET fund_limit = $1, current_funds = current_funds + $2 
                            WHERE name = 'General Fund';''', new_limit, additional_funds)
                # if the general fund is overfunded
                if current_fund > fund_limit:
                    # ensure the general fund is more than 500,000 thaler
                    if fund_limit > 500000:
                        # set the new fund limit to 50%
                        new_limit = fund_limit * .5
                        # calculate refund and new current funds
                        new_funds = fund_limit * .25
                        refund = current_fund - fund_limit
                        await conn.execute('''UPDATE funds SET fund_limit = $1, current_funds = $2 
                                WHERE name = 'General Fund';''', new_limit, new_funds)
                        # count the number of investors
                        investor_count = await conn.fetchrow('''SELECT COUNT(user_id) 
                                FROM bank_ledger WHERE type = 'investment';''')
                        # calculate how much each investor will receive
                        investor_cut = (refund * .25) / investor_count['count']
                        # count the number of premium members
                        premium_count = await conn.fetchrow('''SELECT COUNT(user_id) 
                                FROM rbt_users WHERE premium_user = TRUE AND suspended = FALSE;''')
                        # calculate how much each premium user will receive
                        premium_cut = (refund * .25) / premium_count['count']
                        # count the number of recruiters who have sent more than 100 TGs this month
                        sender_count = await conn.fetchrow('''SELECT COUNT(user_id) 
                                FROM recruitment WHERE sent_this_month > 100;''')
                        # calculate sender cut
                        sender_cut = (refund * .25) / sender_count['count']
                        # count the number of registered members
                        member_count = await conn.fetchrow('''SELECT COUNT(user_id) 
                                FROM rbt_users WHERE suspended = FALSE;''')
                        # calculate the member cut
                        member_cut = (refund * .25) / member_count['count']
                        # credit premium group
                        await conn.execute('''UPDATE rbt_users SET funds = funds + $1 
                                WHERE premium_user = TRUE AND suspended = FALSE;''', premium_cut)
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
                WHERE type = 'investment';''')
                if investment_sum_raw['sum'] is None:
                    investment_sum = 0
                else:
                    investment_sum = investment_sum_raw['sum']
                # increase investments by 2% for investors
                await conn.execute('''UPDATE bank_ledger SET amount = amount * 1.02 WHERE type = 'investment';''')
                # increase investment fund by 2%
                await conn.execute(
                    '''UPDATE funds SET current_funds = current_funds * 1.02 WHERE name = 'Investment Fund';''')
                # pay 6% dividend to general fund
                await conn.execute(
                    '''UPDATE funds SET current_funds = current_funds + $1 WHERE name = 'General Fund';''',
                    (investment_sum * .06))
                # increase loan by interest rate
                await conn.execute('''UPDATE bank_ledger SET amount = amount * (1+(interest/100)) 
                WHERE type = 'loan';''')
                # LOANS DUE
                today = datetime.now()
                loans_due = await conn.fetch('''SELECT * FROM bank_ledger WHERE due_date < $1 AND type = 'loan';''',
                                             today)
                # for all the loans in due, reposes thaler or default
                for loan in loans_due:
                    amount = loan['amount']
                    borrower = loan['user_id']
                    borrower_snowflake = self.bot.get_user(borrower)
                    # fetch borrower information
                    borrower_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''', borrower)
                    # if the user does not have enough thaler in their funds, increase loan by 35%
                    if borrower_info['funds'] < amount:
                        await conn.execute('''UPDATE bank_ledger SET amount = amount * 1.35, due_date = $2 
                        WHERE account_id = $1;''', loan['account_id'], today + timedelta(days=14))
                        # create and send user a DM
                        await borrower_snowflake.send(f"This is your official notice from the Royal Bank of Thegye "
                                                      f"that you have defaulted on your loan account "
                                                      f"(ID: {loan['account_id']}. This loan has been increased by 35% "
                                                      f"in lieu of payment and will become due two weeks from today.")
                        continue
                    else:
                        # remove funds from user
                        await conn.execute('''UPDATE rbt_users SET funds = funds - $1 WHERE user_id = $2;''',
                                           amount, borrower)
                        # add funds to investment fund
                        await conn.execute('''UPDATE funds SET current_funds = current_funds + $1 
                        WHERE name = 'Investment Fund';''', amount)
                        # remove loan account
                        await conn.execute('''DELETE FROM bank_ledger WHERE account_id = $1;''', loan['account_id'])
                        # log action
                        await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                           borrower, 'bank', f"Loan account #{loan['account_id']} automatically "
                                                             f"repaid by {borrower_snowflake.name}#"
                                                             f"{borrower_snowflake.discriminator}.")
                        continue
                # payroll
                thegye = self.bot.get_guild(674259612580446230)
                official_role = thegye.get_role(674278988323225632)
                for official in official_role.members:
                    if datetime.now().weekday() <= 5:
                        await conn.execute('''UPDATE rbt_users SET funds = funds + 20 WHERE user_id = $1;''',
                                           official.id)
                        await conn.execute(
                            '''UPDATE funds SET current_funds = current_funds - 20 WHERE name = 'General Fund';''')
                        await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                           official.id, 'bank', f"Payroll {self.thaler}20.")
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
            # fetch all accounts
            investment = await conn.fetchrow('''SELECT * FROM bank_ledger 
            WHERE user_id = $1 AND type = 'investment';''', user.id)
            loan = await conn.fetchrow('''SELECT * FROM bank_ledger WHERE user_id = $1 AND type = 'loan';''', user.id)
            # fetch stocks and calculate worth
            ledger = await conn.fetch('''SELECT * FROM ledger WHERE user_id = $1;''',
                                      user.id)
            wallet_contents = await conn.fetchrow('''SELECT SUM(amount) FROM ledger WHERE user_id = $1;''',
                                                  user.id)
            if wallet_contents['sum'] is None:
                wallet_contents = 0
            else:
                wallet_contents = wallet_contents['sum']
            # calculate total stock value
            stock_value = 0
            for stock in ledger:
                # fetch stock info
                stock_info = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''',
                                                 stock['stock_id'])
                stock_value += stock['amount'] * float(stock_info['value'])
            total_value = round(stock_value + float(rbt_member['funds']), 2)
            # create embed
            rbtm_embed = discord.Embed(title=f"{user.nick}", description=f"Information about the Royal Bank of Thegye"
                                                                         f" member {user.name}#{user.discriminator}.",
                                       color=discord.Color.gold())
            rbtm_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
            rbtm_embed.add_field(name="Thaler", value=f"{self.thaler}{rbt_member['funds']:,.2f}")
            rbtm_embed.add_field(name="Membership", value=f"{user_type}")
            rbtm_embed.add_field(name=self.space, value=self.space)
            if investment is not None:
                rbtm_embed.add_field(name="Investment Account", value=f"{self.thaler}{investment['amount']:,.2f}")
                total_value += investment['amount']
            if loan is not None:
                rbtm_embed.add_field(name="Loan Account", value=f"{self.thaler}{loan['amount']:,.2f}")
                total_value -= loan['amount']
            rbtm_embed.add_field(name="Net Worth", value=f"{self.thaler}{total_value:,.2f}", inline=False)
            rbtm_embed.add_field(name="Wallet", value=f"{wallet_contents} shares out of {rbt_member['wallet']} shares")
            return await interaction.followup.send(embed=rbtm_embed)

    @rbt.command(name='directory', description="Displays all registered members of the Royal Bank of Thegye.")
    async def directory(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # define thegye
        thegye = self.bot.get_guild(674259612580446230)
        # establish connection
        conn = self.bot.pool
        # fetch all rbt members
        rbt_members = await conn.fetch('''SELECT * FROM rbt_users;''')
        # create dictionary
        member_dict = {}
        # calculate net worth
        for member in rbt_members:
            # fetch member ledger
            ledger = await conn.fetch('''SELECT * FROM ledger WHERE user_id = $1;''',
                                      member['user_id'])
            # fetch accounts
            investment = await conn.fetchrow('''SELECT * FROM bank_ledger 
            WHERE user_id = $1 AND type = 'investment';''', member['user_id'])
            loan = await conn.fetchrow('''SELECT * FROM bank_ledger 
            WHERE user_id = $1 AND type = 'loan';''', member['user_id'])
            # calculate total stock value
            stock_value = 0
            for stock in ledger:
                # fetch stock info
                stock_info = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''',
                                                 stock['stock_id'])
                stock_value += stock['amount'] * float(stock_info['value'])
            total_value = round(stock_value + float(member['funds']), 2)
            if investment is not None:
                total_value += float(investment['amount'])
            if loan is not None:
                total_value -= float(loan['amount'])
            member_dict.update({member['user_id']: round(total_value, 2)})
        # sort members by total value
        ranked_members = sorted(member_dict.items(), key=lambda x: x[1], reverse=True)
        # create string
        ranked_string = "Members are ranked by their net worth.\n\n"
        for ranked_member in ranked_members:
            this_string = f"{ranked_members.index(ranked_member) + 1}. <@{thegye.get_member(ranked_member[0]).id}>"
            this_string += f": {self.thaler}{ranked_member[1]:,.2f}\n"
            ranked_string += this_string
        # create and send embed
        directory_embed = discord.Embed(title="Royal Bank of Thegye Directory", description=ranked_string)
        directory_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
        await interaction.followup.send(embed=directory_embed)

    @rbt.command(name="wire", description="Sends funds from your account to another account.")
    @app_commands.describe(amount="The amount you wish to wire. Must be a whole number.",
                           recipient="The user you want to wire the funds to.")
    async def wire(self, interaction: discord.Interaction, recipient: discord.User,
                   amount: app_commands.Range[float, 0.01]):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # define user
        author = interaction.user
        # calculate fee
        tax = round(.005 * amount, 2)
        if tax < .01:
            tax = .01
        total = tax + amount
        # check if user is registered
        author_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''', author.id)
        if author_info is None:
            return await interaction.followup.send("You are not a registered member of the Royal Bank of Thegye.")
        # check if recipient is registered
        recipient_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''', recipient.id)
        if recipient_info is None:
            return await interaction.followup.send(f"{recipient.display_name} is not a"
                                                   f" registered member of the Royal Bank of Thegye.")
        # check if the sender has enough thaler
        if total > author_info['funds']:
            return await interaction.followup.send(f"You do not have {self.thaler}{amount:,.2f}")
        # otherwise, send funds
        await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''', amount, recipient.id)
        await conn.execute('''UPDATE rbt_users SET funds = funds - $1 WHERE user_id = $2;''', total, author.id)
        await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                           author.id, 'trade', f"Wired {self.thaler}{amount} to "
                                               f"{recipient.name}#{recipient.discriminator} (ID:{recipient.id})")
        await conn.execute('''UPDATE funds SET current_funds = current_funds + $1 WHERE name = 'General Fund';''', tax)
        await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                           recipient.id, 'trade', f"Received {self.thaler}{amount} from "
                                                  f"{author.name}#{author.discriminator} (ID:{author.id})")
        return await interaction.followup.send(f"You have successfully sent {self.thaler}{amount} to "
                                               f"{recipient.display_name}.")

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

    @rbt.command(name="signed_contracts", description="Displays all contracts a user has signed.")
    async def signed_contracts(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # ensure membership
        user_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''', user.id)
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the Royal Bank of Thegye.")
        # fetch all contracts where the user is a signatory
        contracts = await conn.fetch('''SELECT * FROM contracts WHERE $1 = ANY(signatories);''', user.id)
        # if they have signed no contracts, return
        if contracts is None:
            return await interaction.followup.send("You have not signed any contracts.")
        # make list
        contract_list = "You have signed the following contract(s): \n"
        for contract in contracts:
            contract_list += f"Contract ID: `{contract['contract_id']}` " \
                             f"\(signed `{contract['time'].strftime('%H:%M on %d/%m/%Y')}`)\n"
        # send list
        return await interaction.followup.send(content=contract_list)

    @rbt.command(name="fund_info", description="Displays information about a given fund.")
    @app_commands.describe(fund="The name of the fund.")
    async def fund_info(self, interaction: discord.Interaction,
                        fund: typing.Literal['General Fund', 'Investment Fund']):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # fetch fund
        fund = await conn.fetchrow('''SELECT * FROM funds WHERE name = $1;''', fund)
        # create embed
        fund_embed = discord.Embed(title=f"{fund['name']}", description=f"Information about the {fund['name']}.")
        fund_embed.add_field(name="Current Funds", value=f"{self.thaler}{fund['current_funds']:,.2f}")
        fund_embed.add_field(name="Fund Limit", value=f"{self.thaler}{fund['fund_limit']:,.2f}")
        fund_embed.add_field(name="\u200b", value="\u200b")
        await interaction.followup.send(embed=fund_embed)

    @rbt.command(name="open_account",
                 description="Opens an account with the bank, be that an investment or a loan account.")
    @app_commands.describe(account_type="The type of account you want to open.",
                           amount="The amount of thaler you wish to invest or borrow.")
    async def open_account(self, interaction: discord.Interaction, account_type: typing.Literal['investment', 'loan'],
                           amount: float):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # round amount
        amount = round(amount, 2)
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # fetch user info
        user_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''', user.id)
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the Royal Bank of Thegye.")
        # ensure the user does not already have an account if they are opening a loan account
        if account_type == "loan":
            # ensure the amount is over 1000
            if amount < 1000:
                return await interaction.followup.send(f"The Royal Bank of Thegye does not issue loans "
                                                       f"below {self.thaler}1,000.")
            loan = await conn.fetchrow('''SELECT * FROM bank_ledger WHERE user_id = $1 AND type = 'loan';''',
                                       user.id)
            if loan is not None:
                return await interaction.followup.send(f"You already have an open loan. To view this loan account, "
                                                       f"use `/rbt view_account loan`."
                                                       f"To deposit, use `/rbt manage_account`.")
            # check if the investment fund has enough funds
            investment_fund = await conn.fetchrow('''SELECT * FROM funds WHERE name = 'Investment Fund';''')
            if float(investment_fund['current_funds']) < amount:
                return await interaction.followup.send(f"The Investment Fund does not have enough available funds to "
                                                       f"fill that request.")
            message = await interaction.followup.send(content="Use the dropdown menu below to choose loan type:")
            await message.edit(view=LoanView(amount=amount, user=user, message=message))
        # if the type is investment, ensure the user has the amount to invest
        if account_type == "investment":
            if amount > user_info['funds']:
                return await interaction.followup.send(f"You do not have {self.thaler}{amount:,.2f}.")
            # ensure they dont already have an account
            investment_account = await conn.fetchrow('''SELECT * FROM bank_ledger WHERE user_id = $1 
            AND type = 'investment';''', user.id)
            if investment_account is not None:
                return await interaction.followup.send(f"You already have an investment account. To view the account "
                                                       f"use `/rbt view_account investment`. "
                                                       f"To deposit or withdraw, use `/rbt manage_account`.")
            # add funds to investment fund
            await conn.execute('''UPDATE funds SET current_funds = current_funds + $1 
            WHERE name = 'Investment Fund';''', amount)
            # create loan account
            await conn.execute('''INSERT INTO bank_ledger VALUES($1,$2,$3,$4);''',
                               user.id, interaction.id, amount, 'investment')
            # credit to user account and log
            await conn.execute('''UPDATE rbt_users SET funds = funds - $1 WHERE user_id = $2;''',
                               amount, user.id)
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'bank', f"Opened a new investment account (ID: {interaction.id}) "
                                                f"with {self.thaler}{amount:,.2f}.")
            return await interaction.followup.send(f"You have successfully opened an investment account (ID: "
                                                   f"{interaction.id}) with {self.thaler}{amount:,.2f}.")

    @rbt.command(name="manage_account", description="Manages an existing loan or investment account.")
    @app_commands.describe(account_type="The type of account you want to manage.",
                           action="The type of action you want to do. Withdrawing from a "
                                  "loan account will increase the loan and depositing will decrease it.")
    async def manage_account(self, interaction: discord.Interaction, account_type: typing.Literal['investment', 'loan'],
                             action: typing.Literal['withdraw', 'deposit'], amount: float):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # round amount
        amount = round(amount, 2)
        # ensure membership
        user_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                        user.id)
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the Royal Bank of Thegye.")
        # fetch investment fund info
        investment_fund = await conn.fetchrow('''SELECT * FROM funds WHERE name = 'Investment Fund';''')
        # loan account management
        # ensure the user does not already have an account if they are opening a loan account
        if account_type == "loan":
            loan = await conn.fetchrow('''SELECT * FROM bank_ledger WHERE user_id = $1 AND type = 'loan';''',
                                       user.id)
            if loan is None:
                return await interaction.followup.send(f"You do not have an open loan account. Use "
                                                       f"`/rbt open_account` to open a new loan account.")
            # if the action is withdraw
            if action == "withdraw":
                # check if the investment fund has enough funds
                if investment_fund['current_funds'] < amount:
                    return await interaction.followup.send(
                        f"The Investment Fund does not have enough available funds to "
                        f"fill that request.")
                # remove funds from investment fund
                await conn.execute('''UPDATE funds SET current_funds = current_funds - $1 
                WHERE name = 'Investment Fund';''', amount)
                # update loan account
                await conn.execute('''UPDATE bank_ledger SET amount = amount + $1 
                WHERE user_id = $2 AND type = 'loan';''', amount, user.id)
                # credit to user account and log
                await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                                   amount, user.id)
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'bank', f"Borrow {self.thaler}{amount:,.2f} from loan account "
                                                    f"(ID: {loan['account_id']}).")
                return await interaction.followup.send(f"You have successfully borrowed an additional"
                                                       f" {self.thaler}{amount:,.2f} from your existing loan account "
                                                       f"(ID:{interaction.id}).")
            # if action is deposit
            if action == "deposit":
                # ensure user has enough funds
                if user_info['funds'] < amount:
                    return await interaction.followup.send("You do not have enough thaler for that.")
                # if the user is depositing more than the loan amount, auto-adjust
                if amount > loan['amount']:
                    amount = loan['amount']
                # remove funds from user
                await conn.execute('''UPDATE rbt_users SET funds = funds - $1 WHERE user_id = $2;''',
                                   amount, user.id)
                # update bank ledger
                await conn.execute('''UPDATE bank_ledger SET amount = amount - $1 
                WHERE user_id = $2 AND type = 'loan';''', amount, user.id)
                # update investment fund
                await conn.execute('''UPDATE funds SET current_funds = current_funds + $1 
                WHERE name = 'Investment Fund';''', amount)
                # update log
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'bank', f"Repaid {self.thaler}{amount:,.2f} of loan account "
                                                    f"(ID: {loan['account_id']}).")
                # remove any accounts with 0 amount
                await conn.execute('''DELETE FROM bank_ledger WHERE round(amount::numeric,2) <= 0;''')
                # send message
                return await interaction.followup.send(f"You have successfully repaid {self.thaler}{amount:,.2f} "
                                                       f"of loan account (ID: {loan['account_id']}).")
        if account_type == "investment":
            # ensure they have an account
            investment = await conn.fetchrow('''SELECT * FROM bank_ledger WHERE user_id = $1 
            AND type = 'investment';''', user.id)
            if investment is None:
                return await interaction.followup.send("You do not have an active investment account. "
                                                       "To open a new account, use `/rbt open_account investment`.")
            # if action is withdraw
            if action == "withdraw":
                # check the account for sufficient funds
                if amount > investment['amount']:
                    return await interaction.followup.send("You do not have enough thaler in "
                                                           "your investment account for that.")
                if investment_fund['current_funds'] < amount:
                    return await interaction.followup.send(
                        f"The Investment Fund does not have enough available funds to fill that request.")
                # add funds to user
                await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                                   amount, user.id)
                # update bank ledger
                await conn.execute('''UPDATE bank_ledger SET amount = amount - $1 
                WHERE user_id = $2 AND type = 'investment';''', amount, user.id)
                # update investment fund
                await conn.execute('''UPDATE funds SET current_funds = current_funds - $1 
                WHERE name = 'Investment Fund';''', amount)
                # update log
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'bank', f"Withdrew {self.thaler}{amount:,.2f} from investment account "
                                                    f"(ID: {investment['account_id']}).")
                # remove any accounts with 0 amount
                await conn.execute('''DELETE FROM bank_ledger WHERE round(amount::numeric,2) <= 0;''')
                # send message
                return await interaction.followup.send(f"You have successfully withdrawn {self.thaler}{amount:,.2f} "
                                                       f"from investment account (ID: {investment['account_id']}).")
            # if action is deposit
            if action == "deposit":
                # ensure user has enough funds
                if user_info['funds'] < amount:
                    return await interaction.followup.send("You do not have enough thaler for that.")
                # remove funds from user
                await conn.execute('''UPDATE rbt_users SET funds = funds - $1 WHERE user_id = $2;''',
                                   amount, user.id)
                # update bank ledger
                await conn.execute('''UPDATE bank_ledger SET amount = amount + $1 
                WHERE user_id = $2 AND type = 'investment';''', amount, user.id)
                # update investment fund
                await conn.execute('''UPDATE funds SET current_funds = current_funds + $1 
                WHERE name = 'Investment Fund';''', amount)
                # update log
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'bank', f"Deposited {self.thaler}{amount:,.2f} into investment account "
                                                    f"(ID: {investment['account_id']}).")
                # remove any accounts with 0 amount
                await conn.execute('''DELETE FROM bank_ledger WHERE ROUND(amount::numeric,2) <= 0;''')
                # send message
                return await interaction.followup.send(f"You have successfully deposited {self.thaler}{amount:,.2f} "
                                                       f"into investment account (ID: {investment['account_id']}).")

    @rbt.command(name="view_account", description="Displays information about one of your associated accounts.")
    @app_commands.describe(account_type="The type of account you want to view.")
    async def view_account(self, interaction: discord.Interaction, account_type: typing.Literal['investment', 'loan']):
        # defer interaction
        await interaction.response.defer(thinking=False)
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # ensure they have the type of account they've requested
        account = await conn.fetchrow('''SELECT * FROM bank_ledger WHERE user_id = $1 and type = $2;''',
                                      user.id, account_type)
        if account is None:
            return await interaction.followup.send(f"You do not have an account of that type.")
        # create embed
        account_embed = discord.Embed(title=f"{user.display_name}'s {account_type.title()} Account",
                                      description=f"{account_type.title()} account for "
                                                  f"member {user.name}#{user.discriminator}.")
        account_embed.set_thumbnail(url=self.logo)
        account_embed.add_field(name="Type", value=f"{account_type.title()}", inline=False)
        account_embed.add_field(name="Amount", value=f"{self.thaler}{account['amount']:,.2f}")
        account_embed.add_field(name="Interest Rate", value=f"{account['interest']:.2f}% per day")
        account_embed.add_field(name=self.space, value=self.space)
        return await interaction.followup.send(embed=account_embed)

    @rbt.command(name='log', description="Sends a log of all trades, buys, sells, signed contracts, "
                                         "and marketplace transactions.")
    @app_commands.describe(log_type="Input one of the choices to view your log.",
                           filter="Filters out one type of log when viewing all.")
    async def log(self, interaction: discord.Interaction,
                  log_type: typing.Literal['exchange', 'casino', 'trade', 'contract', 'market', 'payroll', 'all'],
                  filter: typing.Literal['exchange', 'casino', 'trade', 'contract', 'market', 'payroll'] = None):
        # defer response
        await interaction.response.defer(thinking=True, ephemeral=True)
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
        elif filter is not None:
            logs = await conn.fetch('''SELECT * FROM rbt_user_log WHERE user_id = $1 AND action != $2
                                    ORDER BY timestamp DESC;''', user.id, filter)
        else:
            logs = await conn.fetch('''SELECT * FROM rbt_user_log WHERE user_id = $1
                        ORDER BY timestamp DESC;''', user.id)
        with open(rf"{user.id}_exchange_log.txt", "w+", encoding="UTF-8") as exchange_log:
            exchange_log.write("Note that transactions are ordered by most recent.\n")
            for log in logs:
                exchange_log.write(f"[{log['timestamp']}] {log['description']}\n")
        await interaction.followup.send(file=discord.File(fp=f"{user.id}_exchange_log.txt",
                                                          filename=f"{user.id}_exchange_log.txt"),
                                        ephemeral=True)
        return

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
                    value = float(stock['value'])
                    # change chance
                    change_chance = randint(1, 100)
                    # calculate trending course if up
                    if stock['trending'] == "up":
                        if change_chance <= 25 + (5 * stock['risk']):
                            trending = "down"
                        else:
                            trending = "up"
                    # calculate trending course if down
                    elif stock['trending'] == "down":
                        if change_chance <= 25 + (5 * stock['risk']):
                            trending = "up"
                        else:
                            trending = "down"
                    # calculation: new_value = value + ((percentage increase + outstanding over issued / 10) * value)
                    value_roll = uniform(0, 2 + stock['risk'])
                    # if the trend is up, increase stock based on risk
                    if trending == "up":
                        value += round(value_roll + (stock['outstanding'] / stock['issued']), 2)
                    else:
                        value -= round(value_roll, 2)
                        # if the value drops below the floor, set it to be 5 - risk
                    floor = 15 - uniform(0, stock['risk'])
                    if value < floor:
                        value = floor
                    # if the outstanding shares is between 0 and 500 shares away from the total issued shares,
                    # increase by half and dilute by (5 * risk to 10 * risk)% capped at 23%
                    if stock['issued'] - stock['outstanding'] < randint(0, 500):
                        # royal bonds are immune to automatic dilution
                        if stock['stock_id'] != 1:
                            new_shares = stock['issued'] / 5
                            dilution = round(uniform(5 * stock['risk'], 10 * stock['risk']), 2)
                            value = round(value * (clip(dilution, 0, 23) / 100), 2)
                            self.announcement += f"{stock['name']} has been diluted. Issued shares have increased to " \
                                                 f"{new_shares:,.0f}, and the diluted value is now " \
                                                 f"{self.thaler}{value:,.2f} per share.\n"
                    # update stock information
                    await conn.execute('''UPDATE stocks SET value = ROUND($1,2), issued = issued + $2, trending = $3, 
                    change = ($1/value)-1 WHERE stock_id = $4;''', value, new_shares, trending, stock['stock_id'])
                # calculate value of stocks
                stock_sum = await conn.fetchrow('''SELECT SUM(value) FROM stocks;''')
                # fetch stock count
                stock_count = await conn.fetchrow('''SELECT COUNT(*) FROM stocks;''')
                # fetch crash
                crash = await conn.fetchrow('''SELECT * FROM info WHERE name = 'rbt_crash';''')
                self.crash = crash['bool']
                # calculate market crash chance
                if self.crash is True:
                    recovery_chance = uniform(1, 20)
                    if recovery_chance <= 8:
                        self.crash = False
                        self.announcement += "The Royal Bank of Thegye announces the end of the **Exchange Crash**.\n" \
                                             "Stock prices have recovered by 25%.\n "
                        await conn.execute('''UPDATE stocks SET value = ROUND((value*1.25)::numeric, 2), 
                        change = ROUND(value*1.25::numeric-value::numeric, 2) - 1;''')
                    else:
                        await conn.execute('''UPDATE stocks SET value = ROUND((value*.25)::numeric, 2), 
                        change = ROUND(value*.25::numeric-value::numeric, 2) - 1;''')
                        self.announcement += "The Royal Bank of Thegye is observing an **Exchange Crash**. " \
                                             "All stock values are decreased by 75%.\n"
                else:
                    crash_chance = uniform(1, 100)
                    if stock_sum['sum'] / stock_count['count'] > 15 + stock_count['count']:
                        crash_chance += float(stock_sum['sum']) / int(stock_count['count'])
                    if crash_chance <= 1:
                        if self.crash is False:
                            await conn.execute('''UPDATE stocks 
                                SET value = round((value * .25)::numeric, 2), trending = 'down', 
                                change = ROUND(value*.25::numeric-value::numeric, 2) - 1;''')
                            self.announcement += "The Royal Bank of Thegye has observed an **Exchange Crash**. " \
                                                 "All stock values are decreased by 75% and begun trending down.\n "
                            self.crash = True
                # update stocks' value tracker
                await conn.execute('''INSERT INTO exchange_log(stock_id, value, trend)
                SELECT stock_id, value, trending FROM stocks;''')
                # unpin old message
                old_message = await conn.fetchrow('''SELECT * FROM info WHERE name = 'rbt_pinned_message';''')
                old_message = await bankchannel.fetch_message(old_message['bigint'])
                await old_message.unpin()
                # announce
                new_announcement = await bankchannel.send(content=self.announcement)
                await new_announcement.pin()
                await conn.execute('''UPDATE info SET bigint = $1 WHERE name = 'rbt_pinned_message';''',
                                   new_announcement.id)
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
        bankchannel = ctx
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
            value = float(stock['value'])
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
            # calculation: new_value = value + ((percentage increase + outstanding over issued / 10) * value)
            value_roll = uniform(1, 3 * stock['risk'])
            # if the trend is up, increase stock based on risk
            if trending == "up":
                value += round(value_roll + (stock['outstanding'] / stock['issued']), 2)
            else:
                value -= round(value_roll, 2)
                # if the value drops below the floor, set it to be 5 - risk
            if value < (5 - stock['risk']):
                value = 5 - stock['risk']
            # if the outstanding shares is between 0 and 500 shares away from the total issued shares,
            # increase by half and dilute by (5 * risk to 10 * risk)% capped at 23%
            if stock['issued'] - stock['outstanding'] < randint(0, 500):
                # royal bonds are immune to automatic dilution
                if stock['stock_id'] != 1:
                    new_shares = stock['issued'] / 5
                    dilution = round(uniform(5 * stock['risk'], 10 * stock['risk']), 2)
                    value = round(value * (clip(dilution, 0, 23) / 100), 2)
                    self.announcement += f"{stock['name']} has been diluted. Issued shares have increased to " \
                                         f"{new_shares}, and the diluted value is now " \
                                         f"{self.thaler}{value} per share.\n"
            # update stock information
            await conn.execute('''UPDATE stocks SET value = ROUND($1,2), issued = issued + $2, trending = $3, 
            change = ($1/value)-1 WHERE stock_id = $4;''', value, new_shares, trending, stock['stock_id'])
        # calculate value of stocks
        stock_sum = await conn.fetchrow('''SELECT SUM(value) FROM stocks;''')
        # fetch stock count
        stock_count = await conn.fetchrow('''SELECT COUNT(*) FROM stocks;''')
        # fetch crash
        crash = await conn.fetchrow('''SELECT * FROM info WHERE name = 'rbt_crash';''')
        self.crash = crash['bool']
        # calculate market crash chance
        if self.crash is True:
            recovery_chance = uniform(1, 20)
            if recovery_chance <= 8:
                self.crash = False
                self.announcement += "The Royal Bank of Thegye announces the end of the **Exchange Crash**.\n" \
                                     "Stock prices have recovered by 25%.\n "
                await conn.execute('''UPDATE stocks SET value = ROUND((value*1.25)::numeric, 2), 
                change = ROUND(value*1.25::numeric-value::numeric, 2) - 1;''')
            else:
                await conn.execute('''UPDATE stocks SET value = ROUND((value*.25)::numeric, 2), 
                change = ROUND(value*.25::numeric-value::numeric, 2) - 1;''')
                self.announcement += "The Royal Bank of Thegye is observing an **Exchange Crash**. " \
                                     "All stock values are decreased by 75%.\n "
        crash_chance = uniform(1, 100)
        if stock_sum['sum'] / stock_count['count'] > 10 * stock_count['count']:
            crash_chance += float(stock_sum['sum']) / int(stock_count['count'])
        if crash_chance <= 1:
            if self.crash is False:
                await conn.execute('''UPDATE stocks 
                    SET value = round((value * .25)::numeric, 2), trending = 'down', 
                    change = ROUND(value*.25::numeric-value::numeric, 2) - 1;''')
                self.announcement += "The Royal Bank of Thegye has observed an **Exchange Crash**. " \
                                     "All stock values are decreased by 75% and begun trending down.\n "
                self.crash = True
        # update stocks' value tracker
        await conn.execute('''INSERT INTO exchange_log(stock_id, value, trend)
        SELECT stock_id, value, trending FROM stocks;''')
        # unpin old message
        old_message = await conn.fetchrow('''SELECT * FROM info WHERE name = 'rbt_pinned_message';''')
        old_message = await bankchannel.fetch_message(int(old_message['bigint']))
        await old_message.unpin()
        # announce
        new_announcement = await bankchannel.send(content=self.announcement)
        await new_announcement.pin()
        await conn.execute('''UPDATE info SET bigint = $1 WHERE name = 'rbt_pinned_message';''',
                           str(new_announcement.id))
        self.announcement = \
            "The Royal Exchange of Thegye has updated. Below is a summary of any important changes:\n"

    @commands.command()
    @commands.is_owner()
    async def force_bank_update(self, ctx):
        try:
            # establish connection
            conn = self.bot.pool
            # GENERAL FUND CHECKS
            # check general fund for minting/refund
            general_fund = await conn.fetchrow('''SELECT * FROM funds WHERE name = 'General Fund';''')
            current_fund = float(general_fund['current_funds'])
            fund_limit = float(general_fund['fund_limit'])
            # if the general fund is near/overdrawn
            if current_fund <= (.02 * fund_limit):
                # set new fund to 150% of old fund
                new_limit = fund_limit * 1.5
                additional_funds = fund_limit * .5
                # ADD MARKET INCREASES/DECREASES HERE
                # update funds
                await conn.execute('''UPDATE funds SET fund_limit = $1, current_funds = current_funds + $2 
                        WHERE name = 'General Fund';''', new_limit, additional_funds)
            # if the general fund is overfunded
            if current_fund > fund_limit:
                # ensure the general fund is more than 500,000 thaler
                if fund_limit > 500000:
                    # set the new fund limit to 50%
                    new_limit = fund_limit * .5
                    # calculate refund and new current funds
                    new_funds = fund_limit * .25
                    refund = current_fund - fund_limit
                    await conn.execute('''UPDATE funds SET fund_limit = $1, current_funds = $2 
                            WHERE name = 'General Fund';''', new_limit, new_funds)
                    # count the number of investors
                    investor_count = await conn.fetchrow('''SELECT COUNT(user_id) 
                            FROM bank_ledger WHERE type = 'investment';''')
                    # calculate how much each investor will receive
                    investor_cut = (refund * .25) / investor_count['count']
                    # count the number of premium members
                    premium_count = await conn.fetchrow('''SELECT COUNT(user_id) 
                            FROM rbt_users WHERE premium_user = TRUE AND suspended = FALSE;''')
                    # calculate how much each premium user will receive
                    premium_cut = (refund * .25) / premium_count['count']
                    # count the number of recruiters who have sent more than 100 TGs this month
                    sender_count = await conn.fetchrow('''SELECT COUNT(user_id) 
                            FROM recruitment WHERE sent_this_month > 100;''')
                    # calculate sender cut
                    sender_cut = (refund * .25) / sender_count['count']
                    # count the number of registered members
                    member_count = await conn.fetchrow('''SELECT COUNT(user_id) 
                            FROM rbt_users WHERE suspended = FALSE;''')
                    # calculate the member cut
                    member_cut = (refund * .25) / member_count['count']
                    # credit premium group
                    await conn.execute('''UPDATE rbt_users SET funds = funds + $1 
                            WHERE premium_user = TRUE AND suspended = FALSE;''', premium_cut)
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
            WHERE type = 'investment';''')
            if investment_sum_raw['sum'] is None:
                investment_sum = 0
            else:
                investment_sum = investment_sum_raw['sum']
            # increase investments by 2% for investors
            await conn.execute('''UPDATE bank_ledger SET amount = amount * 1.02 WHERE type = 'investment';''')
            # increase investment fund by 2%
            await conn.execute(
                '''UPDATE funds SET current_funds = current_funds * 1.02 WHERE name = 'Investment Fund';''')
            # pay 6% dividend to general fund
            await conn.execute(
                '''UPDATE funds SET current_funds = current_funds + $1 WHERE name = 'General Fund';''',
                (investment_sum * .06))
            # increase loan by interest rate
            await conn.execute('''UPDATE bank_ledger SET amount = amount * (1+(interest/100)) 
            WHERE type = 'loan';''')
            # LOANS DUE
            today = datetime.now()
            loans_due = await conn.fetch('''SELECT * FROM bank_ledger WHERE due_date < $1 AND type = 'loan';''',
                                         today)
            # for all the loans in due, reposes thaler or default
            for loan in loans_due:
                amount = loan['amount']
                borrower = loan['user_id']
                borrower_snowflake = self.bot.get_user(borrower)
                # fetch borrower information
                borrower_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''', borrower)
                # if the user does not have enough thaler in their funds, increase loan by 35%
                if borrower_info['funds'] < amount:
                    await conn.execute('''UPDATE bank_ledger SET amount = amount * 1.35, due_date = $2 
                    WHERE account_id = $1;''', loan['account_id'], today + timedelta(days=14))
                    # create and send user a DM
                    await borrower_snowflake.send(f"This is your official notice from the Royal Bank of Thegye "
                                                  f"that you have defaulted on your loan account "
                                                  f"(ID: {loan['account_id']}. This loan has been increased by 35% "
                                                  f"in lieu of payment and will become due two weeks from today.")
                    continue
                else:
                    # remove funds from user
                    await conn.execute('''UPDATE rbt_users SET funds = funds - $1 WHERE user_id = $2;''',
                                       amount, borrower)
                    # add funds to investment fund
                    await conn.execute('''UPDATE funds SET current_funds = current_funds + $1 
                    WHERE name = 'Investment Fund';''', amount)
                    # remove loan account
                    await conn.execute('''DELETE FROM bank_ledger WHERE account_id = $1;''', loan['account_id'])
                    # log action
                    await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                       borrower, 'bank', f"Loan account #{loan['account_id']} automatically "
                                                         f"repaid by {borrower_snowflake.name}#"
                                                         f"{borrower_snowflake.discriminator}.")
                    continue
            # payroll
            thegye = self.bot.get_guild(674259612580446230)
            official_role = thegye.get_role(674278988323225632)
            for official in official_role.members:
                if datetime.now().weekday() <= 5:
                    await conn.execute('''UPDATE rbt_users SET funds = funds + 20 WHERE user_id = $1;''',
                                       official.id)
                    await conn.execute(
                        '''UPDATE funds SET current_funds = current_funds - 20 WHERE name = 'General Fund';''')
                    await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                       official.id, 'bank', f"Payroll {self.thaler}20.")
            await ctx.send("Royal Bank of Thegye updated.")
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

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
            stock_embed.add_field(name="Outstanding Shares", value=f"{stock['outstanding']:,}")
            stock_embed.add_field(name="Issued Shares", value=f"{stock['issued']:,}")
            stock_embed.add_field(name="\u200b", value="\u200b")
            stock_embed.add_field(name="Trend", value=f"{stock['trending'].title()} ({stock['change'] * 100:.2f}%)")
            stock_embed.add_field(name="Risk Type", value=f"{risk}")
            stock_embed.add_field(name="\u200b", value="\u200b")
            return await interaction.followup.send(embed=stock_embed)

    @exchange.command(description="Purchases a specified amount of a stock's shares.", name="buy")
    @app_commands.describe(stock_id="The name or ID of the stock",
                           amount="A whole number amount. Also accepts \"max\".")
    async def buy(self, interaction: discord.Interaction, stock_id: str, amount: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # fetches user information
        user = interaction.user
        # fetches RBT member information
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)
        if rbt_member is None:
            return await interaction.followup.send(f"You are not a registered member of the Royal Bank of Thegye.")
        # if the amount isn't max, then set the amount = a number
        try:
            amount = int(amount)
            # if the amount is less than 0
            if amount <= 0:
                return await interaction.followup.send(f"Positive whole numbers only!")
        except ValueError:
            if amount.lower() != "max":
                return await interaction.followup.send(f"`{amount}` is not a valid argument for this command.")
        # fetches stock information
        stock = await conn.fetchrow('''SELECT * FROM stocks WHERE lower(name) = $1;''', stock_id.lower())
        # if stock does not exist, return message
        if stock is None:
            try:
                stock = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''', int(stock_id))
            except ValueError:
                return await interaction.followup.send(
                    f"``{stock_id}`` does not exist on the Exchange.")  # if the amount is maximum, calculate how much the user can purchase
        if type(amount) == str:
            if amount.lower() != "max":
                return await interaction.followup.send(f"`{amount}` is not a valid argument for this command.")
            base_price = round(float(stock['value']))
            tax = round(base_price * .005, 2)
            if tax < .01:
                tax = .01
            sub_total = round(base_price + tax, 2)
            amount = math.floor(rbt_member['funds'] / sub_total)
            # if the user cant afford any
            if amount < 1:
                return await interaction.followup.send(f"You cannot afford any shares of {stock['name']}.")
            transaction = round(amount * sub_total, 2)
        else:
            # define transaction cost
            base_price = round(float(stock['value']) * amount, 2)
            tax = round(base_price * .005, 2)
            if tax < .01:
                tax = .01
            transaction = round(base_price + tax, 2)
        # check the user's wallet
        wallet_contents = await conn.fetchrow('''SELECT sum(amount) FROM ledger WHERE user_id = $1;''', user.id)
        if wallet_contents['sum'] is None:
            wallet_contents = 0
        else:
            wallet_contents = wallet_contents['sum']
        if wallet_contents + amount > rbt_member['wallet']:
            if amount.lower() == "max":
                amount = rbt_member - wallet_contents
            else:
                return await interaction.followup.send(f"Your wallet (size: {rbt_member['wallet']:,}) "
                                                       f"does not have enough room to buy {amount:,} "
                                                       f"shares of {stock['name']}.")
        # if the stock would become overdrawn, notify user
        if amount + stock['outstanding'] > stock['issued']:
            return await interaction.followup.send(f"Purchasing {amount:,} shares of {stock['name']} would cause it to "
                                                   f"be overdrawn. Either purchase an appropriate number of issued "
                                                   f"shares or notify a Director to increase the number of shares of "
                                                   f"this company.")
        # check for sufficient funds and return if not
        if transaction > rbt_member['funds']:
            return await interaction.followup.send(f"You do not have enough funds to purchase that amount of shares.\n"
                                                   f"{amount:,} shares of **{stock['name']}** cost "
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
                f"You have successfully purchased {amount:,} shares of {stock['name']} for "
                f"{self.thaler}{transaction:,.2f} at {self.thaler}{float(stock['value']):,.2f} per share.\n"
                f"{self.thaler}{stock['value']:,.2f} * {amount} + {self.thaler}{tax:,.2f} (transaction fee) = "
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
            try:
                amount = int(amount)
            except ValueError:
                return await interaction.followup.send(f"The command only accepts "
                                                       f"whole numbers and \"all\" as arguments.")
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
        tax = round(base_price * .005, 2)
        if tax < .01:
            tax = .01
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
        # reduce outstanding shares
        await conn.execute('''UPDATE stocks SET outstanding = outstanding - $1 WHERE stock_id = $2;''',
                           amount, stock['stock_id'])
        # log sale
        await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                           user.id, 'exchange', f'Sold {amount} {stock["name"]} (id: {stock["stock_id"]}) @ '
                                                f'{self.thaler}{stock["value"]} for {self.thaler}{transaction}.')
        return await interaction.followup.send(f"You have successfully sold {amount} shares of {stock['name']} for "
                                               f"{self.thaler}{transaction:,.2f} at "
                                               f"{self.thaler}{float(stock['value'])} per share.\n"
                                               f"{self.thaler}{float(stock['value']):,.2f} * {amount} - "
                                               f"{self.thaler}{tax:,.2f} (transaction fee) = "
                                               f"{self.thaler}{transaction:,.2f}")

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
        return await interaction.followup.send(f"You have successfully sent {amount} shares of {stock['name']} to "
                                               f"{recipient.name}#{recipient.discriminator}.")

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
                                            description=f"Portfolio information of Royal Bank of Thegye member "
                                                        f"{user.name}#{user.discriminator}.")
            portfolio_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
            portfolio_embed.add_field(name="Current Thaler", value=f"{self.thaler}{rbt_member['funds']:,.2f}")
            # fetches all accounts
            investment = await conn.fetchrow('''SELECT * FROM bank_ledger 
            WHERE user_id = $1 AND type = 'investment';''', user.id)
            loan = await conn.fetchrow('''SELECT * FROM bank_ledger 
            WHERE user_id = $1 AND type = 'loan';''', user.id)
            # fetch all ledger information
            ledger_info = await conn.fetch('''SELECT * FROM ledger WHERE user_id = $1 ORDER BY stock_id ASC;''',
                                           user.id)
            ledger_string = ""
            stock_value = 0
            for shares in ledger_info:
                stock = await conn.fetchrow('''SELECT * FROM stocks WHERE stock_id = $1;''', shares['stock_id'])
                risk = ""
                if stock['risk'] == 1:
                    risk = "S"
                if stock['risk'] == 2:
                    risk = "M"
                if stock['risk'] == 3:
                    risk = "V"
                this_string = f"{shares['name']} (#{shares['stock_id']}, {risk}): " \
                              f"{shares['amount']} @ {self.thaler}{stock['value']:,.2f}"
                if stock['trending'] == "up":
                    this_string += " :chart_with_upwards_trend: "
                else:
                    this_string += " :chart_with_downwards_trend: "
                if stock['change'] > 0:
                    this_string += "+"
                this_string += f"{(stock['change'] * 100):.2f}%\n" \
                               f"> Sale value: {self.thaler}" \
                               f"{round(float(shares['amount']) * float(stock['value']), 2):,.2f}\n"
                ledger_string += this_string
                stock_value += float(shares['amount']) * float(stock['value'])
            total_value = float(rbt_member['funds']) + float(stock_value)
            if investment is not None:
                total_value += float(investment['amount'])
            if loan is not None:
                total_value -= float(loan['amount'])
            portfolio_embed.add_field(name="Stock Value", value=f"{self.thaler}{stock_value:,.2f}")
            portfolio_embed.add_field(name="Net Worth",
                                      value=f"{self.thaler}"
                                            f"{round(total_value, 2):,.2f}")
            portfolio_embed.add_field(name=f"Stocks and Shares", value=ledger_string)
            await interaction.followup.send(embed=portfolio_embed)

    @exchange.command(name="graph_value", description="Displays a graph of a stock's price.")
    @app_commands.describe(stock_id="Input the name or ID of the stock.",
                           start_date="Input a valid date in DD/MM/YYYY format. "
                                      "Also accepts \"today\", \"forever\", \"week\", and \"month\".",
                           end_date="Input a valid date in DD/MM/YYYY format. If left blank, defaults to today.")
    async def graph_value(self, interaction: discord.Interaction, stock_id: str,
                          start_date: str, end_date: str = None):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # fetches stock information
        stock = await conn.fetchrow('''SELECT * FROM stocks WHERE lower(name) = $1;''', stock_id.lower())
        # if the graph should be the average over time, graph
        if stock_id.lower() == "average":
            stock_id = "average"
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
        if not stock_data:
            return await interaction.followup.send(f"Unfortunately, I cannot find any data between"
                                                   f"`{start_date.date().strftime('%d/%m/%Y')}` and "
                                                   f"`{end_date.date().strftime('%d/%m/%Y')}`.")
        stock_prices = [s['value'] for s in stock_data]
        dates = [d['timestamp'] for d in stock_data]
        fig, ax = plt.subplots()
        ax.plot(dates, stock_prices)
        ax.xaxis.set_major_locator(DayLocator(interval=1))
        ax.xaxis.set_major_formatter(DateFormatter("%d/%m/%y"))
        fig.autofmt_xdate()
        days = (end_date - start_date).days
        if days >= 2:
            plt.grid(True, which="major")
            if days > 10:
                ax.xaxis.set_major_locator(DayLocator(interval=3))
            elif days > 30:
                ax.xaxis.set_major_locator(DayLocator(interval=10))
            elif days > 90:
                ax.xaxis.set_major_locator(DayLocator(interval=30))
            elif days > 180:
                ax.xaxis.set_major_locator(DayLocator(interval=60))
            elif days > 360:
                ax.xaxis.set_major_locator(YearLocator(month=start_date.month, day=start_date.day))
        else:
            ax.xaxis.set_minor_locator(HourLocator(interval=1))
            plt.grid(True, which="major")
            plt.grid(True, which="minor")
        plt.title(f"{stock['name']} (ID: {stock['stock_id']})")
        plt.ylabel("Value")
        plt.xlabel("Time")
        plt.savefig(r"C:\Users\jaedo\OneDrive\Pictures\graph.png")
        return await interaction.followup.send(file=discord.File(fp=r"C:\Users\jaedo\OneDrive\Pictures\graph.png",
                                                                 filename=f"Graph of {stock['name']} share price.png",
                                                                 description=f"A graph representing the share prices of"
                                                                             f" {stock['name']}"))

    @exchange.command(name="graph_hourly_value", description="Displays a graph of a stock's price.")
    @app_commands.describe(stock_id="Input the name or ID of the stock.",
                           start_hour="Input a number of hours ago desired. Accepts any whole number between 1 and 24.",
                           end_hour="Input a numeber of hours ago desired. Accepts any whole number between 2 and 24. "
                                    "End hour must be less than start hour. Defaults to now.")
    async def graph_hourly_value(self, interaction: discord.Interaction, stock_id: str,
                                 start_hour: app_commands.Range[int, 1, 24],
                                 end_hour: app_commands.Range[int, 2, 24] = 0):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # make sure hours are unequal
        if start_hour <= end_hour:
            return await interaction.followup.send("The end hour cannot be less than the start hour.")
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
        now = datetime.now()
        # get start hour
        start = now.replace(minute=0, second=0) - timedelta(hours=start_hour)
        # if the end date is none, get the time now
        if end_hour == 0:
            end = datetime.now()
        # otherwise, get the end date
        else:
            end = now.replace(minute=0, second=0) - timedelta(hours=end_hour)
        # get all data from the specified stock
        if stock_id == "average":
            pass
        stock_data = await conn.fetch('''SELECT * FROM exchange_log WHERE (timestamp BETWEEN $1 AND $2) 
        AND stock_id = $3 ORDER BY timestamp ASC;''', start, end, stock['stock_id'])
        if not stock_data:
            return await interaction.followup.send(f"Unfortunately, I cannot find any data between"
                                                   f"`{start.strftime('%H:%M')}` and "
                                                   f"`{end.strftime('%H:%M')}`.")
        stock_prices = [s['value'] for s in stock_data]
        dates = [d['timestamp'] for d in stock_data]
        fig, ax = plt.subplots()
        ax.plot(dates, stock_prices)
        ax.xaxis.set_major_locator(HourLocator(interval=1))
        ax.xaxis.set_major_formatter(DateFormatter("%H"))
        fig.autofmt_xdate()
        plt.grid(True, which="major")
        plt.title(f"{stock['name']} (ID: {stock['stock_id']})")
        plt.ylabel("Value")
        plt.xlabel("Time")
        plt.savefig(r"graph.png")
        return await interaction.followup.send(file=discord.File(fp=r"graph.png",
                                                                 filename=f"Graph of {stock['name']} share price.png",
                                                                 description=f"A graph representing the share prices of"
                                                                             f" {stock['name']}"))

    @exchange.command(name="graph_average_value", description="Displays a graph of the average price of all stocks.")
    @app_commands.describe(start_date="Input a valid date in DD/MM/YYYY format. "
                                      "Also accepts \"today\", \"forever\", \"week\", and \"month\".",
                           end_date="Input a valid date in DD/MM/YYYY format. If left blank, defaults to today.")
    async def graph_average_value(self, interaction: discord.Interaction,
                                  start_date: str, end_date: str = None):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
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
                                                       f"31/1/2020.\n"
                                                       f"This command also accepts `today`, `week`, `month`, "
                                                       f"and `forever` as acceptable arguments.")
        # if the end date is none, get the time now
        if end_date is None:
            end_date = datetime.now()
        # otherwise, get the end date
        else:
            end_date = datetime.strptime(end_date, "%d/%m/%Y")
        stock_data = await conn.fetch('''SELECT * FROM exchange_log WHERE (timestamp BETWEEN $1 AND $2) 
        ORDER BY timestamp;''', start_date, end_date)
        if not stock_data:
            return await interaction.followup.send(f"Unfortunately, I cannot find any data between"
                                                   f"`{start_date.date().strftime('%d/%m/%Y')}` and "
                                                   f"`{end_date.date().strftime('%d/%m/%Y')}`.")
        dates = pd.unique([d['timestamp'] for d in stock_data])
        averages = []
        for d in dates:
            stocks = []
            for s in stock_data:
                if s['timestamp'] == d:
                    stocks.append(s['value'])
            averages.append(sum(stocks) / len(stocks))
        fig, ax = plt.subplots()
        ax.plot(dates, averages)
        ax.xaxis.set_major_locator(DayLocator(interval=1))
        ax.xaxis.set_major_formatter(DateFormatter("%d/%m/%y"))
        fig.autofmt_xdate()
        days = (end_date - start_date).days
        if days >= 2:
            plt.grid(True, which="major")
            if days > 7:
                ax.xaxis.set_major_locator(DayLocator(interval=3))
            elif days > 30:
                ax.xaxis.set_major_locator(DayLocator(interval=10))
            elif days > 90:
                ax.xaxis.set_major_locator(DayLocator(interval=30))
            elif days > 180:
                ax.xaxis.set_major_locator(DayLocator(interval=60))
            elif days > 360:
                ax.xaxis.set_major_locator(YearLocator(month=start_date.month, day=start_date.day))
        else:
            ax.xaxis.set_minor_locator(HourLocator(interval=1))
            plt.grid(True, which="major")
            plt.grid(True, which="minor")
        plt.title(f"Average Stock Price")
        plt.ylabel("Value")
        plt.xlabel("Time")
        plt.savefig(r"graph.png")
        return await interaction.followup.send(file=discord.File(fp=r"graph.png",
                                                                 filename=f"Graph of average share price.png"))

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
            for space in range(0, 50 - len(this_string)):
                this_string += " "
            if stock['trending'] == "up":
                this_string += "``:chart_with_upwards_trend: ``"
            else:
                this_string += "``:chart_with_downwards_trend: ``"
            if stock['change'] >= 0:
                this_string += "+"
            this_string += f"{(stock['change'] * 100):.2f}%``\n"
            rank += 1
            stock_string += this_string
        # create embed
        feed_embed = discord.Embed(title="Stocks by Share Price", description=stock_string)
        feed_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
        embed_message = await interaction.followup.send(embed=feed_embed)
        await embed_message.edit(view=FeedView(self.bot, embed_message))

    # creates casino subgroup
    casino = app_commands.Group(name="casino", description="...", guild_only=True)

    @casino.command(name="rank", description="Displays the rank of casino users over time.")
    async def rank(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # fetch rank data
        rank_data = await conn.fetch('''SELECT * FROM casino_rank WHERE winnings != 0 ORDER BY winnings DESC;''')
        # for all items in the data, attach to rank string
        rank_string = ""
        rank = 1
        for u in rank_data:
            user = self.bot.get_user(u['user_id'])
            rank_string += f"{rank}. {user.name}#{user.discriminator}:  "
            if u['winnings'] < 0:
                rank_string += "-"
            rank_string += f"{self.thaler}{abs(u['winnings']):,.2f}\n"
            rank += 1
        rank_embed = discord.Embed(title="Royal Casino Rank by Winnings", description=rank_string)
        rank_embed.set_thumbnail(url="https://i.ibb.co/BKFyd2G/RBT-logo.png")
        await interaction.followup.send(embed=rank_embed)

    @casino.command(name="blackjack", description="Starts a game of blackjack, aka 21.")
    @app_commands.describe(bet="The amount of thaler to bet. Must be a whole number.")
    async def blackjack(self, interaction: discord.Interaction, bet: app_commands.Range[int, 1, 5000]):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # define author
        user = interaction.user
        # set bust
        bust = False
        # ensure membership
        rbt_member = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                         user.id)
        if rbt_member is None:
            return await interaction.followup.send("You are not a registered member of the Royal Bank of Thegye.")
        # ensure the user has enough thaler
        if rbt_member['funds'] < bet:
            return await interaction.followup.send(f"You do not have {self.thaler}{bet:,}.")
        # define deck
        deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A'] * 4
        # define face up card
        up_card = choice(deck)
        # define face down card
        hole_card = choice(deck)
        dealer_hand = [up_card, hole_card]
        player_hand = [choice(deck), choice(deck)]
        # define user
        user = interaction.user
        # define emojis
        real_dealer_hand_string = "".join([get_card_emoji(c) for c in dealer_hand])
        dealer_hand_string = f"{get_card_emoji(dealer_hand[0])}{get_card_emoji('back')}"
        player_hand_string = "".join([get_card_emoji(c) for c in player_hand])
        # define totals
        player_total = 0
        for card in player_hand:
            # if the card is a face card, give it a value of 10
            if card == "J" or card == "Q" or card == "K":
                card = 10
            # if the card is an ace, give it a value of 11
            elif card == "A":
                card = 11
            player_total += card
        dealer_total = 0
        for card in dealer_hand:
            # if the card is a face card, give it a value of 10
            if card == "J" or card == "Q" or card == "K":
                card = 10
            # if the card is an ace, give it a value of 11
            elif card == "A":
                card = 11
            dealer_total += card
        # if the total is more than 21, change aces
        if player_total > 21:
            if "A" in player_hand:
                for ace in player_hand:
                    if ace == "A":
                        player_total -= 10
                    if player_total < 21:
                        break
                if player_total > 21:
                    bust = True
            # otherwise, the player busts
            else:
                bust = True
        if dealer_total > 21:
            if "A" in dealer_hand:
                for ace in dealer_hand:
                    if ace == "A":
                        dealer_total -= 10
                    if dealer_total < 21:
                        break
        if player_total == 21:
            # create embed
            blackjack_embed = discord.Embed(title="Blackjack",
                                            description="A game of blackjack at the Casino Royal.")
            blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{bet:,.2f}", inline=False)
            blackjack_embed.add_field(name="Dealer's Hand",
                                      value=f"{real_dealer_hand_string} (total: {dealer_total})")
            blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
            blackjack_embed.add_field(name="Result", value="**BLACKJACK**", inline=False)
            winnings = round((bet * 3) - bet, 2)
            blackjack_embed.set_footer(text=f"Your winnings total: {self.thaler}{winnings:,.2f}")
            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                               winnings, user.id)
            await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                               winnings, user.id)
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'casino', f'Won {self.thaler}{winnings:,.2f} at blackjack')
            return await interaction.followup.send(embed=blackjack_embed)
        elif bust is True:
            # create embed
            blackjack_embed = discord.Embed(title="Blackjack",
                                            description="A game of blackjack at the Casino Royal.")
            blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{bet:,.2f}", inline=False)
            blackjack_embed.add_field(name="Dealer's Hand",
                                      value=f"{dealer_hand_string} (total: {dealer_total})")
            blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
            blackjack_embed.add_field(name="Result", value="***BUST***", inline=False)
            winnings = bet
            blackjack_embed.set_footer(text=f"Your total winnings: -{self.thaler}{winnings:,.2f}")
            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                               -winnings, user.id)
            await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                               -winnings, user.id)
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'casino', f'Lost {self.thaler}{winnings:,.2f} at blackjack')

            return await interaction.followup.send(embed=blackjack_embed)
        else:
            # create embed
            blackjack_embed = discord.Embed(title="Blackjack",
                                            description="A game of blackjack at the Casino Royal.")
            blackjack_embed.add_field(name="Bet", value=f"{self.thaler}{bet:,.2f}", inline=False)
            blackjack_embed.add_field(name="Dealer's Hand",
                                      value=f"{dealer_hand_string}")
            blackjack_embed.add_field(name="Player's Hand", value=f"{player_hand_string} (total: {player_total})")
            blackjack_message = await interaction.followup.send(embed=blackjack_embed)
            await blackjack_message.edit(embed=blackjack_embed,
                                         view=BlackjackView(author=interaction.user, bot=self.bot, m=blackjack_message,
                                                            bet=bet, player_hand=player_hand,
                                                            dealer_hand=dealer_hand))

    @casino.command(name="slots", description="Spins the slots.")
    @app_commands.describe(bet="The amount of thaler to bet. Must be a whole number.")
    @app_commands.checks.cooldown(1, 5, key=lambda c: (c.user.id, c.guild_id))
    async def slots(self, interaction: discord.Interaction, bet: app_commands.Range[int, 1, 5000]):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # fetch user info
        user_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''',
                                        user.id)
        # if the user does not exist
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the Royal Bank of Thegye.")
        # ensure user has bet funds
        if bet > user_info['funds']:
            return await interaction.followup.send(f"You do not have enough thaler to place that bet.")
        # define slots
        items = ["star", "moon", "bell", "heart", "diamond", "cherry", "clover",
                 "seven", "gem"] * 10
        items.append("axolotl")
        items.append("doubler")
        items.append("tripler")
        # define combos
        single_combo = ["cherry", "clover", "bell"]
        double_combo = ["star", "moon", "bell", "heart", "diamond"]
        triple_combo = ["cherry", "clover", "seven", "gem"]
        jackpot_combo = "axolotl"
        # roll slots
        slot1 = choice(items)
        slot2 = choice(items)
        slot3 = choice(items)
        slots = [slot1, slot2, slot3]
        # define payouts
        single = (bet * 2) - bet
        double = (bet * 5) - bet
        triple = (bet * 10) - bet
        jackpot = (bet * 50) - bet
        if "doubler" in slots:
            single *= 2
            double *= 2
        if "tripler" in slots:
            single *= 3
            double *= 3
        # get emojis
        slot_string = f"\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n" \
                      f"\u2502{get_card_emoji(slot1)} {get_card_emoji(slot2)} {get_card_emoji(slot3)}\u2502\n" \
                      f"\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518"
        # create embed
        slots_embed = discord.Embed(title="Slots", description="A game of slots at the Royal Casino.")
        slots_embed.add_field(name="Slots Result", value=slot_string, inline=False)
        # search jackpot combos
        if all(s == slots[0] for s in slots) and slots[0] in jackpot_combo:
            slots_embed.add_field(name="***JACKPOT***", value=f"Total winnings of {self.thaler}{jackpot:,.2f}!",
                                  inline=False)
            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                               jackpot, user.id)
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'casino', f'Won {self.thaler}{jackpot:,.2f} at slots')
            await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                               bet, user.id)
            return await interaction.followup.send(embed=slots_embed)
        # search for triple combos
        elif all(s == slots[0] for s in slots) and slots[0] in triple_combo:
            slots_embed.add_field(name="TRIPLE COMBO", value=f"Total winnings of {self.thaler}{triple:,.2f}!")
            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                               triple, user.id)
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'casino', f'Won {self.thaler}{triple:,.2f} at slots')
            await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                               bet, user.id)
            return await interaction.followup.send(embed=slots_embed)
        # search for double combos
        elif slots[0] == slots[1] and slots[0] in double_combo:
            slots_embed.add_field(name="DOUBLE COMBO", value=f"Total winnings of {self.thaler}{double:,.2f}!")
            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                               double, user.id)
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'casino', f'Won {self.thaler}{double:,.2f} at slots')
            await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                               bet, user.id)
            return await interaction.followup.send(embed=slots_embed)
        # search for single combos
        elif slots[0] in single_combo:
            slots_embed.add_field(name="SINGLE COMBO", value=f"Total winnings of {self.thaler}{single:,.2f}!")
            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                               single, user.id)
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'casino', f'Won {self.thaler}{single:,.2f} at slots')
            await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                               bet, user.id)
            return await interaction.followup.send(embed=slots_embed)
        # return no combos
        else:
            slots_embed.add_field(name="***LOSS***", value=f"Total winnings of -{self.thaler}{bet:,.2f}!")
            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                               -bet, user.id)
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'casino', f'Lost {self.thaler}{bet:,.2f} at slots')
            await conn.execute('''UPDATE casino_rank SET winnings = winnings + $1 WHERE user_id = $2;''',
                               -bet, user.id)
            return await interaction.followup.send(embed=slots_embed)

    @casino.command(name="slots_outcomes", description="Displays the slots combinations.")
    async def slots_outcomes(self, interaction: discord.Interaction):
        # define combos
        single_combo = ["cherry", "clover", "bell"]
        double_combo = ["star", "moon", "bell", "heart", "diamond"]
        triple_combo = ["cherry", "clover", "seven", "gem"]
        jackpot_combo = "axolotl"
        # create embed
        outcomes_embed = discord.Embed(title="List of Slots Combinations")
        outcomes_embed.add_field(name="Single Combo (2x payout)",
                                 value=" ".join([get_card_emoji(o) for o in single_combo]), inline=False)
        outcomes_embed.add_field(name="Double Combo (5x payout)",
                                 value=" ".join([get_card_emoji(o) for o in double_combo]), inline=False)
        outcomes_embed.add_field(name="Triple Combo (10x payout)",
                                 value=" ".join([get_card_emoji(o) for o in triple_combo]), inline=False)
        outcomes_embed.add_field(name="Jackpot Combo (50x payout)",
                                 value="".join(get_card_emoji(jackpot_combo)), inline=False)
        await interaction.response.send_message(embed=outcomes_embed)

    # creates market subgroup
    market = app_commands.Group(name="market", description="...", guild_only=True)

    @market.command(name="open", description="Opens the market and displays options.")
    async def open(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # create embed
        market_embed = discord.Embed(title="Royal Thegyan Market",
                                     description="Welcome to the Royal Thegye Market!\n"
                                                 "\n"
                                                 "To use the market, click on the select menu below and "
                                                 "select the option you desire to view.")
        message = await interaction.followup.send(embed=market_embed)
        await message.edit(view=MarketView(message))

    @market.command(name="item", description="Opens the market and displays options.")
    @app_commands.describe(item_id="The ID number of the item you want to buy.")
    async def item(self, interaction: discord.Interaction, item_id: int):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # fetch item information
        item_info = await conn.fetchrow('''SELECT * FROM rbt_market WHERE market_id = $1;''', item_id)
        # if there is no item, return such
        if item_info is None:
            return await interaction.followup.send(content="There is no item with that ID.", ephemeral=True)
        # create the embed for the item
        item_embed = discord.Embed(title=f"{item_info['name']}",
                                   description=f"Cost: {self.thaler}{item_info['value']:,}")
        item_embed.set_thumbnail(url=self.logo)
        item_embed.add_field(name="Description", value=f"{item_info['description']}")
        await interaction.followup.send(embed=item_embed)

    @market.command(name="buy", description="Buys an item from the marketplace.")
    @app_commands.describe(item_id="The ID number of the item you want to buy.")
    async def buy(self, interaction: discord.Interaction, item_id: int):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # fetch user information
        user_info = await conn.fetchrow('''SELECT * FROM rbt_users WHERE user_id = $1;''', user.id)
        # ensure user registration
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the Royal Bank of Thegye.")
        # fetch item information
        item_info = await conn.fetchrow('''SELECT * FROM rbt_market WHERE market_id = $1;''', item_id)
        # ensure item existence
        if item_info is None:
            return await interaction.followup.send(f"No item with ID `{item_id}` exists.")
        # define item value
        value = item_info['value']
        # if the item is the wallet expansion, multiply accordingly
        if item_info['name'] == "Wallet Expansion":
            value = (user_info['wallet'] / 100) * 1000
        # ensure the user can afford item
        if value > user_info['funds']:
            return await interaction.followup.send(f"You do not have enough thaler to purchase {item_info['name']}.")
        # remove funds from user
        await conn.execute('''UPDATE rbt_users SET funds = funds - $1 WHERE user_id = $2;''',
                           value, user.id)
        # add funds to general fund
        await conn.execute('''UPDATE funds SET current_funds = current_funds + $1 WHERE name = 'General Fund';''',
                           value)
        # add to market_ledger
        await conn.execute('''INSERT INTO market_ledger VALUES ($1,$2);''',
                           item_info['market_id'], user.id)
        # update logs
        await conn.execute('''INSERT INTO rbt_user_log VALUES ($1,$2,$3);''',
                           user.id, 'market', f"Bought {item_info['name']} (ID: {item_info['market_id']}) from the"
                                              f"{item_info['market']} for {self.thaler}{value:,}.")
        # if the user bought a wallet expansion, upgrade wallet
        if item_info['name'] == "Wallet Expansion":
            await conn.execute('''UPDATE rbt_users SET wallet = wallet + 100 WHERE user_id = $1;''', user.id)
        return await interaction.followup.send(f"You have successfully purchased {item_info['name']} for "
                                               f"{self.thaler}{value:,}")

    @commands.command()
    @commands.is_owner()
    async def stock_reset(self, ctx):
        # establish connection
        conn = self.bot.pool
        # reset all users to 500 thaler
        await conn.execute('''UPDATE rbt_users SET funds = 500;''')
        # clear all contracts and accounts
        await conn.execute('''DELETE FROM contracts;''')
        await conn.execute('''DELETE FROM bank_ledger;''')
        # clear stock ledger
        await conn.execute('''DELETE FROM ledger;''')
        # remove stock logs and set stock prices to a random number between 15 and 45
        await conn.execute('''DELETE FROM exchange_log;''')
        await conn.execute('''UPDATE stocks SET value = random()*(46-15)+15, change = 0, 
        outstanding = 0, issued = 10000;''')
        # clear logs
        await conn.execute('''DELETE FROM rbt_user_log;''')
        await conn.execute('''UPDATE casino_rank SET winnings = 0;;''')
        # reset funds
        await conn.execute('''UPDATE funds SET current_funds = 250000, fund_limit = 500000 
        WHERE name = 'General Fund';''')
        await conn.execute('''UPDATE funds SET current_funds = 50000 WHERE name = 'Investment Fund';''')
        await ctx.send("Done!")


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = Economy(bot)
    await bot.add_cog(cog)
