import logging
from pathlib import Path

import discord
from discord import Colour
from discord.ext import commands

from config.configuration import WORKING_DIRECTORY, TOKEN, LAVALINK_PASS, LAVALINK_URI

# BE SURE TO SET REPLICATE API TOKEN TO ENV VARIABLE BEFORE RUNNING
log_path = Path(WORKING_DIRECTORY) / "discord.log"
handler = logging.FileHandler(log_path, encoding='utf-8', mode='w')

# 'intents' specify what events our bot will be able to act on. default events covers a lot of events but
# i make sure to specifically include message_content and voice_states as this bot references these events often

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True


# instantiate an instance of the Bot class
bot = commands.Bot(command_prefix='$', intents=intents)

# remove the default empty help command, so i can replace it with my own
bot.remove_command('help')

@bot.event
async def on_ready():
    await bot.load_extension("cogs.economy")
    await bot.load_extension("cogs.games")
    # await bot.load_extension("cogs.rewards") # pyttsx3 installs a pywin32 which I can't have as a dependency
    # await bot.load_extension("cogs.music")
    await bot.load_extension("cogs.canvas")
    await bot.load_extension("cogs.streamingmusic")
    await bot.load_extension("cogs.replikate")
    return print(f'I\'m logged in as {bot.user}')

# defines help command. uses bot.group decorator to enable help to take further inputs after help - so that the
# user can specify which command they want clarification on. also set invoke_without_command to True so i can call 'help' as a 
# command by itself  (i think)

@bot.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title='help', description='to get help with a command, use $help <command>.', color=ctx.author.color)
    em.add_field(name='pic commands', value='`creator`, `dallE`, `findFurry`')
    em.add_field(name='chat commands', value='`heymongrel`, `banmike`, `getNewAssignments`')
    em.add_field(name='voice commands', value="`say`")
    em.add_field(name='game commands', value="`joinQ`, `leaveQ`, `showPlayers`, `clearQ`, `setBet <amount>`, `playPoker`, `playJack`, `resetJack`")
    em.add_field(name='music commands', value="`play`, `pause`, `skip`, `showQ`, `kickBot`")
    await ctx.send(embed = em)

# all help commands are defined below

@help.command()
async def heymongrel(ctx):
    em = discord.Embed(title='heymongrel', description='returns a greeting :D')
    await ctx.send(embed = em)

@help.command()
async def say(ctx):
    em = discord.Embed(title='say', description='usage: `say <what you want bot to say>`. bot speaks requested string in voice channel.')
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

@help.command()
async def playJack(ctx):
    em = discord.Embed(title="playJack", description = "begin a game of blackjack. players must first have joined the queue using `joinQ`. players will remain in player queue until they leave. set bets before hand to win some GleepCoins.")
    await ctx.send(embed = em)

@help.command()
async def playPoker(ctx):
    em = discord.Embed(title="playPoker", description = "begin a game of Poker. players must first have joined the queue using `joinQ`. players will remain in player queue until they leave. don't worry about setting bets before the game, you will set bets during the game.")
    await ctx.send(embed = em)
    
@help.command()
async def setBet(ctx):
    em = discord.Embed(title="setBet", description = "usage : `setBet <amount>`\nuse this command to bet your valuable GleepCoins in the next gambling game.")
    await ctx.send(embed = em)

@help.command()
async def balance(ctx):
    em = discord.Embed(title="balance", description = "show your GleepCoin bank balance. if nothing comes up, you don't have a balance yet. you will receive 1000 GleepCoins to bet with upon your first bet.")
    await ctx.send(embed = em)

@help.command()
async def joinQ(ctx):
    em = discord.Embed(title="joinQ", description= "join the blackjack players pool with this command.") 
    await ctx.send(embed = em)

@help.command()
async def leaveQ(ctx):
    em = discord.Embed(title="leaveQ", description= "leave the player pool and return any bets you had queued, back to your bank balance.") 
    await ctx.send(embed = em)

@help.command()
async def showQ(ctx):
    em = discord.Embed(title="showQ", description= "shows songs in queue") 
    await ctx.send(embed = em)

@help.command()
async def play(ctx):
    em = discord.Embed(title="play", description="usage: `play <name of song>`. if a song is already playing, will queue your request")
    await ctx.send(embed= em)

@help.command()
async def skip(ctx):
    em = discord.Embed(title="skip", description="skips the song that's currently playing")
    await ctx.send(embed = em)

# @help.command()
# async def currentSong(ctx):
#     em = discord.Embed(title="currentSong", description="shows the song currently playing")
#     await ctx.send(embed = em)

@help.command()
async def kickBot(ctx):
    em = discord.Embed(title="kickBot", description="kicks your bot from the voice channel.")
    await ctx.send(embed = em)

@help.command()
async def showPlayers(ctx):
    em = discord.Embed(title="showPlayers", description="shows all the players who are in the gaming player pool")
    await ctx.send(embed = em)

@help.command()
async def clearQ(ctx):
    em = discord.Embed(title="clearQ", description= "removes all players from player pool, and returns their queued bets to each respective bank balance.") 
    await ctx.send(embed = em)

@help.command()
async def resetGames(ctx):
    em = discord.Embed(title="resetGames", description="use this command to hard reset the games and economoy cogs. (use to reset blackjack or poker if they're broken/ glitched. it won't hurt anything)")
    await ctx.send(embed = em)

@help.command()
async def pause(ctx):
    em = discord.Embed(title="pause", description="Pauses the music player if one exists. Use `resume` to resume.")
    await ctx.send(embed = em)
    
@help.command()
async def resume(ctx):
    em = discord.Embed(title="resume", description="resumes a paused music player")
    await ctx.send(embed = em)
# now these are the actual commands corresponding to the list of commands in help

@bot.command()
async def checkCogs(ctx):
    cogs = ["GamesController", "CanvasClient", "Economy", "StreamingCog", "RewardsController"]
    cog_string = ""
    for cog in cogs:
        if bot.get_cog(cog) is not None:
            cog_string += f"{cog}, "
    em = discord.Embed(title=f"Cogs in use", description=cog_string)
    await ctx.send(embed = em)

@bot.command()
async def heymongrel(ctx):
    em = discord.Embed(description='Zah dyood')
    await ctx.send(embed = em)

@bot.command()
async def creator(ctx):
    await ctx.send(file=discord.File('data/images/gigachad.jpg'))

@bot.command()
async def resetGames(ctx):
    await bot.reload_extension("cogs.games")
    await bot.reload_extension("cogs.economy")
    em = discord.Embed(title="Reset games and economy cogs")
    await ctx.send(embed = em)

bot.run(TOKEN, log_handler=handler)

