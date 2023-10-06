from config.configuration import GOOGLE_API_KEY, DATA_DIRECTORY, FFMPEG_PATH, WORKING_DIRECTORY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from cogs.controller import Controller
from collections import deque
from pathlib import Path
import asyncio
import helper
import time
import logging
import html


from spotipy import Spotify, SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError # can be thrown when max amount of youtube searches has been met/exceeded
import discord
from discord import Embed
from discord.ext import commands
from mutagen import mp3
import yt_dlp
from youtube_dl import YoutubeDL

# new music specific log
music_log_path = Path(WORKING_DIRECTORY) / "music.log"
music_handler = logging.FileHandler(music_log_path, encoding="utf-8", mode="w")
logger = logging.Logger("music_logger")
logger.addHandler(music_handler)

def getTime() -> str:
    return time.asctime(time.localtime())
 
#TODO
# backburner goal:
    # introduce database to handle all the files in 'data' folder. I think this would be a tradeoff between setup difficulty and ease of operating in the long term.
    # honestly, might not be worth it to most operators unless they are serving dozens of servers. either way, it would
    # be good practice for me. I could practice the dependency injection pattern by creating a class, ("FileManager" perhaps?) that is 
    # constructed upon booting the bot - which establishes a database client if DB url/creds are provided, otherwise handles all data in the ParkBot/data/ directory.

    # also, this would be a simple, pythonic way of doing this. I think the more safe way, which could more easily be done in something llike Java, 
    # would be to create an interface, let's call it "DataManager". then create subclasses which implement this interface, such as DBManager and FileManager.
    # then, only use calls to the DataManager interface whenever you need to work with IO operations.

    #pythonic way - the 'interface' would be a DataManager class which defines each method(including its parameters and return type), but doesn't implement them (passing on each method).
    # let classes that want to implement this interface just extend the DataManager class

#TODO
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
        self.path = str(Path(DATA_DIRECTORY) / self.slug_title)

    def setDownloaded(self) -> None:
        self.downloaded = True

    def isEmpty(self) -> bool:
        """Checks whether the Song contains any data or if its a ghost."""
        if self.id or self.title is None:
            return True
        return False

class PlayList(commands.Cog):
    def __init__(self, bot, guild:discord.Guild):
        self.guild = guild
        self.bot = bot
        self.current_song:Song = None 
        self.prev_song:Song = None
        self.playque:deque[Song] = deque()
        self.playhistory = deque(maxlen=5)

    def isEmpty(self) -> bool:
        return len(self.playque) == 0
    
    def add(self, song:Song) -> None:
        self.playque.append(song)

    async def _showQ(self, ctx) -> None:
        # if self.playing is False:
        #     await ctx.send(f"Playing nothing right now.")
        if self.current_song is not None:
            pretty_string = ""
            pretty_string += f"Playing: {self.current_song.title}\n\n"
            count = 1 # skip the first song in playque
            for song in self.playque:
                pretty_string += f"{count}: {song.title}\n"
                count += 1
            await ctx.send(embed = Embed(title=f"Current Queue", description=f"{pretty_string}"))
        else:
            await ctx.send(embed = Embed(title=f"No songs in queue yet."))

    async def _showHistory(self, ctx) -> None:
        if len(self.playhistory) > 0:
            pretty_string = ""
            pretty_string += f"Playing: {self.current_song.title}\n"
            playhistory = self.playhistory.copy()
            playhistory.pop() # copy current playhistory, leaving popping off the most recent edition (the current song)
            playhistory_with_index = enumerate(self.playhistory, start=1)
            for index, song in playhistory_with_index: # skip first song in playhistory as this is the current song
                pretty_string += f"{index}: {song.title}\n"
            await ctx.send(embed = Embed(title=f"Recently Played", description=f"{pretty_string}"))
        else:
            await ctx.send(embed = Embed(title=f"No songs have been played yet."))

    async def addToQ(self, ctx, song:Song) -> None:
        """Adds a song to the playque + sends a confirmation message to text chat."""
        self.add(song)
        await ctx.send(embed = Embed(title=f"{song.title} added to queue."))
        return

    def pop(self) -> Song: 
        """Pops the oldest song off the queue, and adds that song to the playhistory queue."""
        removed = self.playque.popleft()
        self.playhistory.append(removed)
        return removed

    def remove(self, song:Song) -> None:
        self.playque.remove(song)

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
    
