from config.configuration import LAVALINK_URI, LAVALINK_PASS, WORKING_DIRECTORY
from wavelink import Player, YouTubeTrack
from discord.ext.commands import Cog
from discord.ext import commands
from discord import Embed
from pathlib import Path
import wavelink
import logging
import aiohttp
import io
import asyncio
import discord
import time

def getTime() -> str:
    return time.asctime(time.localtime())

class StreamingCog(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.node = None

    @commands.command()
    async def showNode(self, ctx) -> None:
        node = self.getNode()
        if node is None:
            await ctx.send(embed=Embed(title=f"ParkBot not currently connected to a lavalink node."))
        else:
            await ctx.send(embed=Embed(title=f"Node connected!: {node.id}"))

    async def leaveWhenDone(self, ctx):
        print(f"sleeping for 600 seconds before checking if voice is playing")    
        await asyncio.sleep(600.0)
        # this didn't work last time, INVESTIGATE!
        print(f"done sleeping, checking if voice client playing")
        node = self.getNode()
        player = node.get_player(ctx.guild.id)
        if player is None: return
        if player.autoplay:
            if player.is_playing():
                await player.disconnect()
        else:
            if not player.is_playing():
                await self.leaveWhenDone(ctx)
            else:
                await player.disconnect()

    @commands.command()
    async def createNode(self, ctx) -> None:
        print("Connecting to lavalink node.")
        if self.node is None:
            node = wavelink.Node(uri=LAVALINK_URI, password=LAVALINK_PASS)
            nodes = await wavelink.NodePool.connect(client=self.bot, nodes=[node])
            if nodes:
                self.node = self.getNode()
            else:
                print(f"Error connecting to Lavalink Node")
        elif self.node is not None:
            print(f"A node is already established and connected with ID: {self.node.id}")
        return

    #NOTE dont even need to explicitly get a node really, it seems the methods that require a node automatically grab one from the NodePool
    def getNode(self) -> wavelink.Node:
        node = wavelink.NodePool.get_node()
        return node

    @commands.command("stop")
    async def stop(self, ctx) -> None:
        node = self.getNode()
        player = node.get_player(ctx.guild.id)
        if player is None: return
        if player.is_playing():
            await player.stop()
    
    @commands.command("skip")
    async def skip(self, ctx) -> None:
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild.id)
        if player is None:
            await ctx.send(embed=Embed(title=f"There is currently no active Player to play songs."))
        else:
            if player.is_connected():
                if player.is_playing(): #or len(player.queue) > 0:
                    current_song = player.current
                    if current_song is None: return
                    await ctx.send(embed=Embed(title=f"Skipping {current_song.title}"))
                    await player.stop(force=True) # automatically forces next song to play if a next one exists
                else:
                    await ctx.send(embed=Embed(title=f"There's no song playing right now, or the queue is empty."))
            else:
                await ctx.send(embed=Embed(title="No voice channel connection right now.", description="Can't skip a song."))
            
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
                    await ctx.send(embed=Embed(title=f"Player is not paused."))
    

    @commands.command("nodePlayers")
    async def getNodePlayers(self, ctx) -> dict[int, Player]:
        node = wavelink.NodePool.get_node()
        await ctx.send(f"Here are your node's players: {node.players}")
        return node.players
    
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
        # if channel is not None:
        #     player = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        #     if player is not None:
        #             print(player)
        #             if not player.is_playing():
        #                 await player.disconnect()
        #                 user_channel = ctx.author.voice.channel
        #                 player = await user_channel.connect(cls = Player, timeout = None)
        #             else:
        #                 # player is playing already so leave it be
        #                 pass

        #     elif (player is None):
        #         user_channel = ctx.author.voice.channel
        #         player = await user_channel.connect(cls = Player, timeout = None)
        #     return player

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
            message = Embed(title=f"Songs up Next: ", description=pretty_string)
        await ctx.send(embed = message)

    @commands.command("play")
    async def stream(self, ctx, *args) -> None:
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild.id)

        if ctx.author.voice is None:
            await ctx.send(embed=Embed(title=f"Please join a voice channel and try again."))
            return
        else:
            if player is not None:
                if not player.is_playing():
                    await player.disconnect()
                    user_channel = ctx.author.voice.channel
                    player:Player = await user_channel.connect(cls = Player, timeout = None)
                    
                else:
                    pass
            elif (player is None):
                user_channel = ctx.author.voice.channel
                player:Player = await user_channel.connect(cls = Player, timeout = None)
        
        if player is not None: # add track to queue, and play song if not playing
            search_results = await self._searchYoutube(*args)
            if search_results is None:
                await ctx.send(embed=Embed(title="There was an issue searching your song on YouTube.", description="Please try again."))
            else:
                best_match = search_results[0]
                player.queue.put(best_match)
                message = Embed(title=f"Added {best_match.title} to the queue.")
                message.set_thumbnail(url = best_match.thumbnail)
                await ctx.send(embed = message)

            if not player.is_playing():
                # search + play requested song
                await player.play(player.queue.pop())
            elif player.is_playing():
                if len(player.queue) > 0:
                    player.autoplay = True
        else:
            return
        # check if player is playing, add song to queue or start pla

    # @commands.Cog.listener()
    # async def on_wavelink_track_end(node:wavelink.Node):
        # need to check if the normal queue is empty after a track is over, and if so then stop playing songs. ( before autoplay populates queue)




    # TODO on_ready event can be called multiple times in a discord session, so should implement
    # logic here for checking if a node already exists before trying to connect to a new one
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Connecting to lavalink node.")
        if self.node is None:
            node = wavelink.Node(uri=LAVALINK_URI, password=LAVALINK_PASS)
            nodes = await wavelink.NodePool.connect(client=self.bot, nodes=[node])
            if nodes:
                print(f"Node connected at ID: {nodes.keys()}")
                self.node = self.getNode()
            else:
                print(f"Error connecting to Lavalink Node")
        elif self.node is not None:
            print(f"A node is already established and connected.")
        return


    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.id} is ready!")



async def setup(bot):
    await bot.add_cog(StreamingCog(bot))