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
from wavelink import Player, YouTubeTrack
from discord.ext.commands.errors import ExtensionFailed

from config.configuration import LAVALINK_URI, LAVALINK_PASS, WORKING_DIRECTORY


music_log_path = Path(WORKING_DIRECTORY) / "music.log"
music_handler = logging.FileHandler(music_log_path, encoding="utf-8", mode="w")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
music_handler.setFormatter(formatter)
logger = logging.Logger("music_logger")
logger.addHandler(music_handler)

class StreamingCog(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.node = None

    #TODO need to find how to clean this up and handle it accordingly when it fails
    async def cog_load(self) -> None:
        """Called when the bot loads this cog - sets up a connection to the lavalink server. Only necessary to do so once; a single node can serve multiple guilds at once."""
        if self.node is None:
            try:
                node = wavelink.Node(uri=LAVALINK_URI, password=LAVALINK_PASS, retries=10)
            except ExtensionFailed:
                logger.error(f"Error connecting to lavalink server.")
                return
            nodes = await wavelink.NodePool.connect(client=self.bot, nodes=[node])
            if nodes:
                self.node = self.getNode()
                logger.info(f"Node created + connected to lavalink server.")
            else:
                logger.error(f"Node created but couldn't establish connection to lavalink server.")
        elif self.node is not None:
            logger.info(f"A node connection has already been established.")

    @commands.command()
    async def showNode(self, ctx) -> None:
        node = self.getNode()
        if node is None:
            await ctx.send(embed=Embed(title=f"ParkBot not currently connected to a lavalink node.", color=Colour.light_embed()))
        else:
            await ctx.send(embed=Embed(title=f"Node connected!: {node.id}", color=Colour.light_embed()))
        
    @commands.command("nodePlayers")
    async def getNodePlayers(self, ctx) -> dict[int, Player]:
        node = wavelink.NodePool.get_node()
        await ctx.send(f"Here are your node's players: {node.players}")
        return node.players

    @commands.command()
    async def createNode(self, ctx) -> None:
        logger.info("Connecting to lavalink node.")
        if self.node is None:
            node = wavelink.Node(uri=LAVALINK_URI, password=LAVALINK_PASS)
            nodes = await wavelink.NodePool.connect(client=self.bot, nodes=[node])
            if nodes:
                self.node = self.getNode()
            else:
                logger.error(f"Error connecting to Lavalink Node")
        elif self.node is not None:
            logger.info(f"A node is already established and connected with ID: {self.node.id}")
        return

    #NOTE dont even need to explicitly get a node really, it seems the methods that require a node automatically grab one from the NodePool
    def getNode(self) -> wavelink.Node:
        node = wavelink.NodePool.get_node()
        return node

    # @commands.command("stop")
    # async def stop(self, ctx) -> None:
    #     node = self.getNode()
    #     player = node.get_player(ctx.guild.id)
    #     if player is None: return
    #     if player.is_playing():
    #         await player.stop()
    
    @commands.command("skip")
    async def skip(self, ctx) -> None:
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None:
            await ctx.send(embed=Embed(title=f"There is currently no active Player to play songs.", color=Colour.brand_red()))
        else:
            if player.is_connected():
                if player.is_playing(): #or len(player.queue) > 0:
                    current_song = player.current
                    if current_song is None: return
                    await ctx.send(embed=Embed(title=f"Skipping {current_song.title}", color=Colour.blue()))
                    await player.stop(force=True) # automatically forces next song to play if a next one exists
                else:
                    await ctx.send(embed=Embed(title=f"There's no song playing right now, or the queue is empty.", color=Colour.brand_red()))
            else:
                await ctx.send(embed=Embed(title="No voice channel connection right now.", description="Can't skip a song.", color=Colour.brand_red()))
    
    @commands.command()
    async def pause(self, ctx) -> None:
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None: 
            await ctx.send(embed=Embed(title=f"There is currently no active Player.", color=Colour.brand_red()))
        else:
            if player.is_connected():
                if player.is_playing():
                    await player.pause()
                    await ctx.send(embed=Embed(title=f"{player.current.title} paused.", description=f"Use `resume` to resume.", color=Colour.light_grey()))

    @commands.command("resume")
    async def resume(self, ctx) -> None:
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None:
            await ctx.send(embed=Embed(title=f"There is currently no active Player."))
        else:
            if player.is_connected():
                if player.is_paused():
                    await player.resume()
                else:
                    await ctx.send(embed=Embed(title=f"Player is not paused.", ))
    
    @commands.command("search")
    async def searchYouTube(self, ctx, *args) -> list[YouTubeTrack] | None:
        query = ""
        for arg in args:
            query += f"{arg} "

        tracks = await wavelink.YouTubeTrack.search(str(query))
        if not tracks:
            await ctx.send(f"Sorry, not tracks were returned.")
            return
        
        tracks_string = ""
        for track in tracks[:4]:
            tracks_string += f"{track.title}\n"

        await ctx.send(f"Here's the search results for your query, '{query}' : \n{tracks_string}")
        return tracks
    
    async def _searchYoutube(self, *args) -> list[YouTubeTrack] | None:
        query = ""
        for arg in args:
            query += f"{arg} "

        tracks = await wavelink.YouTubeTrack.search(str(query))
        if not tracks:
            return
        return tracks

    @commands.command("connect")
    async def connect(self, ctx) -> Player | None:
        channel = None
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send(f"Please join a voice channel before trying to play a song.")
        
        if channel is not None:
            player = await channel.connect(cls= Player, timeout = 0)
            return player

    @commands.command("showQ")
    async def showQueue(self, ctx) -> None:
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None: return

        if len(player.queue) == 0:
            message = Embed(title=f"The queue is currently empty.")
        else:
            pretty_string = ""
            for i in range(len(player.queue)):
                pretty_string += f"{i + 1}: {player.queue[i].title}\n"
            message = Embed(title=f"Songs up Next: ", description=pretty_string, color=Colour.light_embed())
        await ctx.send(embed = message)

    @commands.command("play")
    async def stream(self, ctx, *args) -> None:
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild.id)

        if ctx.author.voice is None:
            await ctx.send(embed=Embed(title=f"Please join a voice channel and try again.", color=Colour.brand_red()))
            return
        # create a new Player or move the current one to user's voice channel
        user_channel = ctx.author.voice.channel
        if player is not None:
            if not player.is_playing() and (ctx.author.voice.channel != player.channel):
                await player.move_to(user_channel)
        else:
            player:Player = await user_channel.connect(cls = Player, timeout = None)
        if player is None: raise RuntimeError("Error while creating a wavelink 'Player' object.")

        # add track to queue, and play song if not playing
        search_results = await self._searchYoutube(*args)
        if search_results is None:
            await ctx.send(embed=Embed(title="There was an issue searching your song on YouTube.", description="Please try again.", color=Colour.brand_red()))
            return
        else:
            best_match = search_results[0]
            player.queue.put(best_match)
            message = Embed(title=f"Added {best_match.title} to the queue.", color=Colour.light_embed())
            message.set_thumbnail(url = best_match.thumbnail)
            await ctx.send(embed = message)

        if not player.is_playing():
            await player.play(player.queue.pop())
        elif player.is_playing():
            if len(player.queue) > 0:
                player.autoplay = True

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
                if voice.is_playing() and not voice.is_paused():
                    time = 0
                if time == 600:
                    await voice.disconnect()
                    await after.channel.send(embed=Embed(title=f"Leaving voice chat due to inactivity.", color=Colour.light_embed()))
                if not voice.is_connected():
                    break

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload:wavelink.TrackEventPayload):
        player = payload.player
        song_title = player.current.title
        channel = await self.get_bot_last_text_channel(player)
        message = Embed(title=f"Playing: {song_title}", color=Colour.brand_green())
        message.set_thumbnail(url=player.current.thumbnail)
        await channel.send(embed=message)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload:wavelink.TrackEventPayload):
        player = payload.player
        queue = player.queue
        # player_autoqueue = player.auto_queue
        # logger.debug([f"autoqueued track: {track.title}" for track in player_autoqueue])
        # logger.debug(f"autoqueue length: {len(player_autoqueue)}")

        # logger.debug([f"queue track:{track.title}" for track in queue])
        # logger.debug(f"queue length: {len(queue)}")
        
        if len(queue) == 0:
            player.autoplay = False
            #TODO does this prevent songs from auto populating ? I will test rn
            
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.id} is ready!")

async def setup(bot):
    await bot.add_cog(StreamingCog(bot))