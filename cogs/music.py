from googleapiclient.discovery import build
from config.config import GOOGLE_API_KEY
from discord.ext import commands
from discord import Embed
from mutagen import mp3
import yt_dlp
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = build('youtube', 'v3', developerKey=GOOGLE_API_KEY)

    @commands.command("search")
    async def getSearchResults(self, ctx = None, *args):
        query = ""
        for arg in args:
            query += f"{arg} "
        request = self.service.search().list(
        part='snippet',
        maxResults=5,
        q=str(args))

        response = request.execute() # response is a json object in dict format
        titles_and_ids = []
        for item in response["items"]:
            id = item["id"]
            snippet = item["snippet"]
            title = snippet["title"]
            titles_and_ids.append((title, id))

        if ctx is None:
            return titles_and_ids
        titles_string = ""
        for i in range(5):
            titles_string += f"{i+1}. {titles_and_ids[i][0]}\n"
        titles_string += "Please select one title 1-5, or type cancel to cancel your selection."
        em = Embed(title="YouTube Search", description=titles_string)
        await ctx.send(embed=em)


    async def getSong(youtube_id):
        base_address = "https://www.youtube.com/watch?v="
        ytdl_format_options = {
            "no_playlist": True,
            "max_downloads": 1,
            'format': 'mp3/bestaudio/best',
            "outtmpl": "data/current_audio.%(ext)s",
            "ffmpeg_location": "C:/Program Files/FFmpeg/bin/ffmpeg.exe",
                # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
                'postprocessors': [{  # Extract audio using ffmpeg
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
        }
        youtube_url = [base_address + youtube_id]
        print(youtube_url)
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            ydl.download(youtube_url)
        await asyncio.sleep(5.0)

    @commands.command
    async def play(self, ctx, *args):
        titles_and_ids = await self.getSearchResults(self, None, *args)
        message1 = await ctx.send(embed = Embed(title=f"Playing: {titles_and_ids[0][0]}"))
        

    async def getAudioLength(self, path_to_audio):
        audio = mp3.MP3(path_to_audio)
        audio = audio.info
        audiolen = int(audio.length)
        return audiolen

async def setup(bot):
    await bot.add_cog(Music(bot))
        
