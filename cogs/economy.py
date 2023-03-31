import pandas as pd
import discord
import helper
from discord import Member
from discord.ext import commands
from discord.ext.commands import Cog
from config.config import BANK_PATH

class Economy(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="loseMoney")
    async def withdraw_money(self, ctx, money) -> None:
        money = int(money)
        bank_df = pd.read_csv(BANK_PATH, header="infer")
        users = bank_df.Usernames
        users = list(users)
        # if member isn't in dataframe already, put them in and give them 100 GleepCoins
        if ctx.author.name not in users:
            bank_df.loc[len(bank_df.index)] = [ctx.author.name, 100]
        current_balance = helper.getUserAmount(bank_df, ctx.author.name)
        helper.setUserAmount(bank_df, ctx.author.name, current_balance - money)
        bank_df.to_csv(BANK_PATH, index=False)
        await ctx.send(f"Withdrew {money} GleepCoins from {ctx.author.name}'s account")

    @commands.command(name="giveMoney")
    async def award_money(self, ctx, money):
        money = int(money)
        bank_df = pd.read_csv(BANK_PATH, header='infer')
        users = bank_df.Usernames
        users = list(users)
        print(users)
        print(ctx.author.name)
        if not ctx.author.name in users:
            bank_df.loc[len(bank_df.index)] = [ctx.author.name, 100]
        current_amount = helper.getUserAmount(bank_df, ctx.author.name)
        helper.setUserAmount(bank_df, ctx.author.name, current_amount + money)
        bank_df.to_csv(BANK_PATH, index=False)
        await ctx.send(f"Added {money} GleepCoins to {ctx.author.name}'s account.")

async def setup(bot):
    await bot.add_cog(Economy(bot))