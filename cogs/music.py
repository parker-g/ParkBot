from googleapiclient.discovery import build
from config.config import GOOGLE_API_KEY
from discord.ext import commands
from discord import Embed
from mutagen import mp3
from collections import deque
import helper
import os
import html
import time
import discord
import yt_dlp
from youtube_dl import YoutubeDL
import asyncio

SONG_PATH = "data/current_audio.mp3"

class PlayList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playque = deque()

    def isEmpty(self):
        return len(self.playque) == 0
    
    def add(self, video_tuple):
        self.playque.append(video_tuple)

    @commands.command()
    async def addToQ(self, ctx, video_tuple):
        self.add(video_tuple)
        added_to_q = await ctx.send(embed = Embed(title=f"{video_tuple[0]} added to queue."))
        await added_to_q.delete(delay=5.0)

    def remove(self): 
        self.playque.popleft()


    @commands.command("showQ")
    async def showQueue(self, ctx):
        pretty_string = ""
        count = 1
        for title, id in self.playlist.playque:
            pretty_string += f"{count}: {title}\n"
            count += 1
        await ctx.send(embed = Embed(title=f"Current Queue", description=f"{pretty_string}"))

# grabs various resources from the internet
class Grabber:
    def __init__(self, bot):
        self.bot = bot
        self.downloading = False
        self.service = build('youtube', 'v3', developerKey=GOOGLE_API_KEY)
    
    async def getSearchResults(self, ctx=None, *args, maxResults=1):
        query = ""
        for arg in args:
            query += f"{str(arg)} "
        request = self.service.search().list(
        part='snippet',
        maxResults=int(maxResults),
        q=str(query))

        response = request.execute() # response is a json object in dict format
        titles_and_ids = []
        for item in response["items"]:
            id = item["id"]["videoId"]
            title = html.unescape(item["snippet"]["title"])
            titles_and_ids.append((title, id))

        if ctx is None:
            return titles_and_ids
    
    def getSong(self, youtube_id):
        base_address = "https://www.youtube.com/watch?v="
        ytdl_format_options = {
            "no_playlist": True,
            # "max_downloads": 1,
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
        
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            ydl.download(youtube_url)
        return


class MusicController(commands.Cog):
    def __init__(self, bot, playlist:PlayList):
        self.bot = bot
        self.playlist = playlist
        self.current_song = None
        self.grabber = Grabber(bot)
        self.voice = None
        self.playing = False
        self.from_skip = False
    
    async def waitTime(self, time_in_seconds):
        print(f"Waiting for {time_in_seconds} seconds.")
        await asyncio.sleep(float(time_in_seconds))
        self.playing = False
        print("Done waiting")
        return

    @commands.command()
    async def showQ(self, ctx):
        await self.playlist.showQueue(self, ctx)

    @commands.command()
    async def currentSong(self, ctx):
        await ctx.send(embed=Embed(title=f"Current Song", description=f"{self.current_song[0]}"))

    # I want to continue experimenting with this later down the line -
    #seems there's some way to play songs without downloading ? not sure
    async def playURL(self, ctx, url):
        author_vc = ctx.author.voice.channel
        if not self.voice:
            self.voice = await author_vc.connect()
        
        with YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['formats'][0]['url']
            self.voice.play(discord.FFmpegPCMAudio(audio_url))

    #must take error as a parameter since it will be passed into an "after" function
    def play_next(self, err):
        self.playing = False
        if not self.playlist.isEmpty():
            self.current_song = self.playlist.playque[0]
            self.playlist.remove()
            self.grabber.getSong(self.current_song[1])
            audio = discord.FFmpegPCMAudio(SONG_PATH, executable="C:/Program Files/FFmpeg/bin/ffmpeg.exe")
            if self.playing is False:
                self.playing = True
                self.voice.play(source = audio, after = self.play_next)
        elif err:
            print(err)
            return

    def _play_song(self):
        # download song
        if not self.playlist.isEmpty():
            self.current_song = self.playlist.playque[0]
            if not self.from_skip:
                self.playlist.remove()
            self.from_skip = False
            self.grabber.getSong(self.current_song[1])
            
            audio = discord.FFmpegPCMAudio(SONG_PATH, executable="C:/Program Files/FFmpeg/bin/ffmpeg.exe")
            if self.playing is False:
                self.playing = True
                self.voice.play(source = audio, after = self.play_next)

    @commands.command()
    async def play(self, ctx, *args):
        # search requested song and add it to the queue
        title_and_id = await self.grabber.getSearchResults(None, args, maxResults=1)
        await self.playlist.addToQ(self.playlist, ctx, title_and_id[0])

        if self.voice is None:
            current_channel = ctx.author.voice.channel
            self.voice = await current_channel.connect(timeout = None)
        if self.playing is False:
            self._play_song()
        
        
    @commands.command()
    async def skip(self, ctx):
        if self.playlist.isEmpty():
            await ctx.send(embed=Embed(title=f"Queue is already empty."))
        else:
            await ctx.send(embed=Embed(title=f"Skipping {self.current_song[0]}."))
            self.voice.stop()
            self.playing = False
            self.from_skip = True
            self._play_song()

    @commands.command()
    async def kickBot(self, ctx):
        if self.playing is True:
            self.voice.stop()
        await self.voice.disconnect()
        self.voice = None


    def getAudioLength(self, path_to_audio):
        audio = mp3.MP3(path_to_audio)
        audio = audio.info
        audiolen = int(audio.length)
        return audiolen

    def formatAudioLength(self, audio_length):
        seconds = audio_length % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return hour, minutes, seconds

async def setup(bot):
    await bot.add_cog(MusicController(bot, PlayList(bot)))
        