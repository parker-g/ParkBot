import pandas as pd
import discord
from discord import Member
from discord.ext import commands
from discord.ext.commands import Cog
from config.config import BANK_PATH

class Economy(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def withdraw_money(member:Member, money) -> None:
        bank_df = pd.read_csv(BANK_PATH, header="infer")
        users = bank_df.Usernames
        # if member isn't in dataframe already, put them in and give them 100 GleepCoins
        if member.name not in users:
            bank_df.loc[len(bank_df.index)] = [member.name, 100]
        current_balance = bank_df.loc[member.name, 'GleepCoins']
        bank_df.loc[member.name, "GleepCoins"] = current_balance - money
        bank_df.to_csv(BANK_PATH, index=False)

    @commands.command()
    async def award_money(self, member:Member, money):
        bank_df = pd.read_csv(BANK_PATH, header='infer')
        users = bank_df.Usernames
        if member.name not in users:
            bank_df.loc[len(bank_df.index)] = [member.name, 100]
        current_balance = bank_df.loc[member.name, 'GleepCoins']
        bank_df.loc[member.name, "GleepCoins"] = current_balance + money
        bank_df.to_csv(BANK_PATH, index=False)

async def setup(bot):
    await bot.add_cog(Economy(bot))