class SpotifyClient:
    def __init__(self, client_id, client_secret):
        self.auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = Spotify(auth_manager=self.auth_manager)

    def getSpotifySongId(self, song_title:str) -> str | None:
        """Searches for an input song query, and returns the Spotify song ID of the search's first result."""
        id = None
        try:
            results = self.sp.search(q=song_title, type="track")
            first_track = results["tracks"]['items'][0]
            id = first_track['id']
        except SpotifyException as e:
            raise Exception("Error accessing the spotify API. Returning None.")
        # album = first_track["album"]
        # artists = first_track["artists"]
        return id
    
    def getSongRecommendations(self, spotify_song_id:str) -> list[tuple[str, list[str]]] | None:
        """Grabs songs recommendations from spotify based on an input song. Returns 3 recommendations by default.\nList format: [(song_name, [song_author1, song_author2]), (song2_name, [song_author1])]"""
        songs_to_artists = []
        try:
            recommendations = self.sp.recommendations(seed_tracks=[spotify_song_id], limit=3)
            for track in recommendations["tracks"]:
                songs_to_artists.append((track['name'], [artist['name'] for artist in track['artists']]))
        except SpotifyException as e:
            raise Exception("Error accessing spotify API. Returning None.")
        return songs_to_artists 

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
                logger.error(f"{getTime()}: {err_message}")

    async def getSearchResultsWithString(self, query:str, maxResults=1) -> list[tuple[str, str]] | None:
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

            return titles_and_ids
        except HttpError as e:
            err_message = f"You have run out of requests to the YouTube API for today. Wait until the next day to get another 100 search requests. Error: {e}"
            logger.error(f"{getTime()}: {err_message}")

    
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
            "outtmpl": str(Path(DATA_DIRECTORY) / (helper.slugify(title) + ".%(ext)s")),  
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


