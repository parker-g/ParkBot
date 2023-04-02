import discord
from discord.ext.commands import Cog
from discord.ext import commands

class Reward(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def say(self, ctx, *args):
        speech = ""
        for arg in args:
            speech += f" {arg}"
        message = await ctx.send(speech, tts=True)
        await message.delete(15.0)

async def setup(bot):
   await bot.add_cog(Reward(bot))

