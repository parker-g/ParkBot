from googleapiclient.discovery import build
from config.config import GOOGLE_API_KEY
from discord.ext import commands
from discord import Embed
from mutagen import mp3
from collections import deque
import html
import time
import discord
import yt_dlp
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
        q=str(args))

        response = request.execute() # response is a json object in dict format
        titles_and_ids = []
        for item in response["items"]:
            id = item["id"]["videoId"]
            title = html.unescape(item["snippet"]["title"])
            titles_and_ids.append((title, id))

        if ctx is None:
            return titles_and_ids
    
    async def getSong(self, youtube_id):
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
        
        if (self.downloading is False): 
            self.downloading = True
            with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
                ydl.download(youtube_url)
            # check for existence of temp files to check if song's done downloading
            await asyncio.sleep(5.0)
            self.downloading = False
            return
        else:
            print("You're already downloading a song right now.")
            return
        
        

class MusicController(commands.Cog):
    def __init__(self, bot, playlist:PlayList):
        self.bot = bot
        self.playlist = playlist
        self.grabber = Grabber(bot)
        self.voice = None
        self.playing = False
    
    async def waitTime(self, time_in_seconds):
        await asyncio.sleep(float(time_in_seconds))
        self.playing = False
        return

    @commands.command()
    async def showQ(self, ctx):
        await self.playlist.showQueue(self, ctx)

    @commands.command()
    async def play(self, ctx, *args):
        # search requested song and add it to the queue
        title_and_id = await self.grabber.getSearchResults(None, args, maxResults=1)
        await self.playlist.addToQ(self.playlist, ctx, title_and_id[0])

        if self.voice is None:
            current_channel = ctx.author.voice.channel
            self.voice = await current_channel.connect(timeout = 600)

        # if music already playing: wait
        if (self.playing is True): # if bot is already in the current channel, and if a song's already playing 
                queue_time = time.time()
                audio_elapsed_time = self.play_time - queue_time
                audio_length = self.getAudioLength(SONG_PATH)
                time_to_wait = audio_length - audio_elapsed_time
                await self.waitTime(time_to_wait)

        # while songs are in the queue, 
        while (self.playlist.isEmpty() is False):
            next_song = self.playlist.playque[0]
            if self.playing is False:
                processing = await ctx.send(embed = Embed(title = f"Processing {next_song[0]}."))
                await self.grabber.getSong(str(next_song[1]))
                await processing.delete()

                if self.grabber.downloading is False:
                    self.play_task = asyncio.create_task(self.broadcastSong(ctx, next_song))
                    await self.play_task

        if self.playlist.isEmpty():
            await self.voice.disconnect()

    @commands.command()
    async def skip(self, ctx):
        if (self.playlist.isEmpty()) and (self.playing is False):
            await ctx.send(embed = Embed(title="The queue must not be empty to skip a song."))
        elif self.playing is True:
            try:
                await ctx.send(embed=Embed(title="Skipping current song."))
                self.playlist.remove()
                await self.play_task.cancel()
                self.playing = False
            except:
                print("Cleaning up canceled task.")

    async def broadcastSong(self, ctx, name_and_id):
        if self.grabber.downloading is False:
            try:
                audio = discord.FFmpegPCMAudio(SONG_PATH, executable="C:/Program Files/FFmpeg/bin/ffmpeg.exe")
                self.playing = True
                length = self.getAudioLength(SONG_PATH)
                hours, minutes, seconds = self.formatAudioLength(length)
                try:
                    self.voice.play(source=audio)
                    playing_message = await ctx.send(embed = Embed(title=f"Playing {name_and_id[0]}", description = f"{hours}:{minutes}:{seconds}"))
                    await playing_message.delete(delay = length)
                    await self.waitTime(length)
                    self.playlist.remove()
                except: 
                    self.playing = False
                    # this is where control flows when task is canceled
            except:
                self.playing = False
                print("Error accessing song from path provided.")

    def getAudioLength(self, path_to_audio):
        audio = mp3.MP3(path_to_audio)
        audio = audio.info
        audiolen = int(audio.length)
        return audiolen

    def formatAudioLength(self, audio_length):
        hours = audio_length // 3600
        audio_length %= 60
        minutes = audio_length // 60
        audio_length %= 60
        seconds = audio_length
        return hours, minutes, seconds

async def setup(bot):
    await bot.add_cog(MusicController(bot, PlayList(bot)))
        