class Player(commands.Cog):
    """Class that performs logic pertaining to playing or skipping songs. Constructed with a PlayList and YoutubeClient."""
    def __init__(self, bot, playlist:PlayList, ytclient: YoutubeClient, spotifyclient: SpotifyClient):
        self.playing = False
        self.from_skip = False
        self.bot = bot
        self.playlist = playlist
        self.ytclient = ytclient
        self.spclient = spotifyclient
        self.voice = None

        self.autoplay = False

    def play_next(self, err = None):
        # self.from_skip = False
        logger.debug(f"{getTime()}: play_next method executing")
        playlist = self.playlist
        self.playing = False
        playlist.prev_song = playlist.current_song
        song_titles_to_save = [song.slug_title for song in playlist.playque] + [playlist.current_song.slug_title]
        helper.deleteSongsBesidesThese(song_titles_to_save)
        logger.info(f"{time.asctime(time.localtime())}: ParkBot deleted songs besides those in this list, {song_titles_to_save}")
        #TODO review this `from skip` logic
        if not playlist.isEmpty():
            if not self.from_skip: # if coming from a skip, don't iterate current song to the next song. if coming from a skip, I want to negate this call to play_next
                playlist.current_song = playlist.playque[0]
            playlist.playque.popleft()
            self.from_skip = False
            # if autoplay is True, search and add antoher song to the queue
            next_song = playlist.getNextSong()
            # download next song if its not downloaded
            if (next_song is not None) and (next_song.downloaded is False):
                try: 
                    self.ytclient.downloadSong(next_song)
                except yt_dlp.utils.DownloadError:
                    logger.error(f"{getTime()}: The video you wanted to download was too large. Deleting this song from the queue.")
                    playlist.remove(next_song)
                    helper.cleanupSong(next_song.slug_title)
            # otherwise, pre download a song ahead in the queue after a song is playing
            audio = discord.FFmpegPCMAudio(playlist.current_song.path, executable=FFMPEG_PATH)
            if self.playing is False:
                self.playing = True
                self.voice.play(source = audio, after = self.play_next)
                # check if num of downloaded songs is < 4, if so then download the next undownloaded song.
                preload_song = playlist.getNextUndownloadedSong()
                if preload_song is not None:
                    try:
                        self.ytclient.downloadSong(preload_song)
                    except yt_dlp.utils.DownloadError:
                        logger.error(f"{time.asctime(time.localtime())}: Error preloading the next undownloaded song in play_next method")
                        helper.cleanupSong(preload_song.slug_title)
        elif err:
            logger.error(f"{getTime()}: Error in play_next method: {err}" )
            return
        
    def _play_song(self):
        # print(f"***starting _play_song method")
        playlist = self.playlist

        if not playlist.isEmpty():
            logger.debug(f"{getTime()}: Playlist is not empty so continuing _play_song method.")
            logger.debug(f"{getTime()}: Playlist is not empty! Contents: {[song.title for song in playlist.playque]}")
            if self.voice.is_playing():
                logger.debug(f"{getTime()}: Voice is already playing, so returning early.")
                return
            playlist.current_song = playlist.playque[0]
            logger.debug(f"{getTime()}: _play_song iterating current_song to {playlist.playque[0].title}.")
            logger.debug(f"{getTime()}: Current playlist: {[song.title for song in playlist.playque]}")

            next_song = playlist.getNextUndownloadedSong()
            if (next_song is not None) and (next_song.downloaded is False):
                logger.debug(f"{getTime()}: _play_song attempting to download the next song in queue, {next_song.title}")
                try: 
                    self.ytclient.downloadSong(next_song) # does this remove song from the queue?
                except yt_dlp.utils.DownloadError:
                    logger.error(f"{getTime()}: The video you wanted to download was too large. Deleting this song from the queue.")
                    playlist.remove(next_song)
                    logger.error(f"{getTime()}: Removed {next_song.title} from playlist due to a YT Download error.")
                    helper.cleanupSong(next_song.slug_title)
            
            # if coming from a skip, don't pop the left song.
            bye = playlist.playque.popleft()
            logger.debug(f"{getTime()}: _play_song popping left song off the playque, {bye.title}.")
            song_titles_to_save = [song.slug_title for song in playlist.playque] + [playlist.current_song.slug_title]
            playlist.playhistory.append(playlist.current_song)

            try:
                helper.deleteSongsBesidesThese(song_titles_to_save)
                logger.info(f"{time.asctime(time.localtime())}: ParkBot deleted all songs besides those in this list, {song_titles_to_save}")
            except:
                pass
            # print(f"Loading current song from this path: {playlist.current_song.path}")
            audio = discord.FFmpegPCMAudio(playlist.current_song.path, executable=FFMPEG_PATH)
            if audio is not None:
                logger.debug(f"{getTime()}: _play_song successfully created a discord compatible audio from {playlist.current_song.title}")
            else:
                logger.debug(f"{getTime()}: _play_song failed to create a discord compatible audio from {playlist.current_song.title}")
            if self.playing is False:
                self.playing = True
                logger.debug(f"{getTime()}: _play_song attempting to voice.play current song.")
                self.voice.play(source = audio, after = self.play_next)

     
    async def _autoplay(self, ctx, *args) -> None:
        """A variation of `_play()` that is called when the `autoplay` flag is true.\nQueries spotify for songs recommended to the user's input query, and adds the top 3 to the playque."""
        self.autoplay = False
        playlist = self.playlist
        new_song = Song()
        if ctx.author.voice is None:
            await ctx.send(embed=Embed(title=f"Please join a voice channel and try again."))
            return
        song_titles_and_ids = await self.ytclient.getSearchResults(None, args, maxResults=1)
        if song_titles_and_ids is None:
            await ctx.send(embed=Embed(title=f"Search Error", description=f"There was an issue with the results of the search for your song. Please try again, but change your search term slightly."))
            return
        else:
            if self.voice is not None:
                if not self.voice.is_playing():
                    await self.voice.disconnect()
                    user_channel = ctx.author.voice.channel
                    self.voice = await user_channel.connect(timeout = None)
                else:
                    pass

            elif (self.voice is None):
                user_channel = ctx.author.voice.channel
                # create voice connection
                self.voice = await user_channel.connect(timeout = None)
            

            new_song.setData(song_titles_and_ids[0])
            await playlist.addToQ(ctx, new_song)
            if len(playlist.playque) < 4: # download up to 3 songs ahead of time
                try:
                    self.ytclient.downloadSong(new_song)
                    logger.info(f"{time.asctime(time.localtime())}: ParkBot {ctx.guild} instance downloaded a song - {new_song.title}")
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f"{time.asctime(time.localtime())}: ParkBot {ctx.guild} instance had a download Error - {e}", exc_info=True, stack_info=True)
                    await ctx.send(embed=Embed(title="Download Error", description=f"{e}"))
                    playlist.remove(new_song) # removes the song without adding it to playhistory, since it wasn't played
                    helper.cleanupSong(new_song.slug_title)
        
            # play song if music isnt already playing
            if not self.voice.is_playing():
                self._play_song()

            # now, check if we should autoplay, and attempt to query spotify to add more songs to queue
            if (len(playlist.playque) < 7):
                logger.debug(f"{getTime()}: _autoplay attempting to download autoplay stuff")
                # add 3 related songs to the playque
                id = self.spclient.getSpotifySongId(new_song.title)
                if id is not None:
                    autoplay_songs = self.spclient.getSongRecommendations(id)
                    if autoplay_songs is not None:
                        for title_and_artist in autoplay_songs:
                            print(title_and_artist)
                            title = title_and_artist[0]
                            artist = title_and_artist[1][0]
                            query_string = f"{title} {artist}"
                            song = Song()
                            yt_song_title_and_id = await self.ytclient.getSearchResultsWithString(query_string)
                            song.setData(yt_song_title_and_id[0])
                            playlist.add(song)

                    # pre-download a song
                    if len(playlist.playque) < 4:
                        try:
                            autoplay_song = playlist.getNextUndownloadedSong()
                            self.ytclient.downloadSong(autoplay_song)
                            logger.info(f"{time.asctime(time.localtime())}: ParkBot {ctx.guild} instance downloaded a song - {autoplay_song.title}")
                        except yt_dlp.utils.DownloadError as e:
                            logger.error(f"{time.asctime(time.localtime())}: ParkBot {ctx.guild} instance had a download Error - {e}", exc_info=True, stack_info=True)
                            await ctx.send(embed=Embed(title="Download Error", description=f"{e}"))
                            playlist.remove(autoplay_song) # removes the song without adding it to playhistory, since it wasn't played
                            helper.cleanupSong(autoplay_song.slug_title)
                await ctx.send(embed=Embed(title=f"Up Next", description=f"{playlist.playque[0].title}\n"))
            return
            

    async def test_play(self, ctx, *args) -> None:
        pass
      
      
    async def _play(self, ctx, *args) -> None:
        playlist = self.playlist
        new_song = Song()
        # check if user is in a voice channel
        if ctx.author.voice is None:
            await ctx.send(embed=Embed(title=f"Please join a voice channel and try again."))
            return
        song_titles_and_ids = await self.ytclient.getSearchResults(None, args, maxResults=1)
        if song_titles_and_ids is None:
            await ctx.send(embed=Embed(title=f"Search Error", description=f"There was an issue with the results of the search for your song. Please try again, but change your search term slightly."))
            return
        else:
            if self.voice is not None:
                if not self.voice.is_playing():
                    await self.voice.disconnect()
                    user_channel = ctx.author.voice.channel
                    self.voice = await user_channel.connect(timeout = None)
                else:
                    pass

            elif (self.voice is None):
                user_channel = ctx.author.voice.channel
                # create voice connection
                self.voice = await user_channel.connect(timeout = None)

            new_song.setData(song_titles_and_ids[0])
            # make this check in each of the play functions.
            await playlist.addToQ(ctx, new_song)
            if len(playlist.playque) < 4: # download up to 3 songs ahead of time
                try:
                    self.ytclient.downloadSong(new_song)
                    logger.info(f"{time.asctime(time.localtime())}: ParkBot {ctx.guild} instance downloaded a song - {new_song.title}")
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f"{time.asctime(time.localtime())}: ParkBot {ctx.guild} instance had a download Error - {e}", exc_info=True, stack_info=True)
                    await ctx.send(embed=Embed(title="Download Error", description=f"{e}"))
                    playlist.remove(new_song) # removes the song without adding it to playhistory, since it wasn't played
                    helper.cleanupSong(new_song.slug_title)
            # check if there's already a voice connection

            if not self.voice.is_playing():
                self._play_song()
                await self.leaveWhenDone(ctx)

            else:
                return
    
    #TODO skip is deleting a song after the next song
    async def _skip(self, ctx):
        playlist = self.playlist
        current_song = playlist.current_song
        if current_song is not None:
            logger.info(f"{getTime()}: Skipping {current_song.title}")
            await ctx.send(embed=Embed(title=f"Skipping {current_song.title}."))
            self.voice.stop()
            self.playing = False
            self.from_skip = True
            playlist.playhistory.append(current_song)
            playlist.current_song = None
            logger.debug(f"{getTime()}: _skip calling _play_song().")
            self._play_song()
        # need to be able to skip even if no songs are in queue after the current song.
        else:
            await ctx.send(embed=Embed(title=f"Queue is already empty."))

    async def leaveWhenDone(self, ctx):
        playlist = self.playlist

        print(f"sleeping for 600 seconds before checking if voice is playing")    
        await asyncio.sleep(600.0)
        # this didn't work last time, INVESTIGATE!
        print(f"done sleeping, checking if voice client playing")
        # message = await ctx.send(f"checking if voice client playing")
        # await message.delete(delay=7.0)
        if self.voice is not None:
            if self.voice.is_connected():
                # get the voice channel it's connected to and check the amount of users in the voice channel.
                if not self.voice.is_playing(): # or if len(users in channel) < 2:
                    try:
                        await self.voice.disconnect()
                        await ctx.send(embed=Embed(title=f'Left voice chat due to inactivity.'))
                        self.voice = None
                        playlist.current_song = None
                        self.autoplay = False
                        return
                    except Exception as e:
                        error_message = await ctx.send(f"Bot was cleared to leave the voice channel, however It was unable to execute this action. Exception: {e}")
                        logger.error(error_message, exc_info=True)
                        await error_message.delete(delay=7.0)
                        return
                elif self.voice.is_playing():
                    await self.leaveWhenDone(ctx)
            elif not self.voice.is_connected():
                print(f"self.voice is already disconnected. setting self.voice to none.")
                playlist.current_song = None
                self.voice = None
                self.autoplay = False
                return
        else:
            print(f"self.voice is already None.")
            return

