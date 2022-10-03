import discord
from config import TOKEN
from PIL import Image

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    return print(f'I\'m online as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$heymongrel'):
        await message.channel.send('Zah dyood. To view my capabilities, try $help')
    if message.content.startswith('$help'):
        await message.channel.send('This is a list of commands I can respond to dyood: \n$heymongrel \n$mommy \n$milkies \n$playcheckers \n$banMike \n$creator')
    if message.content.startswith('$mommy'):
        await message.channel.send('hey baby it\'s me, mommy. u want some $milkies ;)')
    if message.content.startswith('$milkies'):
        with open('milkies.jpg', 'rb') as f:
            picture = discord.File(f)
        await message.channel.send(file=picture)
    if message.content.startswith('$creator'):
        with open('gigachad.jpg', 'rb') as f:
            picture = discord.File(f)
        await message.channel.send(file=picture)
client.run(TOKEN)

    
