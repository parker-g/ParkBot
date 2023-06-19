import pyttsx3
import discord
import asyncio
from discord.ext.commands import Cog
from discord.ext import commands
from config.config import NAUGHTY_WORDS

class Reward(Cog):
    def __init__(self, bot):
        self.bot = bot

    async def processAudio(self, ctx, string):
        engine = pyttsx3.init("sapi5")
        voices = engine.getProperty('voices')
        engine.setProperty("voice", voices[0].id) # 0 for male, 1 for female
        engine.save_to_file(string, "data/say.mp3")
        # default speaking rate is 200
        engine.setProperty("rate", 125)
        engine.runAndWait()
        message = await ctx.send("Processed Request")
        await message.delete(delay = 5.0)

    @commands.command()
    async def say(self, ctx, *args):
        speech = ""
        for arg in args:
            arg = str(arg)
            speech += f"{arg} "
            if arg.lower() in NAUGHTY_WORDS:
                speech = "You said a naughty word. Bad."
                break
        await self.processAudio(ctx, speech)

        current_channel = ctx.author.voice.channel
        voice = await current_channel.connect()
        try:
            audio = discord.FFmpegPCMAudio("data/say.mp3", executable="C:/Program Files/FFmpeg/bin/ffmpeg.exe")
            voice.play(source=audio)
            await asyncio.sleep(15.0)
            await voice.disconnect()
        except:
            print("The audio was not properly stored in memory")
        

        

async def setup(bot):
   await bot.add_cog(Reward(bot))

