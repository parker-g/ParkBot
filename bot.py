import discord
from config.config import TOKEN
import logging
from discord.ext import commands
import api
import test


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
    return print(f'I\'m logged in as {bot.user}')

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
    em.add_field(name='syntax/how to use', value='`$dallE "your prompt"`')
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
    image = api.get_image(args=args)
    await ctx.send(file=discord.File(image, description='Here\'s the result of your prompt'))


    # url for jina reference - https://github.com/jina-ai/jina/issues/4761
    # if this method doesn't work - i could always go the jina route again, but this time 
    # 1. create my own dall E flow
    # 2. deploy it using jcloud
    # 3. use Flow and Client to post requests to my jcloud flow
    # ----- thing is, this method may still end with the async Jina error from earlier. may have to focus my learning on 
    # improving understanding of async/await before I can finish this project. will see
@bot.command()
async def imgTest(ctx):
    image = test.img_test0()
    await ctx.send(file=discord.File(image))



bot.run(TOKEN, log_handler=handler)

