import random
import logging
import asyncio
from cogs.economy import Economy
from config.config import BANK_PATH
from discord.ext.commands.cog import Cog
from discord.ext import commands
from discord import Member, Embed
from helper import getUserAmount



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
        self.name = ctx.author.name
        self.hand = []
        self.bust = False
        self.blackJack = False
        self.tie = False
        self.done = False
        if self.bust is True:
            self.done = True
        self.winner = False        
        self.bet = 0



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

# use playerqueue to queue up players and control the creation of game classes.
class PlayerQueue(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.q = []
    
    @commands.command("joinQ")
    async def joinQueue(self, ctx):
        new_player = Player(ctx)
        # check if person using command is already in the player pool
        for player, member in self.q:
            if ctx.author.name == player.name:
                # if so, tell user that they're already in the queue
                message_str = f"{ctx.author.name} is already in queue."
                message = await ctx.send(embed = Embed(title=message_str))
                await message.delete(delay=5.0)
                return
        # if not, add them to player pool

        # so Q will be a list of tuples of (player object, discord.Member object)
        self.q.append((new_player, ctx.author))
        message_str = f"{ctx.author.name} has been added to blackjack queue."
        message = await ctx.send(embed = Embed(title=message_str))
        await message.delete(delay=5.0)
        
    @commands.command("leaveQ")
    async def leaveQueue(self, ctx):
        # check if person using command is in player pool
        for player, member in self.q:
            if ctx.author.name == player.name:
                # if so, return the persons bet money to them, and remove them from player pool
                economy = Economy(self.bot)
                await economy.giveMoney(ctx, player.bet)
                self.q.remove((player, ctx.author))
                message_str = f"{ctx.author.name} has been removed from the queue."
                message = await ctx.send(embed = Embed(title=message_str))
                await message.delete(delay=5.0)
                return
        # if command caller isn't in player pool, tell them
        message_str = f"{ctx.author.name} is not in the queue."
        message = await ctx.send(embed = Embed(title=message_str))
        await message.delete(delay=5.0)

    @commands.command("clearQ")
    async def clearQueue(self, ctx):
        economy = Economy(self.bot)
        for player, member in self.q:
            if player.bet > 0:
                await economy.giveMoneyPlayer(player, player.bet)
        message = await ctx.send(embed= Embed(title = f"All players have been removed from queue."))
        await message.delete(delay=5.0)

    @commands.command("showPlayers")
    async def showQueue(self, ctx):
        players_string = ""
        for player, member in self.q:
            players_string += f"{player.name}\n"
        em = Embed(title="Players in Queue", description=f"{players_string}")
        await ctx.send(embed = em)

    @commands.command()
    async def setBet(self, ctx, bet:int):
        bet = int(bet)
        for player, member in self.q:
            if ctx.author.name == player.name:
                player.bet = bet
                # store players bet amount in corresponding player object
                economy = Economy(self.bot)
                withdraw_success = await economy.withdrawMoney(ctx, bet)
                if withdraw_success is False:
                    return
                message_str = f"{ctx.author.name} has placed a {bet} GleepCoin bet on the next game, to win {int(bet) * 2} GC."
                message = await ctx.send(embed = Embed(title=message_str))
                await message.delete(delay=7.5)
                return
        # otherwise, if player isn't in self.players ->
        message_str = f"You must join the queue before you can place a bet."
        message = await ctx.send(embed = Embed(title=message_str))
        await message.delete(delay=7.5)

    @commands.command()
    async def beg(self, ctx):
        economy = Economy(self.bot)
        amount = random.randint(1, 20)
        await economy.giveMoney(ctx, float(amount))
        beg_message = await ctx.send(embed=Embed(title=f"{ctx.author.name} recieved {amount} GleepCoins from begging."))
        await beg_message.delete(delay=5.0)

    @commands.command()
    async def playJack(self, ctx):
        blackjack = BlackJackGame(self.bot, self)
        await blackjack.play(ctx)

    
        




class Dealer(Player):
    def __init__(self, deck:Deck, players:list[Player]):
        self.name = "Dealer"
        self.deck = deck.deck
        self.players = players
        self.cards_in_play = []
        self.hand = []
        self.winner = False
        self.tie = False
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
    def __init__(self, bot:commands.Bot, player_queue:PlayerQueue):
        self.bot = bot
        self.deck = Deck()
        self.deck.shuffle()
        self.player_queue = player_queue.q
        self.players = []
        for player, member in self.player_queue:
            self.players.append(player)
        

        self.dealer = Dealer(self.deck, self.players)


    def resetPlayers(self) -> None:
        for player in self.players:
            player.winner = False
            player.done = False
            player.bust = False
            player.blackJack = False
            player.tie = False
            player.hand = []

    def showHands(self, players:list[Player]):
        for player in players:
            print(f"\n{player.name} shows their cards. Their hand looks like this: {player.hand}. ")

    async def cashOut(self, ctx, players):
        economy = Economy(self.bot)
        for player in players:
            if player.winner:
                winnings = player.bet * 2
                await economy.giveMoneyPlayer(player, winnings)
                message = await ctx.send(embed = Embed(title=f"{player.name} won {winnings} GleepCoins."))
                await message.delete(delay=5.0)
            elif player.tie:
                winnings = player.bet
                await economy.giveMoneyPlayer(player, winnings)
                message = await ctx.send(embed = Embed(title=f"{player.name} broke even, gaining back {winnings} GleepCoins."))
                await message.delete(delay=5.0)
                    
    
    def getWinners(self, players:Player) -> list[Player]:
        dealer = None
        winners = []
        tiebabies = []
        # get the dealer, store and remove dealer, remove players who have been busted
        for player in players:
            if player.name == "Dealer":
                dealer = player # save dealer object in variable dealer
                continue
        if dealer is None:
            print("There was an error - the dealer is not in the player pool")
            return
        
        #store dealer sum
        dealer_total = dealer.sumCards()
        #remove dealer from player pool 
        players.remove(dealer)

        # for the players who haven't busted or aren't the dealer: 
        for player in players:
            if not player.bust:
                if dealer_total > 21:
                    player.winner = True
                    winners.append(player)
                    continue
                if player.sumCards() > dealer_total:
                    player.winner = True
                    winners.append(player)
                elif player.sumCards() == dealer_total:
                    player.tie = True
                    tiebabies.append(player)
        
        # now winners holds all our winners, tiebabies holds anyone who's tied
        return winners, tiebabies

    async def play(self, ctx):
        self.resetPlayers()
        deck = Deck()
        deck.shuffle()
        # create a new dealer each round - he deals his own hand first, and shows his first card.
        dealer = Dealer(deck, self.players)
        dealer.dealToSelf()
        dealer_shows = Embed(title=f"Dealer's Showing: {dealer.hand[0][0]} of {dealer.hand[0][1]}.")
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
                    if (user.name == player.name) and (reaction.emoji == "✅"):
                        await input_message.delete()
                        dealer.dealCard(player)
                        if player.isBust():
                            player.done = True
                            await ctx.send(f"You busted! Your total is {player.sumCards()}")
                        else: 
                            continue
                    elif (user.name == player.name) and (reaction.emoji == "🚫"):
                        await input_message.delete()
                        player.done = True
                        await your_turn_message.delete()
                except asyncio.TimeoutError:
                    await ctx.send("You took too long to react! Your turn is over.")
                    player.done = True
        #when all players are done with their turns
        self.players.append(dealer)

        # dealer is successfully getting added here
        await dealer_hand_message.edit(embed = Embed(title = f"Dealer's total is: {dealer.sumCards()}", description=f"The dealer's hand is: {dealer.hand}"))

        # print(self.players)
        winners, ties = self.getWinners(self.players) 
        await self.cashOut(ctx, self.players)
        # if there are no winners, and no ties, send "Everyone lost."
        # else if there are winners, send "Here are our winners: "
        # else if there are no winners but there are ties, send "These players tied:"
        if (len(winners) == 0) and (len(ties) == 0):
            await ctx.send(embed = Embed(title="You're All Losers!"))
        elif len(winners) > 0:  
            winners = [winner.name for winner in winners]  
            await ctx.send(embed = Embed(title=f"Our Winners are: {winners}"))
        elif len(ties) > 0:
            ties = [tie.name for tie in ties]
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
    await bot.add_cog(PlayerQueue(bot))        
