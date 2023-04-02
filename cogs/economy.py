import pandas as pd
import helper
from discord.ext import commands
from discord.ext.commands import Cog
from config.config import BANK_PATH
from discord import Embed
class Economy(Cog):
    def __init__(self, bot):
        self.bot = bot

    async def withdrawMoney(self, ctx, money) -> None:
        money = int(money)
        bank_df = pd.read_csv(BANK_PATH, header="infer")
        users = bank_df.Usernames
        users = list(users)
        # if member isn't in dataframe already, put them in and give them 100 GleepCoins
        if ctx.author.name not in users:
            bank_df.loc[len(bank_df.index)] = [ctx.author.name, 1000]
        current_balance = helper.getUserAmount(bank_df, ctx.author.name)
        # if user has insufficient funds, then don't let them withdraw
        if money > current_balance:
            broke_message = await ctx.send(embed = Embed(title=f"{ctx.author.name}, you're broke. Your current balance is {current_balance}."))
            await broke_message.delete(delay=10.0)
            return False
        helper.setUserAmount(bank_df, ctx.author.name, current_balance - money)
        bank_df.to_csv(BANK_PATH, index=False)

    async def giveMoney(self, ctx, money):
        money = int(money)
        bank_df = pd.read_csv(BANK_PATH, header='infer')
        users = bank_df.Usernames
        users = list(users)
        # if member isn't in dataframe, add them + give them 100 gleepcoins
        if not ctx.author.name in users:
            bank_df.loc[len(bank_df.index)] = [ctx.author.name, 1000]
        current_amount = helper.getUserAmount(bank_df, ctx.author.name)
        helper.setUserAmount(bank_df, ctx.author.name, current_amount + money)
        bank_df.to_csv(BANK_PATH, index=False)

    async def giveMoneyPlayer(self, player, money):
        money = int(money)
        bank_df = pd.read_csv(BANK_PATH, header='infer')
        users = bank_df.Usernames
        users = list(users)
        # if member isn't in dataframe, add them + give them 100 gleepcoins
        if not player.name in users:
            bank_df.loc[len(bank_df.index)] = [player.name, 100]
        current_amount = helper.getUserAmount(bank_df, player.name)
        helper.setUserAmount(bank_df, player.name, current_amount + money)
        bank_df.to_csv(BANK_PATH, index=False)


    # implement later
    @commands.command("balance")
    async def showMoney(self, ctx):
        pass

async def setup(bot):

    await bot.add_cog(Economy(bot))
    return Economy(bot)