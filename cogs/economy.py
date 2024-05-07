from discord import Embed
from discord import Member, User
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands import Context

import db
from db import Connection


class Economy(Cog):

    def __init__(self, bot, db_connection:Connection):
        self.bot = bot
        self.connection = db_connection

    async def withdraw_money_player(self, ctx:Context, player:Member | User, money:int) -> bool:
        self.connection.create_user_if_none(player.name, str(player.id))
        withdraw_amount = int(money)
        current_balance = self.connection.get_user_amount(player.id)
        if withdraw_amount > current_balance:
            broke_message = await ctx.send(embed = Embed(title=f"{player.name}, you're broke. Your current balance is {current_balance}."))
            await broke_message.delete(delay=10.0)
            return False
        else:
            self.connection.set_user_amount(player.id, current_balance - withdraw_amount)
            return True

    async def give_money_player(self, player:Member | User, money:int) -> None:
        money = int(money)
        self.connection.create_user_if_none(player.name, str(player.id))
        current_amount = self.connection.get_user_amount(player.id)
        self.connection.set_user_amount(player.id, current_amount + money)

    def _get_balance(self, player:Member|User):
        amount = self.connection.get_user_amount(player.id)
        return amount

    @commands.command("balance")
    async def get_balance(self, ctx:Context) -> None:
        amount = self.connection.get_user_amount(ctx.author.id)
        if amount is None:
            self.connection.create_user_if_none(ctx.author.name, ctx.author.id)
            amount = self.connection.get_user_amount(ctx.author.id)
        message = await ctx.send(embed = Embed(title=f"{ctx.author.name}'s balance is: {amount} GleepCoins."))
        await message.delete(delay=7.5)

    @commands.command("pocketWatch")
    async def pocket_watch(self, ctx:Context):
        bank_df_string = self.connection.stringify_all_user_amounts(ctx)
        await ctx.send(embed = Embed(title=f"Domain Expansion: Pocket Watch", description=bank_df_string))

async def setup(bot):
    connection = db.get_connection("Economy cog")
    await bot.add_cog(Economy(bot, connection))