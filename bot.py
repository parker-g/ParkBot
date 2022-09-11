import discord
from config import TOKEN

intents = discord.Intents()
intents.message_content = True

client = discord.Client(intents=intents)

    
