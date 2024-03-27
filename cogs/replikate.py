import os
from enum import Enum
from pathlib import Path

import discord
import requests
import replicate
from discord import Colour, Webhook
from requests import HTTPError
from discord.ext import commands
from discord.ext.commands.cog import Cog

from util import slugify
from cogs.controller import Controller

#TODO create a simple webhook handler to run as part of or alongside this cog. 
# I want to implement the replicate API's webhook capabilities so I can send a request to replicate and wait for its response without blocking the rest of the bots actions.
# right now, even if I asynchronously run a replicate prediction, all other bot operations are blocked while it waits for the response.


class Model(Enum):
    stable_diff = "stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478"
    dall_e = "kuprel/min-dalle:2af375da21c5b824a84e1c459f45b69a117ec8649c2aa974112d7cf1840fc0ce"

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
    async def request_image_generation(self, prompt:str) -> str:
        """Takes prompt and runs it against stable-diffusion model. Returns a URL linking to the generated image hosted on replicate's domain."""
        # webhook_url = https://discord.com/api/webhooks/1196555866820849807/RJNPoIGzkJ4_oaQhfqlrJ2w-HqpJe4Z_wYvsB9CR2Htz4qenPK5KxDwBZ_nrSbc-i3Gn
        # webhook = Webhook.from_url()
        output = await replicate.async_run(Model.stable_diff.value,
                            input = {"prompt": prompt,
                                    "num_outputs": 1,
                                    "width": 768,
                                    "height": 768,
                                    }
                            )
        url = output[0]
        return url
    
    async def request_dalle_generation(self, prompt:str):
        """Generates a generator, returns the generator. Iterate through generator to get results of prediction."""
        output = await replicate.async_run(Model.dall_e.value,
                            input = {"prompt": prompt,
                                    # "num_outputs": 1,
                                    "width": 768,
                                    "height": 768,
                                    "progressive_outputs": False,
                                    "grid_size": 1,
                                    }
                            )
        return output

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
    async def generate(self, ctx, *args):
        stringified_prompt = self.stringify_args(args)
        await ctx.send(embed = discord.Embed(title=f"AI Image Generation", description=f"I\'m processing your prompt, '{stringified_prompt} using stable diffusion'. This may take a minute.", color=Colour.yellow()))

        image_url = await self.request_image_generation(stringified_prompt)
        result_message = discord.Embed(title=f"Stable Diffusion Generated Result", color = Colour.green())
        result_message.set_image(url = image_url)
        await ctx.send(embed = result_message)

    @commands.command("generateDallE")
    async def generateDallE(self, ctx, *args):
        stringified_prompt = self.stringify_args(args)
        await ctx.send(embed = discord.Embed(title=f"AI Image Generation", description=f"I\'m processing your prompt, '{stringified_prompt}' using Dall-E mini. This may take a minute.", color=Colour.yellow()))

        images = self.request_dalle_generation(stringified_prompt)
        # for image in images:
        #     result_message = discord.Embed(title=f"Stable Diffusion Generated Result", color = Colour.green())
        #     result_message.set_image(url = image_url)
        #     await ctx.send(embed = result_message)
class ReplicateController(Controller):
    def __init__(self):
        pass

async def setup(bot):
   await bot.add_cog(ReplicateClient(bot))

