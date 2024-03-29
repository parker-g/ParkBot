import logging
import asyncio
import datetime
from pathlib import Path

import discord
import wavelink
from discord import Embed
from discord import Colour
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import ExtensionFailed
from wavelink import Player, AutoPlayMode, TrackSource, LavalinkLoadException

from config.configuration import LAVALINK_URI, LAVALINK_PASS, WORKING_DIRECTORY

music_log_path = Path(WORKING_DIRECTORY) / "music.log"
music_handler = logging.FileHandler(music_log_path, encoding="utf-8", mode="w")
formatter = logging.Formatter('[%(asctime)s - %(levelname)s] - %(message)s')
music_handler.setFormatter(formatter)
logger = logging.Logger("music_logger")
logger.addHandler(music_handler)

class StreamingCog(Cog):


    def __init__(self, bot):
        self.bot = bot
        self.node = None

    @staticmethod
    def parse_seconds(time:str) -> int:
        total = 0
        if ":" in time:
            mins = int(time.split(":")[0]) * 60
            seconds = int(time.split(":")[1])
            total = mins + seconds
        else:
            total = int(time)
        return total * 1000 # seconds to milliseconds conversion

    @staticmethod
    def stringify_args(args:tuple) -> str:
        query = ""
        for arg in args[:-1]:
            #NOTE consider html escaping each character in the query
            query += f"{arg} "
        query += f"{args[-1]}"
        return query

    #TODO need to find how to clean this up and handle it accordingly when it fails
    async def cog_load(self) -> None:
        """Called when the bot loads this cog - sets up a connection to the lavalink server. Only necessary to do so once; a single node can serve multiple guilds at once."""
        if self.node is None:
            try:
                node = wavelink.Node(uri=LAVALINK_URI, password=LAVALINK_PASS, retries=10)
            except ExtensionFailed:
                logger.error(f"Error connecting to lavalink server.")
                return
            nodes = await wavelink.Pool.connect(client=self.bot, nodes=[node])
            await asyncio.sleep(3.0)
            if nodes:
                self.node = self.getNode()
                logger.info(f"Node created + connected to lavalink server.")
            else:
                logger.error(f"Node created but couldn't establish connection to lavalink server.")
        elif self.node is not None:
            logger.info(f"A node connection has already been established.")

    # @commands.command()
    # async def showNode(self, ctx) -> None:
    #     node = self.getNode()
    #     if node is None:
    #         await ctx.send(embed=Embed(title=f"ParkBot not currently connected to a lavalink node.", color=Colour.light_embed()), silent=True)
    #     else:
    #         await ctx.send(embed=Embed(title=f"Node connected!: {node.identifier}", color=Colour.light_embed()), silent=True)
        
    # @commands.command("nodePlayers")
    # async def getNodePlayers(self, ctx) -> dict[int, Player]:
    #     node = wavelink.Pool.get_node()
    #     await ctx.send(f"Here are your node's players: {node.players}", silent=True)
    #     return node.players

    @commands.command()
    async def createNode(self, ctx) -> None:
        if self.node is not None:
            logger.info(f"A node is already established and connected with ID: {self.node.identifier}")
        else:
            logger.info("Connecting to lavalink node.")
            node = wavelink.Node(uri=LAVALINK_URI, password=LAVALINK_PASS)
            nodes = await wavelink.Pool.connect(nodes=[node], client=self.bot)
            if nodes:
                self.node = self.getNode()
            else:
                logger.error(f"Error connecting to Lavalink Node")
        return

    #NOTE dont even need to explicitly get a node really, it seems the methods that require a node automatically grab one from the Pool
    def getNode(self) -> wavelink.Node:
        node = wavelink.Pool.get_node()
        return node
    
    @commands.command("skip")
    async def skip(self, ctx) -> None:
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None:
            await ctx.send(embed=Embed(title=f"There is currently no active Player to play songs.", color=Colour.brand_red()))
        else:
            if player.connected:
                if player.playing: #or len(player.queue) > 0:
                    current_song = player.current
                    if current_song is None: return
                    await ctx.send(embed=Embed(title=f"Skipping {current_song.title}", color=Colour.blue()), silent=True)
                    await player.stop(force=True) # automatically forces next song to play if a next one exists
                else:
                    await ctx.send(embed=Embed(title=f"There's no song playing right now, or the queue is empty.", color=Colour.brand_red()), silent=True)
            else:
                await ctx.send(embed=Embed(title="No voice channel connection right now.", description="Can't skip a song.", color=Colour.brand_red()), silent=True)
    
    @commands.command()
    async def pause(self, ctx) -> None:
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None: 
            await ctx.send(embed=Embed(title=f"There is currently no active Player.", color=Colour.brand_red()), silent=True)
        else:
            if player.connected:
                if player.playing:
                    await player.pause(True)
                    await ctx.send(embed=Embed(title=f"{player.current.title} paused.", description=f"Use `resume` to resume.", color=Colour.light_grey()), silent=True)

    @commands.command("resume")
    async def resume(self, ctx) -> None:
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None:
            await ctx.send(embed=Embed(title=f"There is currently no active Player."), silent=True)
        else:
            if player.connected:
                if player.paused:
                    await player.pause(False)
                else:
                    await ctx.send(embed=Embed(title=f"Player is not paused.", ), silent=True)

    async def search_with_retry(self, ctx, query:str, attempts = 1):
        """Method uses lavalink to search for a user's query, taking up to 3 retries to search again if lavalink throws an error."""
        tracks = None
        try:
            tracks = await wavelink.Playable.search(str(query), source = TrackSource.YouTube)
        except LavalinkLoadException as e:
            logger.warn(f"Lavalink encountered an error while requesting '{query}'. Retrying search, attempt number {attempts}. Detailed exception - {e}")
            if attempts < 3:
                await asyncio.sleep(1)
                return await self.search_with_retry(ctx, query, attempts + 1)
            else:
                await ctx.send(embed=Embed(
                    title=f"Lavalink encountered an error while searching for your request", 
                    description=f"Please try again.",
                    # description=f"Cause: {e.cause}", 
                    color = Colour.brand_red()), 
                    silent=True)
                return None
        if not tracks:
            await ctx.send(embed=Embed(
                title="Found no results for your search query.", 
                description="Please try again.", 
                color=Colour.brand_red()), 
                silent=True)
        return tracks

    @commands.command("showQ")
    async def showQueue(self, ctx) -> None:
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None: 
            await ctx.send(embed=Embed(title=f"There's no music player currently active.", color=Colour.light_embed()), silent=True)
            return

        if len(player.queue) == 0:
            message = Embed(title=f"The queue is currently empty.")
        else:
            pretty_string = ""
            for i in range(len(player.queue)):
                pretty_string += f"{i + 1}: {player.queue[i].title}\n"
            message = Embed(title=f"Songs up Next: ", description=pretty_string, color=Colour.light_embed())
        await ctx.send(embed = message, silent=True)

    @commands.command("play")
    async def stream(self, ctx, *args) -> None:
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)

        query = StreamingCog.stringify_args(args)
        logger.debug(f"Received query: {query}")
        if query.isspace() or query == "":
            await ctx.send(embed=Embed(title="The 'play' command requires a query.", description="Please use 'play' again, with a song query in your command call. Or, if you are trying to resume a paused player, use 'resume' command.", colour=Colour.brand_red()), silent=True)
            return
        

        if ctx.author.voice is None:
            await ctx.send(embed=Embed(title=f"Please join a voice channel and try again.", color=Colour.brand_red()), silent=True)
            return
        # create a new Player or move the current one to user's voice channel
        user_channel = ctx.author.voice.channel
        if player is not None:
            if not player.playing and (ctx.author.voice.channel != player.channel):
                await player.move_to(user_channel)
        else:
            player = await user_channel.connect(cls = Player, timeout = None)
        if player is None: raise RuntimeError("Error while creating a wavelink 'Player' object.")

        search_results = await self.search_with_retry(ctx, query) # handles sending failure message to discord
        if search_results is None:
            return
        else:
            best_match = search_results[0]
            num_tracks_added = player.queue.put(best_match) # should be 1 track
            message = Embed(title=f"Added {best_match.title} to the queue.", color=Colour.light_embed())
            message.set_thumbnail(url = best_match.artwork)
            await ctx.send(embed = message, silent=True)
        if player.playing and player.paused:
            await ctx.send(embed=Embed(title=f"The Player is paused.", description="Please use `resume` to continue playing music.", color=Colour.gold()))
        elif not player.playing:
            await player.play(player.queue.get())
        if player.playing:
            if len(player.queue) > 0:
                player.autoplay = AutoPlayMode.partial

    @commands.command()
    async def seek(self, ctx, *args) -> None:
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None:
            await ctx.send(embed=Embed(title=f"There is currently no active Player to play songs.", color=Colour.brand_red()))
            return
        if args[0] is None or args[0] == "":
            await ctx.send(embed=Embed(title=f"Please include a time you would like to skip to.", description=f"Acceptable format examples: `90` or `2:45`.", colour=Colour.brand_red()))
            return
        else:
            try:
                time_ms = StreamingCog.parse_seconds(args[0])
                await player.seek(time_ms)
                await ctx.send(embed = Embed(title=f"Seeking to {args[0]}", colour=Colour.brand_green()))
            except ValueError:
                await ctx.send(embed = Embed(title=f"Please use a valid time format.", description=f"Failed to seek, please use a format like one of these examples: `90` or `2:45`.", colour=Colour.brand_red()))
                return
            
    async def get_most_recent_message(self, channel:discord.TextChannel):
        "Returns the bot's most recent message in a given channel, searching up to 100 messages in history."
        async for message in channel.history(limit=100):
            if message.author == self.bot.user:
                return message
    
    async def get_bot_last_text_channel(self, player:wavelink.Player) -> discord.TextChannel:
        """Returns the discord.TextChannel where the bot most recently sent a message."""
        tchannels = [channel for channel in player.guild.text_channels if channel.type != discord.ChannelType.private]
        last_text_channel = None
        tzinfo = datetime.datetime.now().astimezone().tzinfo
        most_recent = datetime.datetime(1000, 1, 1, 1, 1, 1, tzinfo=tzinfo)
        # greater = more recent
        for channel in tchannels:
            message = await self.get_most_recent_message(channel)
            if message is None: continue
            if message.created_at > most_recent:
                most_recent = message.created_at
                last_text_channel = message.channel
        return last_text_channel

    @commands.Cog.listener("on_voice_state_update")
    async def leaveIfFinished(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        """This method call acts as an occasional check up on the bot's voice client, disconnecting the bot if its not playing."""
        if not member.id == self.bot.user.id:
            return
        elif before.channel is None: # if before.channel is None, then after.channel must be not-None
            voice:Player = after.channel.guild.voice_client
            time = 0
            while True:
                await asyncio.sleep(1)
                time = time + 1
                if voice.playing and not voice.paused:
                    time = 0
                if (time == 600 and not voice.paused) or (voice.paused and time==1200):
                    await after.channel.send(embed=Embed(title=f"Leaving voice chat due to inactivity.", color=Colour.light_embed()), silent=True)
                    await voice.disconnect()
                if not voice.connected:
                    break

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload:wavelink.TrackStartEventPayload):
        player = payload.player
        if player is None:
            logger.error("No 'wavelink.Player' object was found associated with your 'wavelink.TrackStartEventPayload'.")
            return
        try:
            song_title = player.current.title
            channel = await self.get_bot_last_text_channel(player)
            message = Embed(title=f"Playing: {song_title}", color=Colour.brand_green())
            message.set_thumbnail(url=player.current.artwork)
            await channel.send(embed=message, silent=True)
        except AttributeError as e: # would happen is player.current is None (in my experience this is caused by Lavalink needing to refresh its youtube 'viewer ID')
            #TODO handle error by attempting to play request again (give play a retries parameter?)
            logger.debug(f"Lavalink encountered an error while trying to play your song. Here's the player {player}, here's the player from payload: {payload.player}, here's the song that failed to play {payload.track}. Here's the error: {e}")
            await channel.send(embed=Embed(
                title="Lavalink encountered an error while trying to play your song.",
                color=Colour.brand_red()), silent=True)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload:wavelink.TrackEndEventPayload):
        player = payload.player
        if player is None:
            logger.error("No 'wavelink.Player' object was found in your wavelink.TrackEndEventPayload.")
            return
        queue = player.queue
        
        if len(queue) == 0:
            player.autoplay = AutoPlayMode.disabled
            
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.identifier} is ready!")

async def setup(bot):
    await bot.add_cog(StreamingCog(bot))