from googleapiclient.discovery import build
from config.config import GOOGLE_API_KEY
from discord.ext import commands
from discord import Embed
from mutagen import mp3
import html
import time
import discord
import yt_dlp
import asyncio

SONG_PATH = "data/current_audio.mp3"


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = build('youtube', 'v3', developerKey=GOOGLE_API_KEY)
        self.queue = []
        self.voice = None
        self.play_time = None
        self.playing = False

    @commands.command("search")
    async def getSearchResults(self, ctx = None, *args, maxResults=1):
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
            id = item["id"]
            snippet = item["snippet"]
            title = snippet["title"]
            title = html.unescape(title)
            titles_and_ids.append((title, id))

        if ctx is None:
            return titles_and_ids

        # finish implementing search function ( as used in vexera)

        # else:
        #     titles_string = ""
        #     for i in range(5):
        #         titles_string += f"{i+1}. {titles_and_ids[i][0]}\n"
        #     titles_string += "Please select one title 1-5, or type cancel to cancel your selection."
        #     em = Embed(title="YouTube Search", description=titles_string)
        #     await ctx.send(embed=em)


    # maybe refactor this to actually save audio as the song name. then later
    # delete the song using the song name from the queue. This could allow
    # for processing/downloading a song ahead of the currently queued song for 
    # faster song results
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
        print(youtube_url)
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            ydl.download(youtube_url)
        

    @commands.command()
    async def skip(self, ctx):
        if self.qEmpty() == False:
         #   current_channel = ctx.author.voice.channel
            if self.playing is True:
                self.voice.stop()
                await ctx.send(embed=Embed(title="Skipping current song."))
                await self.play(ctx, "blah", searchArgs=False) # searchArgs false means don't search the "blah" I pass here.
        else:
            await ctx.send(embed = Embed(title="The queue must not be empty to skip a song."))

    async def waitTime(self, time_in_seconds):
        await asyncio.sleep(float(time_in_seconds))


    async def waitSong(self):
        audio_len_seconds= self.getAudioLength(SONG_PATH)
        for second in range(audio_len_seconds): # don't leave until song is over
            await asyncio.sleep(1)
        if self.voice is not None:
            self.voice.stop()


    async def addToQ(self, ctx, song_name, song_id):
        self.queue.append((str(song_name), song_id))
        added_to_q = await ctx.send(embed = Embed(title=f"{song_name} added to queue."))
        await added_to_q.delete(delay=5.0)


    @commands.command("showQ")
    async def showQueue(self, ctx):
        pretty_string = ""
        for title, id in self.queue:
            pretty_string += f"{title}\n"
        await ctx.send(embed = Embed(title=f"Current Queue", description=f"{pretty_string}"))
    
    @commands.command()
    async def play(self, ctx, *args, searchArgs = True):
         # if args is our special skip word, then don't try to enqueue anything
        if searchArgs is True:
            titles_and_ids = await self.getSearchResults(None, *args, maxResults=1)
            first_song = titles_and_ids[0]
            song_name = first_song[0]
            song_id = first_song[1]
            song_id = song_id["videoId"]

        # if self.qEmpty():
        #     self.addToQ(ctx, str(song_name), song_id)
        #     processing_message = await ctx.send(embed=Embed(title="Processing your song."))
        #     await self.getSong(song_id) # download the first result
        #     await processing_message.delete()
        #     message1 = await ctx.send(embed = Embed(title=f"Playing: {song_name}"))
        #     await self.broadcastAndPopSong(ctx) #handles popping queue
        #     await message1.delete() #delete message when song is over
            await self.addToQ(ctx, song_name, song_id)
        while self.qEmpty() == False or self.voice is not None:
            if self.voice is not None:
                await asyncio.sleep(1.0)
                if searchArgs == True:
                    if self.voice.is_playing(): # if a song's already playing
                        queue_time = time.time()
                        audio_elapsed_time = self.play_time - queue_time
                        audio_length = self.getAudioLength(SONG_PATH)
                        time_to_wait = audio_length - audio_elapsed_time
                        await self.waitTime(time_to_wait + 2.0) # 3 seconds of buffer time
            next_song = self.queue[0]
            processing = await ctx.send(embed = Embed(title = f"Processing {next_song[0]}."))
            await self.getSong(str(next_song[1]))
            self.play_time = time.time()

            await processing.delete()
            message2 = await ctx.send(embed = Embed(title=f"Playing: {next_song[0]}"))
            await self.broadcastSong(ctx)
            length = self.getAudioLength(SONG_PATH)
            await message2.delete(delay=float(length)) # don't delete "playing" message until song is over
            if self.qEmpty():
                await self.voice.disconnect()       
            else:
                self.queue.pop(0)         


    def qEmpty(self):
        return (len(self.queue) == 0)

    async def broadcastSong(self, ctx):
        current_channel = ctx.author.voice.channel
        if self.voice is None:
            self.voice = await current_channel.connect()
        try:
            audio = discord.FFmpegPCMAudio(SONG_PATH, executable="C:/Program Files/FFmpeg/bin/ffmpeg.exe")
            self.voice.play(source=audio)
            self.playing = True
        except:
            print("There was an error playing your song.")
        
        
    def isBotConnected(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is None:
            return False
        return True

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
    await bot.add_cog(Music(bot))
        
