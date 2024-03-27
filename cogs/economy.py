import pandas as pd
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands import Context

import db
from db import Connection
from config.configuration import BANK_PATH


class Economy(Cog):

    def __init__(self, bot, db_connection:Connection):
        self.bot = bot
        self.connection = db_connection

    async def withdrawMoneyPlayer(self, ctx, player, money:int) -> bool:
        self.connection.create_user_if_none(player.name)
        withdraw_amount = int(money)
        current_balance = self.connection.get_user_amount(player.name)
        if withdraw_amount > current_balance:
            broke_message = await ctx.send(embed = Embed(title=f"{player.name}, you're broke. Your current balance is {current_balance}."))
            await broke_message.delete(delay=10.0)
            return False
        else:
            self.connection.set_user_amount(player.name, current_balance - withdraw_amount)
            return True


    async def withdrawMoney(self, ctx:Context, money:int) -> bool:
        """
        Takes context and amount as arguments; withdraws said amount from ctx.author's bank balance.

        Args:
            ctx (discord.Context): context the method is called from,

            money (int): amount of money to withdraw from caller's bank balance

        Returns:
            None
        """
        money = int(money)
        self.connection.create_user_if_none(ctx.author.name)
        current_balance = self.connection.get_user_amount(ctx.author.name)
        # if user has insufficient funds, then don't let them withdraw
        if money > current_balance:
            return False
        self.connection.set_user_amount(ctx.author.name, current_balance - money)
        return True

    async def giveMoney(self, ctx, money) -> None:
        money = int(money)
        self.connection.create_user_if_none(ctx.author.name)
        current_amount = self.connection.get_user_amount(ctx.author.name)
        self.connection.set_user_amount(ctx.author.name, current_amount + money)

    async def giveMoneyPlayer(self, player, money) -> None:
        money = int(money)
        self.connection.create_user_if_none(player.name)
        current_amount = self.connection.get_user_amount(player.name)
        self.connection.set_user_amount(player.name, current_amount + money)

    def _getBalance(self, player):
        amount = self.connection.get_user_amount(player.name)
        return amount

    @commands.command("balance")
    async def getBalance(self, ctx) -> None:
        try:
            amount = self.connection.get_user_amount(ctx.author.name)
        except Exception as e:
            amount = 1000
            self.connection.set_user_amount(ctx.author.name, amount)
        message = await ctx.send(embed = Embed(title=f"{ctx.author.name}'s balance is: {amount} GleepCoins."))
        await message.delete(delay=7.5)

    @commands.command()
    async def pocketWatch(self, ctx):
        bank_df_string = self.connection.stringify_all_user_amounts(ctx)
        await ctx.send(embed = Embed(title=f"Domain Expansion: Pocket Watch", description=bank_df_string))

async def setup(bot):
    connection = db.get_connection()
    await bot.add_cog(Economy(bot, connection))