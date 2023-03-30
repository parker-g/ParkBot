import discord
from config.config import TOKEN, CANVAS_API_KEY
import logging
from discord.ext import commands
import helper
from get_assignments import get_new_assignments, datetime_file
import blackjack

#note for me:
# when using python keyword in terminal, u must reference the direct path to the venv python executable.
# don't forget this ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# BE SURE TO SET REPLICATE API TOKEN TO ENV VARIABLE BEFORE RUNNING





# used to log errors and statuses on discord.log
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# 'intents' specify what events our bot will be able to act on. default events covers a lot of events but
# i make sure to specifically set the 'message_content_ intent to True, bc that's the main intent I will be using

intents = discord.Intents.default()
intents.message_content = True

# instantiate an instance of the Bot class (Bot is a subclass of Client - so it has all the functionality of Client with the addition of Bot functionality
bot = commands.Bot(command_prefix='$', intents=intents)

# remove the default empty help command, so i can replace it with my own
bot.remove_command('help')

# on the event called `on_ready`, python terminal shows that the bot is logged in by printing 
@bot.event
async def on_ready():
    return print(f'I\'m logged in as {bot.user}')

# defines help command. uses bot.group decorator to enable help to take further inputs after help - so that the
# user can specify which command they want clarification on. also set invoke_without_command to True so i can call 'help' as a 
# command by itself  (i think)

@bot.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title='help', description='to get help with a command, use $help <command>.', color=ctx.author.color)
    em.add_field(name='pic commands', value='`milkies`, `creator`, `dallE`, `findFurry`')
    em.add_field(name='chat commands', value='`heymongrel`, `banmike`, `getNewAssignments`')
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

@help.command()
async def findFurry(ctx):
    em = discord.Embed(title='findFurry', description='step right up and use this command to find your buddys\' furry lookalikes! input a name, or input nothing at all.')
    await ctx.send(embed = em)


@help.command()
async def getNewAssignments(ctx):
    em = discord.Embed(title='getNewAssignments', description='takes a number of days as input. function returns all assignments from CSC 221 within given number of days ahead from current day.\n for example `getNewAssignments 15` will return any assignments due in the next 15 days.')
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

@bot.command()
async def dallE(ctx, args:str):
    em = discord.Embed()
    em.add_field(name='dallE', value='I\'m working on processing your prompt. This may take a minute.')
    image = helper.get_image(args=args)
    await ctx.send(embed =em, file=discord.File(image))

@bot.command()
async def findFurry(ctx):
    image = helper.get_furry_image()
    await ctx.send(file=discord.File(image))


@bot.command()
async def getNewAssignments(ctx, num:str):
    num = int(num)
    assignments, time_diff = get_new_assignments(datetime_file, num)
    pretty_string = ""
    for item in assignments:
        pretty_string += f"{item}\n"
    if len(assignments) == 0:
        pretty_string = "Yay, no new assignments in that range!"
    
    em = discord.Embed(title="New assignments", description=pretty_string)
    em.add_field(name="Time since last checked: (hours/minutes/seconds)", value=f"{time_diff}")
    await ctx.send(embed = em)

@bot.command()
async def playBlackJack(ctx, *args):
    game = blackjack.Game(args)
    


# @bot.command()
# async def imgTest(ctx):
#     em = discord.Embed()
#     em.add_field(name='dallE', value='I\'m working on processing your prompt. This may take a minute.')
#     image = test.img_test0()
#     await ctx.send(embed = em, file=discord.File(image))



bot.run(TOKEN, log_handler=handler)

