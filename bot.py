from docarray import Document
import discord
from config.config import TOKEN
import logging
from discord.ext import commands
from dall_e_flow import get_image
# server to serve dallE results
server_url = 'grpcs://dalle-flow.dev.jina.ai'

# used to log errors and statuses on discord.log
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# 'intents' specify what events our bot will be able to act on. default events covers our needs for this bot. 
# (i mostly intend to read and send messages, so i am sure to set the message_content intent to True)

intents = discord.Intents.default()
intents.message_content = True

# instantiate an instance of the Bot class (Bot is a subclass of Client - so it has all the functionality of Client with the addition of Bot functionality)
bot = commands.Bot(command_prefix='$', intents=intents)

# remove the default empty help command, so i can replace it with my own
bot.remove_command('help')

# on the event called `on_ready`, python terminal shows that the bot is logged in by printing 
@bot.event
async def on_ready():
    return print(f'I\'m online as {bot.user}')

# defines help command. uses bot.group decorator to enable help to take further inputs after help - so the end
# user can specify which command they want clarification on

@bot.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title='help', description='to get help with a command, use $help <command>.', color=ctx.author.color)
    em.add_field(name='pic commands', value='`milkies`, `creator`, `dallE`')
    em.add_field(name='chat commands', value='`heymongrel`, `banmike`')
    await ctx.send(embed = em)

# all help commands are defined below
@help.command()
async def heymongrel(ctx):
    em = discord.Embed(title='heymongrel', description='returns a greeting :D')
    await ctx.send(embed = em)

@help.command()
async def milkies(ctx):
    em = discord.Embed(title='milkies', description='try it and find out sweet cheeks ;)')
    await ctx.send(embed = em)

@help.command()
async def creator(ctx):
    em = discord.Embed(title='creator', description='returns a picture perfect recreation of this bot\'s creator')
    await ctx.send(embed = em)

@help.command()
async def banmike(ctx):
    em = discord.Embed(title='banmike', description='use your head. this command bans mike of course :P')
    await ctx.send(embed = em)

@help.command()
async def dallE(ctx):
    em = discord.Embed(title='dallE', description='this command allows users to submit a prompt to Dall-E - then returns the results of their prompt :D')
    em.add_field(name='syntax/how to use', value='`$dallE <your prompt>`')
    await ctx.send(embed = em)
 
# now these are the actual commands corresponding to the list of commands in help
@bot.command()
async def heymongrel(ctx):
    em = discord.Embed(description='Zah dyood')
    await ctx.send(embed = em)

@bot.command()
async def milkies(ctx):
    await ctx.send(file=discord.File('images/milkies.jpg'))

@bot.command()
async def creator(ctx):
    await ctx.send(file=discord.File('images/gigachad.jpg'))
    # send(file=discord.File('my_file.png'))

@bot.command()
async def dallE(ctx, args:str):
    em = discord.Embed()
    em.add_field(name='dallE', value='I\'m working on processing your prompt. This may take a minute.')
    results = get_image(args, server = server_url)
    await ctx.send(embed = em,file=discord.File(results[0]))




# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return
#     if message.content.startswith('$heymongrel'):
#         await message.channel.send('Zah dyood. To view my capabilities, try $help')
#     if message.content.startswith('$help'):
#         await message.channel.send('This is a list of commands I can respond to dyood: \n$heymongrel \n$mommy \n$milkies \n$playcheckers \n$banMike \n$creator')
#     if message.content.startswith('$mommy'):
#         await message.channel.send('hey baby it\'s me, mommy. u want some $milkies ;)')
#     if message.content.startswith('$milkies'):
#         with open('milkies.jpg', 'rb') as f:
#             picture = discord.File(f)
#         await message.channel.send(file=picture)
#     if message.content.startswith('$creator'):
#         with open('gigachad.jpg', 'rb') as f:
#             picture = discord.File(f)
#         await message.channel.send(file=picture)
bot.run(TOKEN, log_handler=handler)

