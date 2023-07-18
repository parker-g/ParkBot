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

# current goal:
    # in the MusicController, change references to current_song = None, to current_song = Song(). then, instead of checking whether current_song is None, check if current_song.isEmpty().
        # this will ensure current_song is a more consistent type across the board, instead of letting it vary from None to Song. im assuming this is better practice since the type checker is trying to enforce it.
    # refactor cogs (starting with music) to allow bot to serve all cogs to more than one server at one time. (user story: I can use ParkBot music feature simaltaneously from two different discord servers.)

# requested feature: autoplay suggested videos/songs -
    # could extract tags from the video I'm on and perform a search of those tags, return first video
    # users can turn on / turn off autoplay (off by default)
        # when autoplay is turned off, next 5 songs in queue will stay, anything after will be cleared


# planned feature : ability to play songs from URls (youtube, spotify, soundcloud) could pretty easily play spotify stuff. their API seems not bad. I think doing this would require me to provide my spotify login tho. and spotify limits to listening on one device so i dont like this idea.
class Song:
    def __init__(self):
        self.played = False
        self.title = None
        self.id = None
        self.slug_title = None
        self.path = None
        self.downloaded = False


    def setData(self, song_title_and_id:tuple) -> None:
        """Pass a tuple of (a video's title, and YouTube ID) as the argument to this method. The Song's title, ID, and path will be set accordingly to this input.\n
        Meant to take the result of the `YoutubeClient.getSearchResults()` method, as an argument."""
        self.title = song_title_and_id[0]
        self.id = song_title_and_id[1]
        self.slug_title = helper.slugify(self.title) + ".mp3"
        self.path = DATA_DIRECTORY + self.slug_title

    def setDownloaded(self) -> None:
        self.downloaded = True

    def isEmpty(self) -> bool:
        """Checks whether the Song contains any data or if its a ghost."""
        if self.id or self.title is None:
            return True
        return False

class PlayList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playque:deque[Song] = deque()
        self.playhistory = deque(maxlen=5)

    def isEmpty(self) -> bool:
        return len(self.playque) == 0
    
    def add(self, song:Song) -> None:
        self.playque.append(song)

    async def addToQ(self, ctx, song:Song) -> None:
        """Adds a song to the playque + sends a confirmation message to text chat."""
        self.add(song)
        await ctx.send(embed = Embed(title=f"{song.title} added to queue."))
        return

    def pop(self) -> None: 
        """Pops the most recently played song off the queue, and adds that song to the playhistory queue."""
        removed = self.playque.popleft()
        self.playhistory.append(removed)

    def getNextSong(self) -> Song | None:
        """Returns the next song in the queue, None if next song doesn't exist."""
        try: 
            return self.playque[1]
        except IndexError:
            return None
    
    def getNextUndownloadedSong(self) -> Song | None:
        queue = self.playque
        count = 0
        while count < len(queue):
            song = queue[count]
            if song.downloaded is False:
                return song
            count += 1
        return None
    
    def getNumDownloadedSongs(self) -> int:
        count = 0
        for song in self.playque:
            if song.downloaded is True:
                count += 1
        return count

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

    
    def downloadSong(self, song:Song):
        id = str(song.id)
        title = song.title
        base_address = "https://www.youtube.com/watch?v="
        ytdl_format_options = {
            # add an option to limit download size to maybe 20 mb
            "max_filesize": 10000000, # I think this is bytes, so this should be around 10mb (10 mil)
            "no_playlist": True,
            # "max_downloads": 1,
            'format': 'mp3/bestaudio/best',
            "outtmpl": DATA_DIRECTORY + helper.slugify(title) + ".%(ext)s",  
            "ffmpeg_location": FFMPEG_PATH,
            # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        }

        youtube_url = [base_address + id]
        
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            ydl.download(youtube_url)

        song.setDownloaded()
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
    async def showHistory(self, ctx):
        if len(self.playlist.playhistory) > 1:
            pretty_string = ""
            pretty_string += f"Playing: {self.current_song.title}\n\n"
            count = 1 # skip the first song in playque
            for song in self.playlist.playhistory:
                pretty_string += f"{count}: {song.title}\n"
                count += 1
            await ctx.send(embed = Embed(title=f"Recently Played", description=f"{pretty_string}"))
        else:
            await ctx.send(embed = Embed(title=f"No songs have been played yet."))

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
        songs_to_save = [song.slug_title for song in self.playlist.playque]

        helper.deleteSongsBesidesThese(songs_to_save)
        if not self.playlist.isEmpty():
            if not self.from_skip:
                self.current_song = self.playlist.playque[0]
            self.playlist.pop()
            self.from_skip = False
            next_song = self.playlist.getNextSong()
            # download next song if its not downloaded
            if (next_song is not None) and (next_song.downloaded is False):
                try: 
                    self.client.downloadSong(next_song)
                except yt_dlp.utils.DownloadError:
                    print(f"The video you wanted to download was too large. Deleting this song from the queue.")
                    self.playlist.playque.remove(next_song)
            # otherwise, pre download a song ahead in the queue after a song is playing
            audio = discord.FFmpegPCMAudio(self.current_song.path, executable=FFMPEG_PATH)
            if self.playing is False:
                self.playing = True
                self.voice.play(source = audio, after = self.play_next)
                # check if num of downloaded songs is < 4, if so then download the next undownloaded song.
                preload_song = self.playlist.getNextUndownloadedSong()
                if preload_song is not None:
                    self.client.downloadSong(preload_song)

        elif err:
            print(f"Error in play_next method: ", err)
            return


    def _play_song(self):
        if not self.playlist.isEmpty():
            self.current_song = self.playlist.playque[0]
            self.playlist.pop()
            songs_to_save = [song.slug_title for song in self.playlist.playque] + [self.current_song.slug_title]
            try:
                helper.deleteSongsBesidesThese(songs_to_save)
            except:
                pass
            # print(f"downloading song from _play_song method")
            # self.client.getSong(self.current_song.id, self.current_song.title)
            # print(f"moved past download line")
            audio = discord.FFmpegPCMAudio(self.current_song.path, executable=FFMPEG_PATH)
            if self.playing is False:
                self.playing = True
                self.voice.play(source = audio, after = self.play_next)


    @commands.command()
    async def play(self, ctx, *args) -> None:
        new_song = Song()
        # check if user is in a voice channel
        if ctx.author.voice is None:
            await ctx.send(embed=Embed(title=f"Please join a voice channel and try again."))
            return
        song_titles_and_ids = await self.client.getSearchResults(None, args, maxResults=1)
        if song_titles_and_ids is None:
            await ctx.send(embed=Embed(title=f"Search Error", description=f"There was an issue with the results of the search for your song. Please try again, but change your search term slightly."))
            return
        else:
            new_song.setData(song_titles_and_ids[0])
            # make this check in each of the play functions.
            await self.playlist.addToQ(ctx, new_song)
            if len(self.playlist.playque) < 4: # download up to 3 songs ahead of time
                try: 
                    self.client.downloadSong(new_song)
                except yt_dlp.utils.DownloadError as e:
                    await ctx.send(embed=Embed(title="Download Error", description=f"The video you requested was too large. Please try a different one.\nRemoving this video from the queue - {new_song.title}."))
                    self.playlist.playque.remove(new_song) # removes the song without adding it to eh playhistory, since it wasn't played
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
        