import pyttsx3
import discord
import asyncio
from cogs.controller import Controller
from discord.ext.commands import Cog
from discord.ext import commands
from discord import Embed
from config.configuration import NAUGHTY_WORDS


class RewardsController(Controller):
    def __init__(self, bot):
        super().__init__(bot, TTS)
    
    @commands.command()
    async def say(self, ctx, *args) -> None:
        tts = self.getGuildClazz(ctx) # should be a TTS instance
        await tts._say(ctx, args)

class TTS(Cog):
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

    async def _say(self, ctx, *args):
        
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client:
            if voice_client.is_playing():
                await ctx.send(embed=Embed(title=f"Unable to Speak", description=f"The voice client is already occupied. Try again when it's not."))
                return
            
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
   await bot.add_cog(RewardsController(bot))

