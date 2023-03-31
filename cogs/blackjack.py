import random
import pandas as pd
import logging
import asyncio
from discord.ext.commands.cog import Cog
from discord.ext import commands
from discord import Member, Embed
from config.config import BANK_PATH


logger = logging.Logger('BJLog')

# def check_isHit(ctx, reaction, user):
#     return user == ctx.author and str(reaction.emoji) == "✅"  
        




class Deck:
    color_legend = {
        "spades": "black",
        "clubs": "black",
        "hearts": "red",
        "diamonds": "red",
    }

    card_legend = {
        1: "ace",
        2: "2",
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "10",
        11: "jack",
        12: "queen",
        13: "king",
    }

    blackjack_face_legend = {
        "ace": 1,
        "jack": 10,
        "queen": 10,
        "king": 10,
    }

    def __init__(self):
        self.deck = []
        for i in range(1, 14):
            self.deck.append((Deck.card_legend[i], "spades"))
            self.deck.append((Deck.card_legend[i], "clubs"))
            self.deck.append((Deck.card_legend[i], "hearts"))
            self.deck.append((Deck.card_legend[i], "diamonds"))

    def shuffle(self) -> None:
        random.shuffle(self.deck)


class Player(Cog):
    def __init__(self, ctx):
        self.name = ctx.author
        self.hand = []
        self.bust = False
        self.blackJack = False
        self.done = False
        if self.bust is True:
            self.done = True
        self.winner = False        



    def sumCards(self):
        total = 0
        for tuple in self.hand:
            num = tuple[0]
            try:
                num = int(num)
            except:
                num = Deck.blackjack_face_legend[num]
            total += num
        return total

    def isBlackJack(self):
        if self.sumCards() == 21:
            self.blackJack = True
        return self.blackJack

    def isBust(self):
        if self.sumCards() > 21:
            self.bust = True
        return self.bust
    
    def prettyHand(self) -> str:
        pretty_string = "A"
        for num, suit in self.hand[:-1]:
            pretty_string += f" {num} of {suit}, a"
        last_num, last_suit = self.hand[-1]
        pretty_string += f"nd a {last_num} of {last_suit}"
        return pretty_string

# use playerqueue to queue up players before blackjack game begins
class PlayerQueue:
    def __init__(self):
        self.q = []


class Dealer:
    def __init__(self, deck:Deck, players:list[Player]):
        self.deck = deck.deck
        self.players = players
        self.cards_in_play = []

    def dealCard(self, player:Player):
        player.hand.append(self.deck[0])
        self.cards_in_play.append(self.deck[0])
        self.deck.remove(self.deck[0])

    def returnCardsToDeck(self):
        self.deck += self.cards_in_play
        self.cards_in_play = []
        

    def dealHands(self) -> None:
        for i in range(2):
            for player in self.players:
                self.dealCard(player)
    
    def takeTurn(self, player:Player, toHit:bool):
        if toHit == True:
            self.dealCard(player)
    
    def isBlackjack(self, player:Player):
        if player.sumCards() == 21:
            player.blackJack = True
    
    def isBust(self, player:Player):
        if player.sumCards() > 21:
            player.bust = True

    def getWinner(self, players:list[Player]) -> tuple[str | list[str], int]:
        winner = players[0]
        highest_score = 0
        players_busted = 0
        winners = []
        
        for player in players:
            if player.isBust():
                players_busted += 1
                # use the players busted variable to later check if all players busted ( to see if no one won )
                continue
            # if player isnt bust, then logic will continue here
            if player.sumCards() > highest_score:
                    highest_score = player.sumCards()
                    winner = player
        
        # get player with highest score ^
        for player in players:
            if player.isBust():
                continue
            if player.sumCards() == winner.sumCards():
                winners.append(player)
        # check if there's a tie

        if (len(winners) > 1):
            winners_string = ""
            for winner in winners:
                winners_string += f"{winner.name}, "
            return winners_string, highest_score
        elif len(winners) == 1:
            winner = winner.name

         # if multiple winners, return a string of their names, else return string of sole winner name
        if players_busted == len(players):
            winner = "None"
        # ^ if all players busted, winner = "None"
        return winner, highest_score
        



class BlackJackGame(Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.deck = Deck()
        self.deck.shuffle()
        self.players = []
        self.dealer = Dealer(self.deck, self.players)
    
    @commands.command()
    async def joinQ(self, ctx):
        new_player = Player(ctx)
        self.players.append(new_player)
        await ctx.send(f"{ctx.author} has been added to blackjack queue.")
        

    
    def newRound(self) -> None:
        self.dealer.returnCardsToDeck()
        self.deck.shuffle()
        for player in self.players:
            player.winner = False
            player.done = False
            player.bust = False
            player.blackJack = False
            player.hand = []

    def showHands(self, players:list[Player]):
        for player in players:
            print(f"\n{player.name} shows their cards. Their hand looks like this: {player.hand}. ")
    
    def takeTurn(self, player:Player, wantToHit:bool):
        if wantToHit is False:
            pass
        player.dealCard()
    
    @commands.command("clearQ")
    async def clearQueue(self, ctx):
        self.players = []
        await ctx.send("Okay, queue has been cleared.")

    @commands.command("showQ")
    async def showQueue(self, ctx):
        players_string = ""
        for player in self.players:
            players_string += f"{player.name}\n"
        em = Embed(title="Players in Queue", description=f"{players_string}")
        await ctx.send(embed = em)



    @commands.command("playJack")
    async def play(self, ctx):
        self.newRound()
        # create a new dealer each round - keeping only one dealer caused issues
        dealer = Dealer(self.deck, self.players)
        dealer.dealHands()
        for player in self.players:
            await ctx.send(f"It's your turn, {player.name}! Your total is {player.sumCards()}.")
            # send a message to discord chat telling player it's their turn to go.
            while player.done != True:
                # take the next message from the player we are iterating on
                try:
                    em = Embed(title=f"Your total is {player.sumCards()}.", description="Do you want to hit? React with a ✅ for yes, or 🚫 for no.")
                    message = await ctx.send(embed = em)
                    await message.add_reaction("✅")
                    await message.add_reaction("🚫")
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=15.0)
                    if (user == player.name) and (reaction.emoji == "✅"):
                        await message.delete()
                        await ctx.send("Okay, dealing you another card.")
                        dealer.dealCard(player)
                        if player.isBust():
                            player.done = True
                            await ctx.send(f"You busted! Your total is {player.sumCards()}")
                        else: 
                            continue
                    elif (user == player.name) and (reaction.emoji == "🚫"):
                        await message.delete()
                        player.done = True
                        await ctx.send(f"Okay, your turn is over.")
                except asyncio.TimeoutError:
                    await ctx.send("You took too long to react! Your turn is over.")
                    player.done = True
        #when all players are done with their turns
        winner, highest_score = dealer.getWinner(self.players)   
        win_statement = f"\nAnd the winner for this hand is: {winner}"     
        sum_statement = f" with a sum of {highest_score}."    
        if highest_score != 0:
            await ctx.send(win_statement + sum_statement)
        else:
            await ctx.send(win_statement)
        
        await ctx.send("\nHere's everyone's hands.\n")
        long_ass_string = ""
        for player in self.players:
            long_ass_string += (f"{player.name} had: {player.prettyHand()}, with a total of {player.sumCards()}\n")
        em = Embed(title="All Hands:", description = long_ass_string)
        await ctx.send(embed = em)
        # empty players before giving opportunity for another round to start

# register cog to bot
async def setup(bot):
    await bot.add_cog(BlackJackGame(bot))        
