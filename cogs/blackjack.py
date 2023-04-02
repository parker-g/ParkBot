import random
import pandas as pd
import logging
import asyncio
from discord.ext.commands.cog import Cog
from discord.ext import commands
from discord import Member, Embed
from config.config import BANK_PATH


logger = logging.Logger('BJLog')

# need to modify game play function so that 
    # dealer deals cards to players besides himself
    # dealer deals himself two cards, shows only one
    # let players play their hands

    # dealer reveals his second card, dealer plays till over 17 
    # for players that haven't busted:
        # compare player score to dealer score
        # if player score higher, player added to winners
        # if player score lower, do nothing
    

        




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


class Dealer(Player):
    def __init__(self, deck:Deck, players:list[Player]):
        self.name = "Dealer"
        self.deck = deck.deck
        self.players = players
        self.cards_in_play = []
        self.hand = []
        self.bust = False
        self.done = False
        if self.bust is True:
            self.done = True

    def sumCards(self) -> int:
        total = 0
        for tuple in self.hand:
            num = tuple[0]
            try:
                num = int(num)
            except:
                num = Deck.blackjack_face_legend[num]
            total += num
        return total

    def dealToSelf(self):
        while self.sumCards() < 17:
            self.dealCard(self)
        return
        
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
    
    def isBust(self):
        if self.sumCards() > 21:
            self.bust = True


    # def getWinner(self, players) -> tuple[str | list[str], int]:
    #     winner = players[0]
    #     highest_score = 0




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
        if not new_player in self.players:
            self.players.append(new_player)
            message_str = f"{ctx.author} has been added to blackjack queue."
        elif new_player in self.players:
            message_str = f"{ctx.author} is already in queue."
        message = await ctx.send(message_str)
        await message.delete(delay=5.0)

    
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

    def getWinners(self, players:Player) -> list[Player]:
        dealer = None
        winners = []
        tiebabies = []
        # get the dealer, store and remove dealer, remove players who have been busted
        for player in players:
            if player.name == "Dealer":
                dealer = player # save dealer object in variable dealer
                continue
            if player.isBust():
                players.remove(player)
        if dealer is None:
            print("There was an error - the dealer is not in the player pool")
            return
        
        #store dealer sum
        dealer_total = dealer.sumCards()
        #remove dealer from player pool 
        players.remove(dealer)

        # for the players who haven't busted or aren't the dealer: 
        for player in players:
            if dealer_total > 21:
                player.winner = True
                winners.append(player)
                continue
            if player.sumCards() > dealer_total:
                player.winner = True
                winners.append(player)
            elif player.sumCards() == dealer_total:
                tiebabies.append(player)
        
        # now winners holds all our winners, tiebabies holds anyone who's tied
        return winners, tiebabies




    @commands.command("playJack")
    async def play(self, ctx):
        self.newRound()
        # create a new dealer each round - he deals his own hand first, and shows his first card.
        dealer = Dealer(self.deck, self.players)
        dealer.dealToSelf()
        dealer_shows = Embed(title=f"Dealer's Hand", description=f"The dealer's showing {dealer.hand[0]}.")
        dealer_hand_message = await ctx.send(embed = dealer_shows)

        # dealer now deals a hand to all players in player pool
        dealer.dealHands()
        for player in self.players:
            your_turn_message = await ctx.send(embed = Embed(title = f"It's your turn, {player.name}!"))
            # send a message to discord chat telling player it's their turn to go.
            while player.done != True:
                try:
                    em = Embed(title=f"Your total is {player.sumCards()}.", description="Do you want to hit? React with a ✅ for yes, or 🚫 for no.")
                    input_message = await ctx.send(embed = em)
                    await input_message.add_reaction("✅")
                    await input_message.add_reaction("🚫")
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=15.0)
                    if (user == player.name) and (reaction.emoji == "✅"):
                        await input_message.delete()
                        dealer.dealCard(player)
                        if player.isBust():
                            player.done = True
                            await ctx.send(f"You busted! Your total is {player.sumCards()}")
                        else: 
                            continue
                    elif (user == player.name) and (reaction.emoji == "🚫"):
                        await input_message.delete()
                        player.done = True
                        await ctx.send(f"Okay, your turn is over.")
                        await your_turn_message.delete()
                except asyncio.TimeoutError:
                    await ctx.send("You took too long to react! Your turn is over.")
                    player.done = True
        #when all players are done with their turns
        self.players.append(dealer)
        # dealer is successfully getting added here
        await dealer_hand_message.edit(embed = Embed(title = f"Dealer's total is: {dealer.sumCards()}", description=f"The dealer's hand is: {dealer.hand}"))

        winners, ties = self.getWinners(self.players) 

        # if there are no winners, and no ties, send "Everyone lost."
        # else if there are winners, send "Here are our winners: "
        # else if there are no winners but there are ties, send "These players tied:"
        if (len(winners) == 0) and (len(ties) == 0):
            await ctx.send(embed = Embed(title="You're All Losers!"))
        elif len(winners) > 0:  
            winners = [winner.name.name for winner in winners]  
            await ctx.send(embed = Embed(title=f"Our Winners are: {winners}"))
        elif len(ties) > 0:
            ties = [tie.name.name for tie in ties]
            await ctx.send(embed = Embed(title=f"Our TieBabies are:{ties}"))
            
        
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
