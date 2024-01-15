import os
from pathlib import Path

import discord
import requests
import replicate
from discord import Colour
from requests import HTTPError
from discord.ext import commands
from discord.ext.commands.cog import Cog

from helper import slugify
from cogs.controller import Controller

class ReplicateClient(Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def stringify_args(args:tuple) -> str:
        query = ""
        for arg in args:
            #NOTE consider html escaping each character in the query
            query += f"{arg} "
        return query

    #TODO set this up to just send a request, then set up another method to listen for the 'request completed' webhook -
    #BUG the way this works now, it blocks while waiting for the request to finish, which throws error messages in the main log. it hasn't been a breaking issue so far but I would rather fix it than leave it
    def request_image_generation(self, prompt:str) -> str:
        """Sanitizes input prompt and runs it against stable-diffusion model. Returns a URL linking to the generated image hosted on replicate's domain."""
        output = replicate.run("stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478",
                            input = {"prompt": prompt,
                                    "num_outputs": 1,
                                    "width": 768,
                                    "height": 768,}
                            )
        url = output[0]
        return url

    def download_image(self, image_url:str, image_prompt:str) -> None:
        here = Path(os.getcwd())
        img_title = slugify(image_prompt)
        dl_dest = here / "data" / "images" / "ai" / f"{img_title}.png"
        try:
            response = requests.get(image_url)
            with open(dl_dest, 'wb') as file:
                file.write(response.content)
        except HTTPError as e:
            print(f"Failed to download image - {e}")
    
    @commands.command("generate")
    async def gemerate(self, ctx, *args):
        stringified_prompt = self.stringify_args(args)
        await ctx.send(embed = discord.Embed(title=f"AI Image Generation", description=f"I\'m processing your prompt, '{stringified_prompt}'. This may take a minute.", color=Colour.yellow()))

        image_url = self.request_image_generation(stringified_prompt)
        result_message = discord.Embed(title=f"Stable Diffusion Generated Result", color = Colour.green())
        result_message.set_image(url = image_url)
        await ctx.send(embed = result_message)

class ReplicateController(Controller):
    def __init__(self):
        pass

async def setup(bot):
   await bot.add_cog(ReplicateClient(bot))

