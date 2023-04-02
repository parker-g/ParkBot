import pandas as pd
import helper
from discord.ext import commands
from discord.ext.commands import Cog
from config.config import BANK_PATH

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
            bank_df.loc[len(bank_df.index)] = [ctx.author.name, 100]
        current_balance = helper.getUserAmount(bank_df, ctx.author.name)
        helper.setUserAmount(bank_df, ctx.author.name, current_balance - money)
        bank_df.to_csv(BANK_PATH, index=False)

    async def giveMoney(self, ctx, money):
        money = int(money)
        bank_df = pd.read_csv(BANK_PATH, header='infer')
        users = bank_df.Usernames
        users = list(users)
        # if member isn't in dataframe, add them + give them 100 gleepcoins
        if not ctx.author.name in users:
            bank_df.loc[len(bank_df.index)] = [ctx.author.name, 100]
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