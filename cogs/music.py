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

# suggestion for easier debugging -
    # obtain the bot's voice attribute during the voice methods to keep it in stack. makes debugging easier and would prevent a null voice client value. 

# need to :
    # handle errors within music cog - make them throw messages to the discord chat when possible.

# requested feature: autoplay suggested videos/songs -
    # could extract tags from the video I'm on and perform a search of those tags, return first video
    # users can turn on / turn off autoplay (off by default)
        # when autoplay is turned off, next 5 songs in queue will stay, anything after will be cleared

# planned feature : auto download next queued song - will have to fix the deletion to not delete every .mp3; instead to only delete the selected song

# planned feature : implement a Song class that contains a song's request name, slugified path, slugified title. 
    # would make it easier to pre-load songs and delete them when necessary

# planned feature : implement multithreading module so that music class can download / play simaltaneously 

# planned feature : ability to play songs from URls (youtube, spotify, soundcloud) could pretty easily play spotify stuff. their API seems not bad
class Song:
    def __init__(self, song_title_and_id:tuple):
        self.title = song_title_and_id[0]
        self.id = song_title_and_id[1]
        self.slug_title = helper.slugify(self.title)
        self.path:str = DATA_DIRECTORY + self.slug_title + ".mp3"


class PlayList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playque = deque()
        self.playhistory = deque(maxlen=5)

    def isEmpty(self):
        return len(self.playque) == 0
    
    def add(self, song:Song):
        self.playque.append(song)

    async def addToQ(self, ctx, song:Song):
        self.add(song)
        added_to_q = await ctx.send(embed = Embed(title=f"{song.title} added to queue."))
        await added_to_q.delete(delay=5.0)

    def remove(self): 
        self.playque.popleft()

    

class YoutubeClient:
    """
    The YoutubeClient is used to grab resources from youtube, using both the youtube API and ytdl.\n
    It's two methods are used to poll the YouTube API for search results given a query string,\n
    and to download a song given the youtube video ID returned by the previous method."""
    def __init__(self, bot):
        self.bot = bot
        self.downloading = False
        self.service = build('youtube', 'v3', developerKey=GOOGLE_API_KEY)
    
    async def getSearchResults(self, ctx=None, *args, maxResults=1) -> list[tuple[str, str]] | None:
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
        except HttpError as e:
            err_message = f"You have run out of requests to the YouTube API for today. Wait until the next day to get another 100 search requests. Error: {e}"
            if ctx:
                await ctx.send(err_message)
            else:
                print(err_message + "\n")

    
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
        self.current_song:Song = None
        self.client = YoutubeClient(bot)
        self.voice = None
        self.playing = False
        self.from_skip = False

    @commands.command()
    async def showQ(self, ctx):
        # if self.playing is False:
        #     await ctx.send(f"Playing nothing right now.")
        if self.current_song is not None:
            pretty_string = ""
            pretty_string += f"Playing: {self.current_song.title}\n\n"
            count = 1 # skip the first song in playque
            for song in self.playlist.playque:
                pretty_string += f"{count}: {song.title}\n"
                count += 1
            await ctx.send(embed = Embed(title=f"Current Queue", description=f"{pretty_string}"))
        else:
            await ctx.send(embed = Embed(title=f"No songs in queue yet."))

    @commands.command()
    async def currentSong(self, ctx):
        await ctx.send(embed=Embed(title=f"Current Song", description=f"{self.current_song.title}"))

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
            self.client.getSong(self.current_song.id, self.current_song.title)
            print(f"moved past download line")
            audio = discord.FFmpegPCMAudio(self.current_song.path, executable=FFMPEG_PATH)
            helper.cleanAudioFile(helper.slugify(str(self.prev_song.title)))
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
            self.client.getSong(self.current_song.id, self.current_song.title)
            print(f"moved past download line")
            audio = discord.FFmpegPCMAudio(self.current_song.path, executable=FFMPEG_PATH)
            if self.playing is False:
                self.playing = True
                self.voice.play(source = audio, after = self.play_next)


    @commands.command()
    async def play(self, ctx, *args) -> None:
        # check if user is in a voice channel
        if ctx.author.voice.channel is None:
            await ctx.send(embed=Embed(title=f"Please join a voice channel and try again."))
            return
        song_title_and_id = await self.client.getSearchResults(None, args, maxResults=1)
        await self.playlist.addToQ(ctx, Song(song_title_and_id[0]))
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

    @commands.command()
    async def skip(self, ctx):
        if self.current_song:
            await ctx.send(embed=Embed(title=f"Skipping {self.current_song.title}."))
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
        # message = await ctx.send(f"checking if voice client playing")
        # await message.delete(delay=7.0)
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
                        error_message = await ctx.send(f"Bot was cleared to leave the voice channel, however It was unable to execute this action. Exception: {e}")
                        await error_message.delete(delay=7.0)
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
        