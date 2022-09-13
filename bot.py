import discord
from config import TOKEN

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
    if message.content.startswith('```markdown $heymongrel```'):
        await message.channel.send('```markdown Zah dyood. To view my capabilities, try $help```')
    if message.content.startswith('```$help```'):
        await message.channel.send('```markdown This is a list of commands I can respond to dyood: \n $heymongrel \n $playcheckers \n $banMike```')
client.run(TOKEN)

    