class MusicController(Controller):
    """Class that has top-level control of playing music. The MusicController constructs a PlayList, YoutubeClient,\n
    and Player for each guild the ParkBot is a part of. The `play` and `skip` commands access the appropriate Player instance,\n
    then execute the lower level `_play` or `_skip` commands on the instance. In other words, the MusicController directs users' commands
    to their guild's instance of the ParkBot."""

    def __init__(self, bot):
        logger.info(f"{time.asctime(time.localtime())}: MusicController constructed.")
        super().__init__(bot, PlayList)
        #self.guilds_to_clazzs:dict[discord.Guild, PlayList] - this exists but isnt explicit here
        self.players:dict[PlayList, Player] = {playlist: Player(self.bot, playlist, YoutubeClient(self.bot), SpotifyClient(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)) for playlist in self.guilds_to_clazzs.values()}
        self.client = YoutubeClient(bot)

    @commands.command()
    async def showGuilds(self, ctx):
        guilds = self.bot.guilds
        string = ""
        for guild in guilds:
            string += f"{guild.name}, "
        await ctx.send(embed=Embed(title="Guilds", description=string))

    @commands.command()
    async def showQ(self, ctx):
        """Gets the playlist associated with the caller's guild, and shows it in a text channel."""
        playlist:PlayList = self.getGuildClazz(ctx)
        await playlist._showQ(ctx)

    @commands.command()
    async def showHistory(self, ctx):
        playlist:PlayList = self.getGuildClazz(ctx)
        await playlist._showHistory(ctx)

    @commands.command()
    async def currentSong(self, ctx):
        playlist:PlayList = self.getGuildClazz(ctx)
        await ctx.send(embed=Embed(title=f"Current Song", description=f"{playlist.current_song.title}"))


    #NOTE - I want to continue experimenting with this later down the line -
    #seems there's some way to play songs without downloading ? not sure
    # async def playURL(self, ctx, url):
    #     author_vc = ctx.author.voice.channel
    #     if not self.voice:
    #         self.voice = await author_vc.connect()
        
    #     with YoutubeDL() as ydl:
    #         info = ydl.extract_info(url, download=False)
    #         audio_url = info['formats'][0]['url']
    #         self.voice.play(discord.FFmpegPCMAudio(audio_url))
 
    @commands.command()
    async def play(self, ctx, *args) -> None:
        """Accesses a guild's Player and attempts to play a song through it."""
        playlist = self.getGuildClazz(ctx)
        player = self.players[playlist]
        if player.autoplay is True:
            await player._autoplay(ctx, args)
        else:
            await player._play(ctx, args)

    @commands.command()
    async def autoplay(self, ctx, *args) -> None:
        """Command used to check or set the status of a Player's autoplay flag."""
        playlist = self.getGuildClazz(ctx)
        player = self.players[playlist]
        if args is None:
            await ctx.send(embed=Embed(title=f"Please type an argument after `autoplay`, such as `on`, or `off`."))
            return
        string = str(args[0])
        if isinstance(string, str):
            match string:
                case "on" | "true" | "yes":
                    new_bool = True
                case "off" | "false" | "no":
                    new_bool = False
                case _:
                    new_bool = player.autoplay
            if player.autoplay != new_bool: # if autoplay is being changed, tell the users
                await ctx.send(embed=Embed(title=f"Music autoplay set to {new_bool}."))
            else:
                await ctx.send(embed=Embed(title=f"Music autoplay is currently: {player.autoplay}."))
            player.autoplay = new_bool
        else:
            await ctx.send(embed=Embed(title=f"Invalid Argument", description=f"Please try again, using something like `yes`, `on`, `off`, or `no`."))
        

    @commands.command()
    async def skip(self, ctx):
        playlist = self.getGuildClazz(ctx)
        player = self.players[playlist]
        await player._skip(ctx)
            
    @commands.command()
    async def kickBot(self, ctx):
        # check whether a voice connection exists in this guild, and terminate it if so
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            if voice.is_connected():
                if voice.is_playing():
                    voice.stop()
                await voice.disconnect()
        #TODO need to modify the self.voice and self.playing attributes of whatever guild's player we just terminated


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
    
    await bot.add_cog(MusicController(bot))
        