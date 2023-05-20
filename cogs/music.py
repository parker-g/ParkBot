from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config.config import GOOGLE_API_KEY, DATA_DIRECTORY, FFMPEG_PATH
from discord.ext import commands
from discord import Embed
from mutagen import mp3
from collections import deque
import helper
import html
import discord
import yt_dlp
from youtube_dl import YoutubeDL
import asyncio

class PlayList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playque = deque()
        self.playhistory = deque(maxlen=5)

    def isEmpty(self):
        return len(self.playque) == 0
    
    def add(self, video_tuple):
        self.playque.append(video_tuple)

    async def addToQ(self, ctx, video_tuple):
        self.add(video_tuple)
        added_to_q = await ctx.send(embed = Embed(title=f"{video_tuple[0]} added to queue."))
        await added_to_q.delete(delay=5.0)

    def remove(self): 
        self.playque.popleft()

    

# grabs various resources from the internet
class Grabber:
    """
    Grabber is used to grab resources from the internet.\n
    It's two methods are used to poll the YouTube API for search results given a query string,\n
    and to download a song given the youtube video ID returned by the previous method."""
    def __init__(self, bot):
        self.bot = bot
        self.downloading = False
        self.service = build('youtube', 'v3', developerKey=GOOGLE_API_KEY)
    
    async def getSearchResults(self, ctx=None, *args, maxResults=1):
        query = ""
        args = args[0]
        for arg in args:
            query += f"{arg} "

        request = self.service.search().list(
        part='snippet',
        maxResults=int(maxResults),
        q=str(query))
        try:
            response = request.execute() # response is a json object in dict format
            titles_and_ids = []
            for item in response["items"]:
                id = item["id"]["videoId"]
                title = html.unescape(item["snippet"]["title"])
                titles_and_ids.append((title, id))

            if ctx is None:
                return titles_and_ids
        except HttpError:
            print(f"\nYou have run out of requests to the YouTube API for today. Wait until the next day to get another 100 search requests.\n")

    
    def getSong(self, youtube_id, song_name):
        base_address = "https://www.youtube.com/watch?v="
        ytdl_format_options = {
            "no_playlist": True,
            # "max_downloads": 1,
            'format': 'mp3/bestaudio/best',
            "outtmpl": DATA_DIRECTORY + helper.slugify(song_name) + ".%(ext)s",  
            "ffmpeg_location": FFMPEG_PATH,
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
        self.prev_song = None
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
        # if self.playing is False:
        #     await ctx.send(f"Playing nothing right now.")
        if self.current_song is not None:
            pretty_string = ""
            pretty_string += f"Playing: {self.current_song[0]}\n\n"
            count = 1 # skip the first song in playque
            for title, id in self.playlist.playque:
                pretty_string += f"{count}: {title}\n"
                count += 1
            await ctx.send(embed = Embed(title=f"Current Queue", description=f"{pretty_string}"))
        else:
            await ctx.send(embed = Embed(title=f"No songs in queue yet."))

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

    #must take error as a parameter since "error" will be automatically passed into an "after" function
    def play_next(self, err = None):
        self.playing = False
        self.prev_song = self.current_song

        helper.clearAllAudio()
        if not self.playlist.isEmpty():
            if not self.from_skip:
                self.current_song = self.playlist.playque[0]
            self.playlist.remove()
            self.from_skip = False

            print(f"downloading song from play_next method")
            self.grabber.getSong(self.current_song[1], self.current_song[0])
            print(f"moved past download line")
            song_path = DATA_DIRECTORY + helper.slugify(str(self.current_song[0]))  + ".mp3"
            audio = discord.FFmpegPCMAudio(song_path, executable=FFMPEG_PATH)
            helper.cleanAudioFile(helper.slugify(str(self.prev_song[0])))
            if self.playing is False:
                self.playing = True
                self.voice.play(source = audio, after = self.play_next)      
        elif err:
            print(f"Error in play_next method: ", err)
            return


    def _play_song(self):
        if not self.playlist.isEmpty():
            # save first song into current song, then pop it from queue
            self.current_song = self.playlist.playque[0]
            self.playlist.remove()
            try:
                helper.clearAllAudio()
            except:
                pass
            print(f"downloading song from _play_song method")
            self.grabber.getSong(self.current_song[1], self.current_song[0])
            print(f"moved past download line")
            song_path = DATA_DIRECTORY + helper.slugify(str(self.current_song[0])) + ".mp3"
            audio = discord.FFmpegPCMAudio(song_path, executable=FFMPEG_PATH)
            if self.playing is False:
                self.playing = True
                self.voice.play(source = audio, after = self.play_next)


    @commands.command()
    async def play(self, ctx, *args) -> None:
        # check if user is in a voice channel
        if ctx.author.voice.channel is None:
            await ctx.send(embed=Embed(title=f"Please join a voice channel and try again."))
            return
        song_title_and_id = await self.grabber.getSearchResults(None, args, maxResults=1)
        await self.playlist.addToQ(ctx, song_title_and_id[0])
        # check if there's already a voice connection
        if self.voice is None:
            current_channel = ctx.author.voice.channel
            # create voice connection
            self.voice = await current_channel.connect(timeout = None)
            self._play_song()
            await self.leaveWhenDone(ctx)
        elif self.playing is False:
            self._play_song()
        else:
            return

        # song_title_and_id = await self.grabber.getSearchResults(None, args, maxResults=1)
        # await self.playlist.addToQ(ctx, song_title_and_id[0])

        # if self.voice is None:
        #     if ctx.author.voice.channel is not None:
        #         current_channel = ctx.author.voice.channel
        #         self.voice = await current_channel.connect(timeout = None)
        #         if self.playing is False:
        #             self._play_song()
        #             # only start this once, when voice client is first constructed - it continues to wait/recursively call until music stops, then it makes bot leave
        #             await self.leaveWhenDone(ctx)
        #     elif ctx.author.voice.channel is None:
        #         await ctx.send(embed=Embed(title=f"Please join a voice channel and try again."))

        # elif self.playing is False:
        #     self._play_song()

        # else:
        #     return

    @commands.command()
    async def skip(self, ctx):
        if self.current_song:
            await ctx.send(embed=Embed(title=f"Skipping {self.current_song[0]}."))
            self.voice.stop()
            self.playing = False
            self.from_skip = True
            self.current_song = None
            self._play_song()
        # need to be able to skip even if no songs are in quqeue after the current song.
        else:
            await ctx.send(embed=Embed(title=f"Queue is already empty."))
            

    @commands.command()
    async def kickBot(self, ctx):
        # check whether a voice connection exists in this guild
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            if voice.is_connected():
                if self.playing is True:
                    voice.stop()
                await voice.disconnect()
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
    
    async def leaveWhenDone(self, ctx):
        print(f"sleeping for 600 seconds before checking if voice is playing")    
        await asyncio.sleep(600.0)
        # this didn't work last time, INVESTIGATE!
        print(f"done sleeping, checking if voice client playing")
        if self.voice is not None:
            if self.voice.is_connected():
                if not self.voice.is_playing():
                    try:
                        await self.voice.disconnect()
                        await ctx.send(embed=Embed(title=f'Left voice chat due to inactivity.'))
                        self.voice = None
                        self.current_song = None
                        return
                    except Exception as e:
                        return
                elif self.voice.is_playing():
                    await self.leaveWhenDone(ctx)
            elif not self.voice.is_connected():
                print(f"self.voice is already disconnected. setting self.voice to none.")
                self.current_song = None
                self.voice = None
                return
        else:
            print(f"self.voice is already None.")
            return
        
async def setup(bot):
    await bot.add_cog(MusicController(bot, PlayList(bot)))
        