import discord
from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    await print(f'I have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$heymongrel'):
        await message.channel.send('Zah dyood')

client.run(TOKEN)

    
