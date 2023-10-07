import wavelink
from discord.ext.commands import Cog
from discord.ext import commands
from discord import Embed
import asyncio

class NewMusicCog(Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command("createNode")
    async def createNode(self, ctx) -> dict[str, wavelink.Node]:
        node = wavelink.Node(uri="192.168.1.218:2333", password="biggieReginald")
        nodes = await wavelink.NodePool.connect(client=self.bot, nodes=[node])
        # await ctx.send(embed=Embed(title=f"Your Lavalink Node", description=f"{nodes}"))
        return nodes
    
    def getNode(self) -> wavelink.Node:
        node = wavelink.NodePool.get_node()
        return node
    
    def getNodePlayers(self, node) -> list[wavelink.Player]:
        return node.players
    
    @commands.command("search")
    async def searchYouTube(self, ctx, *args) -> list | None:
        query = ""
        for arg in args:
            query += f"{arg} "

        tracks = await wavelink.YouTubeTrack.search(str(query))
        if not tracks:
            await ctx.send(f"Sorry, not tracks were returned.")
            return
        await ctx.send(f"Here's the search results for your query, {query} : \n{[track.title for track in tracks]}")
        return tracks




    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.id} is ready!")

async def setup(bot):
    await bot.add_cog(NewMusicCog(bot))