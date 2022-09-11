import discord
from config import TOKEN

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}.')
    
