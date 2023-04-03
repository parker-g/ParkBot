import pyttsx3
import discord
import asyncio
from discord.ext.commands import Cog
from discord.ext import commands

class Reward(Cog):
    def __init__(self, bot):
        self.bot = bot

    async def processAudio(self, ctx, string):
        engine = pyttsx3.init("sapi5")
        engine.save_to_file(string, "data/test.mp3")
        engine.runAndWait()
        await ctx.send("Processed Request")

    @commands.command()
    async def say(self, ctx, *args):
        speech = ""
        for arg in args:
            speech += f" {arg}"
        await self.processAudio(ctx, speech)

        current_channel = ctx.author.voice.channel
        voice = await current_channel.connect()
        try:
            audio = discord.FFmpegPCMAudio("data/test.mp3", executable="C:/Program Files/FFmpeg/bin/ffmpeg.exe")
        except:
            print("The audio was not properly stored in memory")
        voice.play(source=audio)
        await asyncio.sleep(30)
        await voice.disconnect()

        

async def setup(bot):
   await bot.add_cog(Reward(bot))

