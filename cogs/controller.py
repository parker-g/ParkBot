from discord.ext.commands.cog import Cog
from discord import Guild

class Controller(Cog):
    """A base class that Cog Controllers derive from.
        :param self.bot: A reference to the discord Bot which is constructing the Controller.
        :param self.clazz: A reference to the class which the Controller will construct an instance of for each guild the Bot is a part of.
        :param self.gulds_to_clazzs: Dictionary storing all the guilds and clazzs that a controller owns."""
    #this is a quick and easy fix, pretty much a bandaid over an issue which should require surgery
    def __init__(self, bot, controlled_class):
        self.bot = bot
        self.clazz = controlled_class
        self.guilds_to_clazzs:dict = {guild : self.clazz(self.bot, guild) for guild in self.bot.guilds}

    def safeAddGuild(self, guild) -> None:
        """Adds input `guild` to `guilds_to_clazzs` if it doesn't already exist there."""
        if guild not in self.guilds_to_clazzs:
            self.guilds_to_clazzs[guild] = self.clazz(self.bot) 

    def getGuildClazz(self, ctx):
        """Returns the self.clazz associated with the current guild."""
        guild = ctx.guild
        self.safeAddGuild(guild)
        return self.guilds_to_clazzs[guild]