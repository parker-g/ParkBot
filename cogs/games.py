import random
import logging
import asyncio
from collections import Counter
from cogs.economy import Economy
from config.config import BANK_PATH
from discord.ext.commands.cog import Cog
from discord.ext import commands
from discord import Member, Embed, TextChannel, Thread
from helper import getUserAmount, readThreads, writePlayerAndThread, bubbleSortCards

# things to do 
    # finish poker logic
        # make sure player's best hands are stored in possible_hands
        # handle tie cases in _getWinners()
    # test/ debug poker logic
    # implement Card class
    # change Player class to include a players discord.Member object representation as an attribute - ultimately allowing the playerqueue.q to just be a simple list of Player objects

logger = logging.Logger('BJLog')

# blackjack note - 
# need to modify game play function so that 
    # dealer deals cards to players besides himself
    # dealer deals himself two cards, shows only one
    # let players play their hands

    # dealer reveals his second card, dealer plays till over 17 
    # for players that haven't busted:
        # compare player score to dealer score
        # if player score higher, player added to winners
        # if player score lower, do nothing

class Card:
    """
    The Card is the most basic data structure used in the games cog.\n
    Make sure to specify which game your card will be used for when constructing cards.
    attributes -
    :str suit: The suit of the card in word form.
    :int pip_value: Value of the card in integer form - can change depending on the game where the card is used."""

    # PIP EXPLANATION | EXPLAIN PIP | PIP
    # "pip" value is a term used to describe a card's value in a numerical form. in 'pip' form, a jack would be an 11, a queen would be a 12, etc
    FACE_TO_PIP_POKER = {
         "2": 2,
         "3": 3,
         "4": 4,
         "5": 5,
         "6": 6,
         "7": 7,
         "8": 8,
         "9": 9,
         "10": 10,
         "jack": 11,
         "queen": 12,
         "king": 13,
         "ace": 14,
    }
    PIP_TO_FACE_POKER = {
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
        14: "ace",
    }
    PIP_TO_FACE_BLACKJACK = {
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
    FACE_TO_PIP_BLACKJACK = {
         "ace": 1,
         "2": 2,
         "3": 3,
         "4": 4,
         "5": 5,
         "6": 6,
         "7": 7,
         "8": 8,
         "9": 9,
         "10": 10,
         "jack": 11,
         "queen": 12,
         "king": 13,
    }
    SUIT_SYMBOL_TO_STRING = {
        "♠": "spade",
        "♣": "club",
        "♥": "heart",
        "♦": "diamond",
    }
    SUIT_STRING_TO_SYMBOL = {
        "spade": "♠",
        "club": "♣",
        "heart": "♥",
        "diamond": "♦",
    }
    SUIT_TO_COLOR = {
        "♠": "black",
        "♣": "black",
        "♥": "red",
        "♦": "red",
    }


    def __init__(self, game:str, value: int | str, suit:str):
        """
        str - game : A string representing which game the card will be used for. Important because card values vary from game to game.\n
        int | str - value : The value of the card you're creating. Accepted as a lowercase string such as <"jack", "ace", "2"> or an integer value such as <2, 7, 14>.
        str - suit : String representing the suit of the card being constructed. Accepts strings in word format or simple unicode symbol format.
        """

        if suit in Card.SUIT_STRING_TO_SYMBOL:
            self.suit = suit
        elif suit in Card.SUIT_SYMBOL_TO_STRING:
            self.suit = Card.SUIT_SYMBOL_TO_STRING[suit]
        else:
            raise ValueError("Inappropriate argument value of `suit`. Refer to Card class for valid argument options.")
        
        match game:
            case "blackjack":
                if isinstance(value, str):
                    self.face_value = value
                    self.pip_value = Card.FACE_TO_PIP_BLACKJACK[value]
                elif isinstance(value, int):
                    self.pip_value = value
                    self.face_value = Card.PIP_TO_FACE_BLACKJACK[value]
            case "poker":
                if isinstance(value, str):
                    self.face_value = value
                    self.pip_value = Card.FACE_TO_PIP_POKER[value]
                elif isinstance(value, int):
                    self.pip_value = value
                    self.face_value = Card.PIP_TO_FACE_POKER[value]
            case _:
                raise ValueError("Game parameter must be a valid game string: 'blackjack' or 'poker' are the only acceptable inputs.")
                
        self.suit = suit
    
    def setValue(self, new_value:int) -> None:
        self.pip_value = new_value

    def getValuePip(self) -> int:
        return self.pip_value
    
    def getValueString(self) -> str:
        return self.face_value

    def getSuit(self) -> str:
        """
        Returns suit of a card, in word form - example: 'spade'"""
        return self.suit

    def getSuitSymbol(self) -> str:
        return Card.SUIT_STRING_TO_SYMBOL[self.suit]
    
    def stringify(self):
        return f"{self.face_value.capitalize()} {self.getSuitSymbol()}"



class Deck:
    """ The Deck class represents a deck of 52 cards - meaning Jokers are not present in this deck.\n 
    Each card in the deck is represented as a tuple of (num, suit).\n
    This class provides methods for working with a deck such as  `.shuffle()`, and for pretty printing cards.
    """

    blackjack_face_legend = {
        "ace": 1,
        "jack": 10,
        "queen": 10,
        "king": 10,
    }

    def __init__(self, game:str):
        """
        Game accepts 'poker' or 'blackjack' as arguments.\n
        :attr list self.deck: A list of Card objects. Populates according to the game that the deck will be used for."""
        self.deck = [] # list of Card
        match game.lower():
            case "blackjack":
                for i in range(1, 14):
                    self.deck.append(Card(game, i, "spade"))
                    self.deck.append(Card(game, i, "club"))
                    self.deck.append(Card(game, i, "heart"))
                    self.deck.append(Card(game, i, "diamond"))
            case "poker":
                # texas hold em poker uses 2 decks at a time
                for i in range(2):
                    for i in range(1, 14):
                        self.deck.append(Card(game, i, "spade"))
                        self.deck.append(Card(game, i, "club"))
                        self.deck.append(Card(game, i, "heart"))
                        self.deck.append(Card(game, i, "diamond"))

    def shuffle(self) -> None:
        random.shuffle(self.deck)

class Player(Cog):
    def __init__(self, ctx):
        self.name = ctx.author.name
        self.hand = []
        self.bet = 0
        self.done = False
        self.winner = False  

        #blackjack attributes
        self.bust = False
        self.blackJack = False
        self.tie = False
        if self.bust is True:
            self.done = True
              
        # poker attributes
        self.button = False
        self.thread = None
        self.folded = False
        self.hand_rank = 16
        # the combination of a player's cards and the community cards (7 cards) - stored in pip format
        self.complete_hand:list[Card] = []
        # a player's best hand, which assigned them their hand_rank (5 or less cards) 
        self.ranked_hand = []
        # possible_hands contains a player's best possible hand at each possible hand rank
        self.possible_hands:dict[int, list[Card]] = {}
    
    # poker method. ACTUALLY NOT USED LOL
    def setBestHand(self, new_best_hand:list) -> None:
        self.ranked_hand = new_best_hand

    def resetPlayer(self) -> None:
        """
        Resets a player's state attributes."""
        self.hand = []
        self.bet = 0
        self.done = False
        self.winner = False

    def pushToPot(self, pot) -> None:
        """
        Pushes a player's current bet to the input pot, and clears the player's current bet."""
        pot += self.bet
        self.bet = 0

    def sumCards(self) -> int:
        """
        Returns the sum of card values in the player's hand."""
        total = 0
        for card in self.hand:
            total += card.pip_value
        return total

    def isBlackJack(self) -> bool:
        """
        If player has blackjack, sets the player's blackjack attribute to True and returns it.\n
        Otherwise, returns False."""
        if self.sumCards() == 21:
            self.blackJack = True
        return self.blackJack

    def isBust(self) -> bool:
        """
        Checks if a player has busted. Returns True if so, False otherwise."""
        if self.sumCards() > 21:
            self.bust = True
        return self.bust
    
    def prettyHand(self) -> str:
        """
        Returns a pretty string representing a player's hand of cards."""
        pretty_string = "A"
        for card in self.hand[:-1]:
            suit_symbol = Card.SUIT_STRING_TO_SYMBOL[card.suit]
            pretty_string += f" {card.pip_value} {suit_symbol}, "
        last_card = self.hand[-1]
        last_symbol = Card.SUIT_STRING_TO_SYMBOL[last_card.suit]
        pretty_string += f"{last_card.pip_value} {last_symbol}"
        return pretty_string

    # used in Poker
    def addCardsToHand(self, community_cards:list) -> list[Card]: # tuple(value, int)
        """
        Combines a player's hand with the community cards on the table, returns them in a new list.\n
        I use the term 'complete hand' to refer to a hand which including BOTH the player's cards, and the community cards.\n
        """
        return self.hand + community_cards



# use playerqueue to queue up players and control the creation of game classes.
class PlayerQueue(Cog):
    """
    The PlayerQueue class is used as a controller of the games available in the games.py 'cog'.\n
    self.q is a list[Card]. Each player is stored as a tuple of (Player, Discord.Member) objects so that we can easily access methods to discord members.
    Right now, I'm actually realizing that it would be much more simple if I instead just incorporated the discord.Member object into the Player class as an attribute. Removing the possibility of confusing others with tuples in the player queue."""
    def __init__(self, bot):
        self.bot = bot
        self.q = []

    @commands.command("joinQ")
    async def joinQueue(self, ctx):
        """
        This is a command giving Discord server members the ability to join the PlayerQueue, by executing the command in a text channel."""
        new_player = Player(ctx)
        # check if person using command is already in the player pool
        for player, member in self.q:
            if ctx.author.name == player.name:
                # if so, tell user that they're already in the queue
                message_str = f"{ctx.author.name} is already in queue."
                message = await ctx.send(embed = Embed(title=message_str))
                await message.delete(delay=5.0)
                return

        # so Q will be a list of tuples of (player object, discord.Member object)
        self.q.append((new_player, ctx.author))
        message_str = f"{ctx.author.name} has been added to players queue."
        message = await ctx.send(embed = Embed(title=message_str))
        await message.delete(delay=5.0)
        
    @commands.command("leaveQ")
    async def leaveQueue(self, ctx):
        """
        This command gives users the ability to leave the PlayerQueue. If a player leaves the queue, any bet they had previously set will be returned to their bank."""
        # check if person using command is in player pool
        for player, member in self.q:
            if ctx.author.name == member.name:
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
        """
        Discord server members can clear the PlayerQueue with this command."""
        economy = Economy(self.bot)
        for player, member in self.q:
            if player.bet > 0:
                await economy.giveMoneyPlayer(player, player.bet)
                player.bet = 0
            self.q.remove((player, member))
            
        message = await ctx.send(embed= Embed(title = f"All players have been removed from queue."))
        await message.delete(delay=5.0)

    @commands.command("showPlayers")
    async def showQueue(self, ctx):
        """
        This command provides users the ability to see who is currently in the PlayerQueue."""
        players_string = ""
        for player, member in self.q:
            players_string += f"{player.name}\n"
        em = Embed(title="Players in Queue", description=f"{players_string}")
        await ctx.send(embed = em)

    async def _setBet(self, ctx, inputPlayer, bet:int):
        """
        This method accomplishes the same thing as the setBet() method, without sending messages to the Discord chat."""
        bet = int(bet)
        for player, member in self.q:
            if inputPlayer.name == player.name:
                # store players bet amount in corresponding player object
                economy = Economy(self.bot)
                try:
                    withdraw_success = await economy.withdrawMoneyPlayer(ctx, inputPlayer, bet)
                    if withdraw_success is False:
                        return False
                    elif withdraw_success is True:
                        player.bet = bet
                        return True
                except Exception as e:
                    print(f"Error while _setBet executing for player, {player.name} : {e}")

    @commands.command()
    async def setBet(self, ctx, bet:int):
        """
        Discord users who have joined the PlayerQueue can use this command to set a bet, valid for the next game of BlackJack.\n"""
        bet = int(bet)
        for player, member in self.q:
            if ctx.author.name == player.name:
                # store players bet amount in corresponding player object
                economy = Economy(self.bot)
                withdraw_success = await economy.withdrawMoney(ctx, bet)
                if withdraw_success is False:
                    return
                player.bet = bet
                message_str = f"{ctx.author.name} has placed a {bet} GleepCoin bet on the next BlackJack game, to win {int(bet) * 2} GC."
                message = await ctx.send(embed = Embed(title=message_str))
                await message.delete(delay=7.5)
                return
        # otherwise, if player isn't in self.players ->
        message_str = f"You must join the queue before you can place a bet."
        message = await ctx.send(embed = Embed(title=message_str))
        await message.delete(delay=7.5)

    @commands.command()
    async def beg(self, ctx):
        """
        Players who have exhausted their bank account can use this command to make money."""
        economy = Economy(self.bot)
        amount = random.randint(1, 20)
        await economy.giveMoney(ctx, float(amount))
        beg_message = await ctx.send(embed=Embed(title=f"{ctx.author.name} recieved {amount} GleepCoins from begging."))
        await beg_message.delete(delay=5.0)

    @commands.command()
    async def playJack(self, ctx):
        """
        This command is the PlayerQueue's interface with a blackjack game. It begins a game of blackjack, using all the players in the queue."""
        blackjack = BlackJackGame(self.bot, self)
        await blackjack.play(ctx)

    @commands.command()
    async def playPoker(self, ctx):
        """
        This command puts all players in the PlayerQueue in a game of Texas Hold'em Poker."""
        poker = Poker(self.bot, self)
        await poker.play(ctx)



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

    # poker methods
    def dealFlop(self, poker_instance) -> None:
        """
        Ejects top card then deals three cards to the community cards."""
        # throw out the top card
        self.deck.pop(0)
        self.dealPokerCommunityCard(poker_instance, 3)
    
    def dealPokerCommunityCard(self, poker_instance, cards = 1) -> None:
        """
        Deals `cards` amount of cards to the `poker_instance`'s community cards."""
        for i in range(cards):
            poker_instance.community_cards.append(self.deck[0])
            self.deck.pop(0)

    def dealCard(self, player:Player) -> None:
        """
        Removes one card from this `Dealer`'s deck and puts that card in the `player`'s hand."""
        player.hand.append(self.deck[0])
        self.cards_in_play.append(self.deck[0])
        self.deck.remove(self.deck[0])

    def dealHands(self) -> None:
        """
        Deals 2 cards to each player.\n
        Used in Blackjack and Poker."""
        for i in range(2):
            for player in self.players:
                self.dealCard(player)

    #return cards doesn't work, need to fix maybe.
    def returnCardsToDeck(self) -> None:
        self.deck = self.deck + self.cards_in_play
        self.cards_in_play.clear()

    def sumCards(self) -> int:
        """
        Returns sum of cards in the dealer's hand."""
        total = 0
        for card in self.hand:
            total += card.pip_value
        return total

    def dealToSelf(self) -> None:
        """
        Dealer deals cards to himself until he reaches 17 or busts."""
        while self.sumCards() < 17:
            self.dealCard(self)
        return
    
    ##################################################### not sure this is actually used
    def isBlackjack(self, player:Player) -> None:
        if player.sumCards() == 21:
            player.blackJack = True
    ####################################################
    def isBust(self) -> None:
        if self.sumCards() > 21:
            self.bust = True
    ################################################### not sure if isBust is used either

class BlackJackGame(Cog):
    def __init__(self, bot:commands.Bot, player_queue:PlayerQueue):
        self.bot = bot
        self.player_queue = player_queue.q
        self.players = []
        for player, member in self.player_queue:
            self.players.append(player)
        


    def resetPlayers(self) -> None:
        for player in self.players:
            player.winner = False
            player.done = False
            player.bust = False
            player.blackJack = False
            player.tie = False
            player.hand = []

    def showHands(self, players:list[Player]) -> None:
        for player in players:
            print(f"\n{player.name} shows their cards. Their hand looks like this: {player.hand}. ")
    
    async def cashOut(self, ctx, players) -> None:
        """
        Method used to award players who didn't lose in the most recent hand of blackjack."""
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
                    
    

    # clean up / make this not fucky wucky
    def getWinners(self, players:list[Player]) -> tuple[list, list]:
        """
        Returns a tuple of (winners, tiers). \n
        May return None if the dealer has been removed from the player pool."""
        dealer = None
        winners = []
        tiebabies = []
        # get the dealer, store and remove dealer, remove players who have been busted
        for player in players:
            if player.name == "Dealer":
                dealer = player # save dealer object in variable dealer
                continue
        if dealer is None:
            raise Exception("The dealer was prematurely removed from the player pool somewhere along the way. Please reboot the BlackJack cog.")
        
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
        """
        Wrapper method to hold and execute all the BlackJack logic in a sequential order."""
        self.resetPlayers()
        deck = Deck("blackjack")
        deck.shuffle()
        # create a new dealer each round - he deals his own hand first, and shows his first card.
        dealer = Dealer(deck, self.players)
        dealer.dealToSelf()
        dealer_shows = Embed(title=f"Dealer's Showing: {dealer.hand[0].face_value} of {dealer.hand[0].getSuitSymbol()}.")
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

        await dealer_hand_message.edit(embed = Embed(title = f"Dealer's total is: {dealer.sumCards()}", description=f"The dealer's hand is: {dealer.hand}"))

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

# could lowkey create a Game super class that BlackJack and Poker would inherit from - simply making them share attributes such as the 
# bot, deck, player queue, players, and dealer.



class Poker(commands.Cog):
    """
    The Poker class contains all logic necessary for carrying out a game of texas hold'em poker and evaluating winners for a game.
    
    attributes required for construction:
    :discord.ext.commands.Bot bot: A discord Bot object, used to communicate with Discord servers.\n
    :Deck deck: A Deck object representing two decks to be used in a poker game.\n
    :PlayerQueue player_queue: A PlayerQueue object which is used to access the players who are in the game.\n
    :list players: The list that becomes populated with any players in the game whenever a Poker game is constructed.\n
    :Dealer dealer: A Dealer is used to deal cards to the community and to the rest of the players in the Poker game.\n
    
    attributes instantiated upon construction:
    :list[Card] community_cards: The cards available to any player in the game to help them form the best hand possible.\n
    :int small_blind: Used to store the small blind, set during a game of Poker.\n
    :int big_blind: Used to store the big blind, set during a game of Poker.\n
    :int small_blind_idx: The index of the player in self.players who sets the small blind.\n
    :int big_blind_idx: The index of the player in self.players who sets the big blind.\n
    :discord.TextChannel channel: A text channel accessed in your Discord server where the bot will send poker related messages, necesary to run the game.\n
    :dict[str, discord.Thread] threads: A dictionary used to store private threads for each player in the game. These threads are used to privately send players their poker hand.\n
    :int pot: Represents the pot of bets in a game of Poker.\n
    :bool postFlop: A boolean used as a way to control state of the poker game.\n
    :bool earlyFinish: A boolean used to control state of poker game, if True, game ends early as all players but 1 have folded.\n
    """
    HANDS_TO_RANKS = {
        "royal flush": 0,
        "straight flush": 1,
        "four of a kind": 2,
        "full house": 3,
        "flush": 4,
        "straight": 5,
        "three of a kind": 6,
        "two pair": 7,
        "pair": 8, 
        "high card": 9,
    }

    def __init__(self, bot, player_queue:PlayerQueue):
        self.bot = bot
        self.deck = Deck("poker")
        self.deck.shuffle()
        self.player_queue = player_queue
        self.players:list[Player] = []
        for player, member in self.player_queue.q:
            self.players.append(player)
        self.dealer = Dealer(self.deck, self.players)
        
        # poker specific attributes 
        self.community_cards:list[Card] = []
        self.small_blind = 0
        self.big_blind = 0
        self.small_blind_idx = None
        self.big_blind_idx = 0
        self.channel = None
        self.threads:dict[str, int] = {} # contains player names as keys, and discord.Thread IDs as values - used to send private messages to players
        self.pot = 0 # holds all bets
        self.post_flop = False # used to modify the self.takeBets() method to make it appropriate for a pre-flop vs a post flop betting round
        self.early_finish = False # responsible for state of whether a game has ended early (due to all but 1 player folding)

    async def resetPlayers(self) -> None:
        """
        Resets all of each player's attributes relating to their game state."""
        economy = Economy(self.bot)
        if self.players:
            for player in self.players:
                player.winner = False
                player.done = False
                player.hand = []
                player.button = False
                player.thread = None
                player.folded = False
                if player.bet > 0:
                    await economy.giveMoneyPlayer(player, player.bet)
                    player.bet = 0



    def getCommunityCardsString(self) -> str:
        """
        Returns the community cards in one long string."""
        pretty_string = ""
        for card in self.community_cards:
            pretty_string += f"{(card.stringify())}\n"
        return pretty_string

    def allPlayersDone(self) -> bool:
        """
        Checks if all players are done, returns True if so. Otherwise, returns False."""
        for player in self.players:
            if player.done == False:
                return False
        return True

    def getThreads(self) -> None:
        """
        Stores any previously used discord threads in memory for sending poker hands to players during the upcoming game of Poker.
        """
        self.threads = readThreads()
        return

    def writeNewThread(self, player, thread_id:int) -> None:
        """
        Writes a username and their discord thread identifier to the threads.csv file.
        """
        writePlayerAndThread(player.name, thread_id)
        return
    
    def setPlayersNotDone(self) -> None:
        """
        Sets all player's done attribute to False. Used when resetting all players' states."""
        for player in self.players:
            player.done = False

    async def showAllHands(self, ctx) -> None:
        """
        Sends a message containing each player's hand to the discord text channel where the Poker game is being held."""
        all_hands = ""
        for player in self.players:
            all_hands += f"{player.name}: {player.prettyHand()}\n"
        await ctx.send(embed=Embed(title=f"Everyone's Hand", description=all_hands))

    async def showHands(self):
        """
        Sends a private thread to each player active in the game, containing their current hand\n
        Stores each player and their thread ID in a file, 'threads.csv', for use during later Poker games.
        """
        for player in self.players:
            member = [user for user in self.player_queue.q if user[0].name == player.name][0][1]
            if not player.name in self.threads:
                # print(f"creating thread for {player.name}")
                thread = await self.channel.create_thread(name="Your Poker Hand", reason = "poker hand", auto_archive_duration = 60)
                self.threads[player.name] = thread.id
                writePlayerAndThread(player, thread.id)
                # need to invite player's Member object to thread
                await thread.send(embed = Embed(title="Your Hand", description=f"{player.prettyHand()}\n{member.mention}"))
                await thread.add_user(member)
            elif player.name in self.threads:
                # print(f"using thread for {player.name}")
                thread_id = self.threads[player.name]
                # print(f"Thread id: {thread_id}")
                thread = await self.guild.fetch_channel(thread_id)
                # print(f"thread type: {type(thread)}")
                await thread.send(embed = Embed(title="Your Hand", description=f"{player.prettyHand()}\n{member.mention}"))

    # button moves clockwise, clockwise will be rightwards -> for our purposes
    async def progressButton(self):
        for i in range(len(self.players)-1):
            # find player who has button, pass button to next player
            if self.players[i].button is True:
                self.players[i].button = False
                if self.players[i+1] is None:
                    self.players[0].button = True
                else:
                    self.players[i+1].button = True
                return

    async def getPokerChannel(self, ctx) -> TextChannel:
        async for guild in self.bot.fetch_guilds():
            if guild.name == "Orlando Come":
                self.guild = guild
                channels = await guild.fetch_channels()
                for channel in channels:
                    if channel.name == "poker":
                        return channel
        raise Exception("Your guild isn't named Orlando Come, or you don't have a text channel named poker. Please change this code Parker to be more easy to use for other people. Perhaps create a new channel named poker and then access that one after its created.")
    
    async def assignButtonAndPostBlinds(self, ctx):
        """
        Assigns the button to a random player, and takes the blinds from the players directly after and 2 players after the button player."""
        num_players = len(self.players)
        if num_players < 2:
            await ctx.send(f"You don't have enough players to play Poker.")
        i = random.randint(0, num_players-1)
        self.players[i].button = True
        button_msg = await ctx.send(embed=Embed(title=f"{self.players[i].name} holds the button this round."))
        await button_msg.delete(delay=10.0)
        if i == num_players - 1 :
            self.small_blind_idx = 0
            self.big_blind_idx = 1
        elif i == num_players - 2:
            self.small_blind_idx = -1
            self.big_blind_idx = 0
        else:
            self.small_blind_idx = i + 1
            self.big_blind_idx = i + 2
        small_blind_player = self.players[self.small_blind_idx]
        big_blind_player = self.players[self.big_blind_idx]
        await ctx.send(embed=Embed(title=f"Game Info:", description= f"Button :{self.players[i].name} \nSmall blind: {small_blind_player.name} \nBig blind: {big_blind_player.name}"))
        input_message = await ctx.send(embed = Embed(title=f"Post the small blind, {small_blind_player.name}.", description=f"{small_blind_player.name}, type the amount of GleepCoins to set as small blind."))
        while self.small_blind == 0:
            message = await self.bot.wait_for("message", timeout = None)
            if message.author.name == small_blind_player.name:
                try:
                    small_blind = int(message.content)
                    is_success = await self.player_queue._setBet(ctx, small_blind_player, small_blind)
                    small_blind_player.pushToPot(self.pot)

                    # if the withdrawal was successful, (player's bet amount increased from 0), continue
                    if is_success is True:
                        self.small_blind = small_blind
                        await ctx.send(embed = Embed(title=f"Small blind posted at {small_blind} GleepCoins."))
                except ValueError or TypeError:
                    error_message = await ctx.send(embed=Embed(title="Please type a valid number."))
                    await error_message.delete(delay=7.0)
        await input_message.delete(delay=15.0)
        big_message = await ctx.send(embed=Embed(title=f"Post the big blind, {big_blind_player.name}."))
        while self.big_blind == 0:
            big_message = await self.bot.wait_for("message", timeout = None)
            if big_message.author.name == big_blind_player.name:
                try:
                    big_blind = int(big_message.content)
                    if big_blind <= self.small_blind:
                        error_msg = await ctx.send(embed=Embed(title=f"Big blind must be larger than small blind. Please type a number larger than {self.small_blind}."))
                        await error_msg.delete(delay = 7.0)
                    elif big_blind > self.small_blind:
                        success = await self.player_queue._setBet(ctx, big_blind_player, big_blind)
                        big_blind_player.pushToPot(self.pot)
                        if success is True:
                            self.big_blind = big_blind
                            self.min_bet = self.big_blind
                            big_blind_alert = await ctx.send(embed = Embed(title=f"Big blind posted at {big_blind} GleepCoins."))
                            await big_blind_alert.delete(delay = 7.0)
                            
                except ValueError or TypeError:
                    int_error = await ctx.send(embed = Embed(title=f"Please type a valid integer."))
                    await int_error.delete(delay = 7.0)
        self.pot += self.big_blind
        return

    async def takePreFlopBets(self, ctx):
        if self.early_finish is not True:
            economy = Economy(self.bot)
            self.setPlayersNotDone()
            max_idx = len(self.players)
            initial_bet = self.big_blind
            min_bet = initial_bet
            
            for i in range(100): # make iteration unreasonably high to ensure we don't reach it's limit
                player_idx = i + self.big_blind_idx
                if player_idx >= max_idx:
                    player_idx = player_idx % max_idx 
                print(f"player_index: {player_idx}")

                player = self.players[player_idx]
                member = [user for user in self.player_queue.q if user[0].name == player.name][0][1]
                
                if player.bet < min_bet:
                    player.done = False
                
                message_embed = Embed(title=f"Pre-Flop Betting", description=f"{member.mention}\nWould you like to call 📞, raise 🆙, or fold 🏃‍♂️?")
                # 📞 call emoji, 🏃‍♂️ fold emoji, 🆙 raise emoji
                while player.done != True:
                    input_message = await ctx.send(embed=message_embed)
                    await input_message.add_reaction("📞")
                    await input_message.add_reaction("🆙")
                    await input_message.add_reaction("🏃‍♂️")
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0)
                        emoji = reaction.emoji
                        if (user.name == player.name):
                            match emoji:
                                case "📞":
                                    isSuccess = await self.player_queue._setBet(ctx, player, min_bet)
                                    if isSuccess:
                                        await ctx.send(embed=Embed(title=f"{player.name} called the bet, {min_bet} GleepCoins."))
                                        player.done = True
                                        
                                case "🆙":
                                    await ctx.send(embed=Embed(title=f"Okay, set a bet higher than {min_bet}.", description=f"Please type your bet to raise."))
                                    raise_message = await self.bot.wait_for("message")
                                    try:
                                        raise_amount = int(raise_message.content)
                                        if raise_amount <= min_bet:
                                            await ctx.send(embed=Embed(title=f"That bet was too small. Please react and try again."))
                                        else:
                                            success = await self.player_queue._setBet(ctx, player, raise_amount)
                                            if success is False:
                                                await ctx.send(embed=Embed(title=f"Get ya money up, not ya funny up.", description=f"Transaction failed. Maybe it's because you only got {economy._getBalance(self.players[i])}.\nTry again, with a lower amount, or you might have to fold."))
                                                continue
                                            elif success is True:
                                                await ctx.send(embed=Embed(title=f"{player.name} raised to {raise_amount}."))
                                                min_bet = raise_amount
                                                player.done = True

                                    except ValueError as e:
                                        print(f"Error casting your message to integer:", e)
                                        await ctx.send(f"That was an invalid integer. Please react and then try again.")
                                        continue
                                case "🏃‍♂️":
                                    # in a fold, mans doesnt place a bet, he just is done betting, and leaves the active players.
                                    leave_message = await ctx.send(embed=Embed(title=f"{player.name} folded. Nice.", description=f"You forfeited {player.bet} GleepCoins to the pot."))
                                    await leave_message.delete(delay=5.0)
                                    player.pushToPot(self.pot)
                                    self.players.remove(player)
                                    max_idx -= 1
                                    player.done = True

                    except asyncio.TimeoutError:
                        player.pushToPot(self.pot)
                        self.players.remove(player)
                        max_idx -= 1
                        player.done = True
                        await ctx.send(embed=Embed(title=f"You took too long, dummy (baltimore accent).", description=f"You automatically folded."))  
                if (len(self.players) == 1):
                    self.players[0].winner = True
                    await ctx.send(embed=Embed(title=f"{self.players[0].name} is the last player standing.", description=f"{self.players[0].name} will receive the pot of {self.pot} GleepCoins."))
                    self.early_finish = True    
                if self.allPlayersDone():
                    # only push players bets to the pot at the end of all betting for the round
                    for player in self.players:
                        player.pushToPot(self.pot)
                    break
            pf_msg = await ctx.send(embed=Embed(title=f"Pre flop betting has come to an end.", description=f"Current Pot: {self.pot} GleepCoins."))
            await pf_msg.delete(delay=10.0)
            return
        else:
            return
        
    async def takePostFlopBets(self, ctx, name_of_betting_round):
        if self.early_finish is not True:
            economy = Economy(self.bot)
            self.setPlayersNotDone()
            max_idx = len(self.players)
            min_bet = 0
            print(f"Max index: {max_idx}")
            for i in range(100): # make iteration unreasonably high to ensure we don't reach it's limit
                player_idx = i + self.big_blind_idx
                if player_idx >= max_idx:
                    player_idx = player_idx % max_idx 
                print(f"player_index: {player_idx}")

                player = self.players[player_idx]
                member = [user for user in self.player_queue.q if user[0].name == player.name][0][1]
                
                if player.bet < min_bet:
                    player.done = False

                if self.allPlayersDone():
                    break

                message_embed = Embed(title=f"Taking bets for the {name_of_betting_round.capitalize()}", description=f"{member.mention}\nWould you like to raise 🆙, check ✔️, fold 🏃‍♂️, or call 📞?")
                if min_bet == 0:
                    message_embed = Embed(title=f"Taking bets for the {name_of_betting_round.capitalize()}", description=f"{member.mention}\nWould you like to bet 🆙, check ✔️, or fold 🏃‍♂️?")
                

                # 📞 call emoji, 🏃‍♂️ fold emoji, 🆙 raise emoji, ✔️ check emoji
                while player.done != True:
                    input_message = await ctx.send(embed=message_embed)
                    await input_message.add_reaction("🆙")
                    await input_message.add_reaction("✔️")
                    await input_message.add_reaction("🏃‍♂️")
                    if (min_bet > 0):
                        await input_message.add_reaction("📞")
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0)
                        emoji = reaction.emoji
                        if (user.name == player.name):
                            match emoji:
                                case "📞":
                                    isSuccess = await self.player_queue._setBet(ctx, player, min_bet)
                                    if isSuccess:
                                        await ctx.send(embed=Embed(title=f"{player.name} called the bet, {min_bet} GleepCoins."))
                                        player.pushToPot(self.pot)
                                        player.done = True
                                        
                                case "🆙":
                                    await ctx.send(embed=Embed(title=f"Okay, set a bet higher than {min_bet}.", description=f"Please type your bet to raise."))
                                    raise_message = await self.bot.wait_for("message")
                                    try:
                                        raise_amount = int(raise_message.content)
                                        if raise_amount <= min_bet:
                                            await ctx.send(embed=Embed(title=f"That bet was too small. Please react and try again."))
                                        else:
                                            success = await self.player_queue._setBet(ctx, player, raise_amount)
                                            if success is False:
                                                await ctx.send(embed=Embed(title=f"Get ya money up, not ya funny up.", description=f"Transaction failed. Maybe it's because you only got {economy._getBalance(self.players[i])}.\nTry again, with a lower amount, or you might have to fold."))
                                                continue
                                            elif success is True:
                                                await ctx.send(embed=Embed(title=f"{player.name} raised to {raise_amount}."))
                                                player.pushToPot(self.pot)
                                                min_bet = raise_amount
                                                player.done = True

                                    except ValueError as e:
                                        print(f"Error casting your message to integer:", e)
                                        await ctx.send(f"That was an invalid integer. Please react and then try again.")
                                        continue
                                case "✔️":
                                    if self.post_flop is True:
                                        player.done = True
                                        check_msg = await ctx.send(embed=Embed(title=f"{player.name} checked."))
                                        await check_msg.delete(delay=7.0)
                                    else:
                                        await ctx.send(embed=Embed(title=f"You can't check before the flop goofball!"))
                                        continue
                                case "🏃‍♂️":
                                    # in a fold, mans doesnt place a bet, he just is done betting, and leaves the active players.
                                    self.players.remove(player)
                                    max_idx -= 1
                                    leave_message = await ctx.send(embed=Embed(title=f"{player.name} folded. Nice."))
                                    await leave_message.delete(delay=5.0)
                                    player.done = True
                    except asyncio.TimeoutError:
                        self.players.remove(player)
                        max_idx -= 1
                        player.done = True
                        await ctx.send(embed=Embed(title=f"You took too long, dummy (baltimore accent).", description=f"You automatically folded."))  
                if (len(self.players) == 1):
                    self.players[0].winner = True
                    await ctx.send(embed=Embed(title=f"{self.players[0].name} is the last player standing."))
                    self.early_finish = True    
                
            pf_msg = await ctx.send(embed=Embed(title=f"Pre flop betting has come to an end."))
            await pf_msg.delete(delay=10.0)
            return
        else:
            return

    def getHandRankAndPossibleHands(self, player:Player) -> int:
        """
        Checks all possibilities for a player's hand, returns the best hand a player has in the form of an integer.\n
        This integer corresponds to a key in the possible_hands dictionary.\n
        Lower is better.
        """
        possible_scores = []
        possible_hands = {
            0: [], #royal flush [10, 11, 12, 13, 14]
            1: [],
            2: [],
            3: [],
            4: [],
            5: [],
            6: [],
            7: [],
            8: [],
            9: [], # high card
        }
        ranker = PokerRanker
        player.complete_hand = player.addCardsToHand(self.community_cards)
        player_hand = player.complete_hand # complete hand in pip value
        bubbleSortCards(player_hand)

        # hand's now in pip value and sorted in ascending order
        flushes = ranker.getFlushes(player_hand)
        straights = ranker.getStraights(player_hand)
        if (flushes is not None) and (straights is not None):
            straight_flushes = ranker.getStraightFlushes(straights, flushes)
            if straight_flushes is not None:
                royal_flush = ranker.getRoyalFlush(straight_flushes)
                if royal_flush is not None:
                    rank = 0 # royal flush
                    possible_scores.append(rank) 
                    possible_hands[rank].append(royal_flush)
                else:
                    rank = 1 # straight flush
                    possible_scores.append(rank) 
                    possible_hands[rank].append(ranker.getBestStraightFlush(straight_flushes))
        elif straights is not None:
            rank = 5 # straight
            possible_scores.append(rank) 
            possible_hands[rank].append(ranker.getBestStraight(straights))
        elif flushes is not None:
            rank = 4 # flush
            possible_scores.append(rank)
            possible_hands[rank].append(ranker.getBestFlush(flushes))
        full_house = ranker.getFullHouse(player_hand)
        if full_house is not None:
            rank = 3 # full house
            possible_scores.append(rank) 
            possible_hands[rank].append(full_house) 

        max_occurences = ranker.getMaxOccurences(player_hand)
        if max_occurences <= 4:
            match max_occurences:
                case 4:
                    rank = 2 # 4 of a kind
                    player_hand = ranker.getNofAKind(max_occurences, player_hand)
                case 3:
                    rank = 6 # three of a kind
                    player_hand = ranker.getNofAKind(max_occurences, player_hand)
                case 2: # if there's a max of 2 occurences, the hand could contain a solo pair OR a two pair
                    two_pair = ranker.getTwoPair(player_hand)
                    if two_pair is True:
                        rank = 7 # two pair
                        player_hand = two_pair 
                    else:
                        rank = 8 # 2 of a kind
                        player_hand = ranker.getPair(player_hand)
                case _: 
                    rank = 9 # high card
                    player_hand = ranker.getHighCard(player_hand)
            possible_scores.append(rank) 
            possible_hands[rank].append(player_hand) # the twopair hand is appended if there is one
        
        player.possible_hands = possible_hands
        return min(possible_scores)


    def _getWinners(self, players:list[Player]) -> list[Player]:
        """
        Returns the winner or list of winners from the input players, in list format.
        """
        ranker = PokerRanker
        best_rank = 15 #start lower than the worst score (higher scores are worse, 0 is the best possible)
        interim_winners = []
        winners = []
        # get the best score
        for player in players:
            if player.hand_rank < best_rank:
                best_rank = player.hand_rank
        # check if any two players share the best score
        for player in players:
            if player.hand_rank == best_rank:
                interim_winners.append(player)
            else:
                players.remove(player)

        # leaves only players who are tied with the best rank
        if len(interim_winners) == 1:
            winners = [interim_winners[0]]
        
        elif len(interim_winners) > 1:
        # depending on what hand the players share, 
            match best_rank:
                case 0: # royal flush
                    winners = interim_winners
                case 1: # straight flush
                    winners = ranker.breakStraightFlushTie(interim_winners)
                case 2: # 4 of a kind
                    winners = ranker.breakFOAKTie(interim_winners)
                case 3: # full house
                    winners = ranker.breakFullHouseTie(interim_winners)
                case 4: # flush
                    winners = ranker.breakFlushTie(interim_winners)
                case 5: # straight
                    winners = ranker.breakStraightTie(interim_winners)
                case 6: # 3 of a kind
                    winners = ranker.breakTripleTie(interim_winners)
                case 7: # two pair
                    winners = ranker.breakTwoPairTie(interim_winners)
                case 8: # pair
                    winners = ranker.breakPairTie(interim_winners)
                case 9: # high card
                    pass
        
        return winners

    async def getWinners(self, ctx) -> list[Player]:
        """
        Wraps the method for evaluating a Poker winner into a pretty, concise form."""
        final_winners = []
        possible_hands = {
            "royal flush": 0,
            "straight flush": 1,
            "four of a kind": 2,
            "full house": 3,
            "flush": 4,
            "straight": 5,
            "three of a kind": 6,
            "two pair": 7,
            "pair": 8, 
            "high card": 9,
        }
        if len(self.players) > 1:
            for player in self.players:
                player.hand_rank = self.getHandRankAndPossibleHands(player)
            interim_winners = self._getWinners(self.players)
            for winner in interim_winners:
                final_winners.append(winner)

        elif len(self.players) == 1:
            final_winners.append(self.players[0])

        return final_winners

    async def rewardWinners(self, ctx, winners) -> None:
        """
        Splits the pot between winners of a Poker hand and sends each winner a congratulatory message."""
        economy = Economy(self.bot)

        # if more than one winner, split the pot rounding to the nearest whole number, give each winner their split
        if len(winners) > 1:
            cut = self.pot // len(winners)
        elif len(winners) == 1:
            cut = self.pot
        else:
            cut = 0
            await ctx.send(f"The amount of winners was less than 1. Please fix this, bro")

        for winner in winners:
            await economy.giveMoneyPlayer(winner, cut)
            await ctx.send(embed=Embed(title=f"Congratulations, {winner.name}! You won {cut} GleepCoins!"))

    async def flop(self, ctx) -> None:
        """
        Dealer of the game deals the flop, then bot sends a message containing the new community cards to the Poker channel."""
        self.dealer.dealFlop(self)
        cards_string = self.getCommunityCardsString()
        await ctx.send(embed=Embed(title=f"Community Cards", description = cards_string))

    async def dealCommunityCard(self, ctx) -> None:
        """
        Method to deal one community card and send the community cards to the public Poker channel."""
        if self.early_finish is not True:
            self.dealer.dealPokerCommunityCard(self)
            cards_string = self.getCommunityCardsString()
            await ctx.send(embed=Embed(title=f"Community Cards", description = cards_string))
        else:
            return
    
    async def play(self, ctx) -> None:
        """
        Wraps up all the steps for playing a Poker game, and executes them in order."""
        # setup
        await self.resetPlayers()
        self.post_flop = False
        self.getThreads()
        self.channel = await self.getPokerChannel(ctx)

        # turning each async function into a task
        first_blind = self.assignButtonAndPostBlinds(ctx)
        show_cards = self.showHands()
        preflop_bets = self.takePreFlopBets(ctx)
        flop = self.flop(ctx)
        turn_bets = self.takePostFlopBets(ctx, "turn")
        turn = self.dealCommunityCard(ctx)
        river_bets = self.takePostFlopBets(ctx, "river")
        river = self.dealCommunityCard(ctx)
        hand_reveal = self.showAllHands(ctx)
        determine_winner = self.getWinners(ctx)
        

        # scheduling each task in the right order, handling states when necessary
        await asyncio.wait_for(first_blind, timeout=45.0)
        self.dealer.dealHands()
        await asyncio.wait_for(show_cards, timeout=None)
        await asyncio.wait_for(preflop_bets, timeout=None)
        await asyncio.wait_for(flop, timeout=None)
        self.post_flop = True
        self.setPlayersNotDone()
        await asyncio.wait_for(turn_bets, timeout=None)
        await asyncio.wait_for(turn, timeout=None)
        self.setPlayersNotDone()
        await asyncio.wait_for(river_bets, timeout=None)
        await asyncio.wait_for(river, timeout=None)
        await asyncio.wait_for(hand_reveal, timeout=None)
        # next, program logic for calculating winner
        await asyncio.wait_for(determine_winner, timeout=None)


class PokerRanker(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @staticmethod
    def getHandTotalValue(player_hand:list[Card]) -> int:
        """
        Takes any length series of cards in a list, and returns the sum of their values.
        """
        total = 0
        for card in player_hand:
            total += card.pip_value
        return total

    # @staticmethod
    # def getBetterFlush(player_one, player_two) -> list[Player]:
    #     """
    #     Given two players with flushes, this method returns whichever player has the better flush.\n
    #     In cases where both flushes are the same, the players tie and both players are returned."""
    #     hand1 = player_one.ranking_hand
    #     hand2 = player_two.ranking_hand
    #     # iterate through each card in the two hands at the same time, whichever flush has highest value at highest card wins
    #     for i in range(len(hand1)):
    #         if hand1[i] > hand2[i]:
    #             return [player_one]
    #         elif hand1[i] < hand2[i]:
    #             return [player_two]
    #     # if both hands have the same value at each index, 
    #     return [player_one, player_two]
    
    @staticmethod
    def getFlushes(sorted_cards:list[Card]) -> list[list[Card]] | None:
        """
        Takes a sorted list consisting of both a player's hand and the community cards.\n
        Returns all possible flushes in a given hand.
        """
        suits = {
            # str, list[(value, suit), (value, suit)]
            "♠": [],
            "♣": [],
            "♥": [],
            "♦": [],
        }
        possible_flushes = []
        for card in sorted_cards:
            card_suit = card.getSuitSymbol()
            suits[card_suit].append(card)
        # now we have populated the suits dict with cards - we need to check if any of the suit lists contain 5 or items
        for suit in suits:
            while len(suits[suit]) > 5:
                possible_flushes.append(suits[suit][-5:])
                suits[suit].pop()
            if len(suits[suit]) == 5:
                possible_flushes.append(suits[suit])
        if len(possible_flushes) > 0:
            return possible_flushes
        return None
    
    @staticmethod
    def breakFlushTie(players:list[Player], length_of_remaining_cards = 5) -> list[Player]:
        # in a flush tie, the winner is determined by who has the highest card in the flush
        ranker = PokerRanker
        rank = Poker.HANDS_TO_RANKS["flush"]
        players_to_high_card = {
            # player: 8,
            # player2: 9,
        }
        # populate dict
        for player in players:
            flush = player.possible_hands[rank]
            best_card = ranker.getHighCard(flush)
            players_to_high_card[player] = best_card
            for card in flush:
                if card.pip_value == best_card:
                    player.possible_hands[rank].remove(card)
                    break
        length_of_remaining_cards -= 1

        #compare high cards
        remaining_players = []
        best_high_card = 0
        for player in players_to_high_card:
            high_card = players_to_high_card[player]
            if high_card > best_high_card:
                best_high_card = high_card
                remaining_players.clear()
                remaining_players.append(player)
            elif high_card == best_high_card:
                remaining_players.append(player)
        
        if (len(remaining_players) == 1) or (length_of_remaining_cards == 1):
            return remaining_players
        else:
            return(ranker.breakFlushTie(remaining_players, length_of_remaining_cards))

    @staticmethod
    def getBestFlush(possible_flushes:list[list[Card]]) -> list[Card]:
        best_flush = possible_flushes[0]
        if len(possible_flushes) > 1:
            for flush in possible_flushes:
                # last card in flush has a higher num value than best flush last card, make best_flush the new flush
                if PokerRanker.getHandTotalValue(flush) > PokerRanker.getHandTotalValue(best_flush):
                    best_flush = flush
        return best_flush

    @staticmethod
    def getStraights(sorted_cards:list[Card]) -> list[list[Card]]| None: # returns list of hands which are in format [list[tuple]]
        """
        Returns a list of all possible straights in the given hand.\n
        If no straights exist in the hand, returns None.
        """
        consecutive_cards:list[Card] = [] # list of Cards
        first_card = sorted_cards[0]
        consecutive_cards.append(first_card)
        possible_straights:list[list[Card]] = []

        # find any straights
        for card in sorted_cards[1:]:
            val = card.pip_value
            most_recent_card_val = consecutive_cards[-1].pip_value # last card val in consecutive cards
            if val == most_recent_card_val + 1:
                consecutive_cards.append(card)
            elif val != most_recent_card_val + 1:
                # the current val is not one higher than most_recent_card_val in consec cards, start consec cards over with the current card
                consecutive_cards = [card]

            # check if we have a straight or not. 
            if len(consecutive_cards) == 5:
                possible_straights.append(consecutive_cards)
            elif len(consecutive_cards) > 5:
                possible_straights.append(consecutive_cards[-5:])

        if len(possible_straights) > 0:
            return possible_straights
        return None
    
    @staticmethod
    def breakStraightTie(players:list[Player], length_of_remaining_cards:int = 5) -> list[Player]:
        ranker = PokerRanker
        rank = Poker.HANDS_TO_RANKS["straight"]
        players_to_highest_val = {
            # player: 8,
            # player2: 9,
        }

        # populate dict
        for player in players:
            straight = player.possible_hands[rank]
            player_high_card = ranker.getHighCard(straight)
            players_to_highest_val[player] = player_high_card
            for card in straight:
                if card.pip_value == player_high_card:
                    player.possible_hands[rank].remove(card)
                    break
        length_of_remaining_cards -= 1

        #compare high cards
        remaining_players = []
        best_high_card = 0
        for player in players_to_highest_val:
            high_card = players_to_highest_val[player]
            if high_card > best_high_card:
                best_high_card = high_card
                remaining_players.clear()
                remaining_players.append(player)
            elif high_card == best_high_card:
                remaining_players.append(player)
        
        if (len(remaining_players) == 1) or (length_of_remaining_cards == 0):
            return remaining_players
        else:
            return(ranker.breakStraightTie(remaining_players, length_of_remaining_cards))

    @staticmethod
    def getBestStraight(possible_straights:list) -> list:
        # (last possible straight will have highest value since the input cards are sorted)
        return possible_straights[-1]

    @staticmethod
    def getStraightFlushes(possible_straights:list[list[Card]], possible_flushes:list[list[Card]]) -> list[list[Card]] | None:
        # check if any of the straights also exist in flushes
        possible_straight_flushes = []
        straights = set(possible_straights)
        flushes = set(possible_flushes)
        for straight in straights:
            if straight in flushes:
                possible_straight_flushes.append(straight)
        if len(possible_straight_flushes) > 0:
            return possible_straight_flushes
        return None

    @staticmethod
    def breakStraightFlushTie(players:list[Player]) -> list[Player]:
        """
        Compares an input list of player's straight flushes, returns the player(s) with the best one."""
        ranker = PokerRanker
        rank = Poker.HANDS_TO_RANKS["straight flush"]
        hands_to_players = {}
        hands_for_comparison = []
        # the tie could potentially remain if the players have the same hand, so this method will return a list
        best_players = []
        # populate dict and hands for comparison 
        for player in players:
            best_hand = player.possible_hands[rank]
            hands_to_players[best_hand] = player
            hands_for_comparison.append(best_hand)
        best_straight_flush = PokerRanker.getBestStraightFlush(hands_for_comparison)
        # see how many people have the best hand
        for straight_flush in hands_for_comparison:
            if ranker.getHighCard(straight_flush) == ranker.getHighCard(best_straight_flush):
                best_players.append(hands_to_players[straight_flush])

        return best_players

    @staticmethod
    def getBestStraightFlush(possible_straight_flushes:list[list[Card]]) -> list[Card]:
        ranker = PokerRanker
        """
        Possible straight flushes should be a list of 5 card combos (straight flushes)"""
        best_one = possible_straight_flushes[0]
        if len(possible_straight_flushes) > 1:
            for flush in possible_straight_flushes:
                if ranker.getHighCard(flush) > ranker.getHighCard(best_one):
                    best_one = flush
        return best_one

    @staticmethod
    def getRoyalFlush(straight_flushes:list) -> list | None:
        """
        If hand contains a Royal Flush, returns the royal flush. Otherwise, returns None."""
        royal_flush_key = [10, 11, 12, 13, 14]
        # convert each straight flush to a list of its pip values
        flush_num_values = []
        for flush in straight_flushes:
            pip_flush = []
            for card in flush:
                pip_flush += [int(card[0])]
            flush_num_values.append(pip_flush)

        # check if any of the straight flushes are royal flushes (they are already sorted)
        for pip_flush in flush_num_values:
            if pip_flush == royal_flush_key:
                return pip_flush
        return None

    #FOAK = four of a kind
    @staticmethod
    def breakFOAKTie(players:list[Player]) -> list[Player]:
        """
        Compares the input players hands to find who has the best kicker in their hand. Returns player or players with the highest value kicker, in a list."""
        rank = Poker.HANDS_TO_RANKS["four of a kind"]
        players_to_kickers = {}
        best_players = []
        ####################################
        # need to compare the player's four of a kind values before resorting to comparing kickers

        # can use the below algorithm in breaking a three of a kind tie as well - below algorithm compares each players kickers
        ###################################
        # populate players to kickers dict
        for player in players:
            complete_hand = player.complete_hand
            foak = player.possible_hands[rank]
            # remove the four of a kind from the complete hand, then get high card to find each players highest kicker
            foak_value = foak[0] # get the value of cards from the four of a kind
            for card in complete_hand:
                if card.pip_value == foak_value:
                    complete_hand.remove(card)
            # all foak values are removed, now store current player's best kicker in dict
            kicker = 0
            for card in complete_hand:
                if card.pip_value > kicker:
                    kicker = card.pip_value
            players_to_kickers[player] = kicker

        # find best kicker val of all players
        best_kicker_val = 0
        for player in players_to_kickers:
            player_kicker = players_to_kickers[player]
            if player_kicker > best_kicker_val:
                best_kicker_val = player_kicker
        # check how many players have a kicker of the best value
        for player in players_to_kickers:
            player_kicker = players_to_kickers[player]
            if player_kicker == best_kicker_val:
                best_players.append(player)
        # return any players who have the best kicker 
        return best_players
    
    @staticmethod
    def breakFullHouseTie(players:list[Player]) -> list[Player]:
        rank = Poker.HANDS_TO_RANKS["full house"]
        players_to_houses:dict[Player, list[int]] = {
            # player : [value of triple, value of double]
            # player : [3, 9],
            # player2 : [7, 10],
        }

        # populate players_to_houses dict
        for player in players:
            full_house = player.possible_hands[rank]
            # since triple is assigned to full_house before the double, 
            # we can get the vallue of the triple cards by taking one of the first three cards value,
            # and the pair's value from one of the last two cards.
            # probably not safe, but I think it will work 
            triple_value = full_house[0].pip_value 
            dub_value = full_house[-1].pip_value
            players_to_houses[player] = [triple_value, dub_value]
        
        # compare player's triples
        players_with_best_triple = []
        best_triple_value = 0
        # get the best triple value, and store all players with that value
        for player in players_to_houses:
            player_trip_value = players_to_houses[player][0]
            if player_trip_value > best_triple_value:
                best_triple_value = player_trip_value
                players_with_best_triple.clear()
                players_with_best_triple.append(player)
            elif player_trip_value == best_triple_value:
                players_with_best_triple.append(player)
        
        # check if we need to continue, (to compare doubles) 
        if len(players_with_best_triple) < 1:
            raise Exception("Somehow, in this tie - no player was evaluated to have the best triple from a comparison of full houses.")
        elif len(players_with_best_triple) == 1:
            return players_with_best_triple
        else: # we need to compare doubles
            # find best double, store all players with best double
            players_with_best_double = []
            best_dub_value = 0
            for player in players_to_houses:
                player_dub_value = players_to_houses[player][1]
                if player_dub_value > best_dub_value:
                    best_dub_value = player_dub_value
                    players_with_best_double.clear()
                    players_with_best_double.append(player)
                elif player_dub_value == best_dub_value:
                    players_with_best_double.append(player)

            # check if there's still a tie or we should return just one player
            if len(players_with_best_double) < 1:
                raise Exception("No players were put into the 'players with best double' list. Revise the code bro")
            else:
                # return whoever is still alive - if there is one that's fine, and if there are more than one that's fine too
                return players_with_best_double



        # compare triples first, see if anyone has a higher triple
            # if so, return the highest player

            # else, its still a tie - 
                # then compare doubles
                    # if anyone has a double higher than anyone else, return that player
                    
                    # else, the tied players have the same triple and double, return all remaining players

    @staticmethod
    def getNofAKind(num_occurences:int, sorted_hand: list) -> list:
        """
        Returns a list of of same-valued cards, if those cards exist in the given `sorted_hand`."""
        pip_hand = [card.pip_value for card in sorted_hand] # remove the unecessary card suit for now
        values_to_occurences = Counter(pip_hand)

        for value in values_to_occurences:
            if values_to_occurences[value] == num_occurences:
                # return the value which occurs the same amount as num_occurences
                return [value for i in range(num_occurences)]
        raise ValueError(f"No value in the input hand, {sorted_hand}, contained {num_occurences} occurences.")        

    @staticmethod
    def getBestKicker(players_to_leftovers:dict[Player, list[int]], remaining_cards:int) -> list[Player]:
        """
        Players to leftovers is a dict containing Player objects as keys, and a list of int values which DONT contribute to the player's ranked hand, as the dict's values.\n
        Checks which input player has the best kicker - recursively if all their first kickers are the same.\n
        Returns player/players with best kicker\n
        
        :param int remaining_cards: `remaining_cards` is the difference between 5 and how big a player's ranked hand is.
        Since a Texas Hold 'em hand can only be 5 cards max, this means kickers only exist within these 5 cards."""
        ranker = PokerRanker
        players_to_kickers = {
            # player: 5, 
        }
        # get each players best kicker
        for player in players_to_leftovers:
            leftovers = players_to_leftovers[player]
            best_kicker = ranker.getHighCard(leftovers)
            players_to_leftovers[player].remove(best_kicker)
        remaining_cards -= 1

        # find the best kicker, and store players who have the best kicker
        remaining_players = []
        winning_kicker = 0
        for player in players_to_kickers:
            if players_to_kickers[player] > winning_kicker:
                winning_kicker = players_to_kickers[player]
                remaining_players.clear()
                remaining_players.append(player)
            elif players_to_kickers[player] == winning_kicker:
                remaining_players.append(player)
        
        # only recurse if there are cards left to compare, and there is more than one player left
        if (len(remaining_players) > 1) and (remaining_cards > 0):
            # remove players who aren't in remaining players from players_to_leftovers, and then call getBestKicker with tihs modified dict
            for player in players_to_leftovers:
                if not player in remaining_players:
                    del players_to_leftovers[player]
            return ranker.getBestKicker(players_to_leftovers, remaining_cards)
        
        elif (len(remaining_players) == 1) or (remaining_cards == 0):
            return remaining_players
        
        else:
            raise Exception("You really fucked up")

    @staticmethod
    def breakTripleTie(players:list[Player]) -> list[Player]:

        ranker = PokerRanker
        rank = Poker.HANDS_TO_RANKS["three of a kind"]
        players_to_hand_values = {
            # player: 9,
        }
        
        def getBestTrip(players_dict:dict[Player, int]):
            best_trip = 0
            for player in players_dict:
                trip = players_dict[player]
                if trip > best_trip:
                    best_trip = trip
            return best_trip
        
        def getLeftovers(player:Player, triple_val:int) -> list[Card]:
            """
            Returns a modified player hand where all the cards with the value of the player's 'three of a kind' have been removed."""
            leftovers = [card for card in player.complete_hand if card.pip_value != triple_val]
            return leftovers

        # populate dict
        for player in players:
            hand_value = player.possible_hands[rank][0] # get value of one of the three cards
            players_to_hand_values[player] = hand_value

        best_triple_value = getBestTrip(players_to_hand_values)

        # remove players who dont have the best 3 of a kind
        for player in players_to_hand_values:
            player_trip_value = players_to_hand_values[player]
            if player_trip_value < best_triple_value:
                del players_to_hand_values[player]

        if len(players_to_hand_values) < 1:
            raise Exception("The developer (Parker) has made a grave mistake while coding this tie case. Please revise")
        elif len(players_to_hand_values) == 1:
            return list(players_to_hand_values.keys())
        
        else: # if len players with best value is greater than 1
            players_to_leftovers = {
            # player: [4, 5, 7, 9],
            }
            # populate players to kickers
            for player in players:
                leftovers = getLeftovers(player, players_to_hand_values[player])
                players_to_leftovers[player] = leftovers
            winners = ranker.getBestKicker(players_to_leftovers, 2)
            return winners
        
    @staticmethod
    def getMaxOccurences(sorted_hand: list) -> int:
        """
        This method checks all cards in a hand and returns the maximum amount of times any card number value appears in the hand.\n
        :param list sorted_hand: A list of 7 sorted cards - acceptable in either in normal or pip format.\n
        :returns int: Highest num of occurences of any card value in the input sorted_hand 
        """
        pip_hand = [card.pip_value for card in sorted_hand] # remove the unecessary card suit for now
        values_to_occurences = Counter(pip_hand)
        max_occurences = 0
        for card_value in values_to_occurences:
            occurences = values_to_occurences[card_value]
            if occurences > max_occurences:
                max_occurences = occurences
        return max_occurences
    
    @staticmethod
    def getFullHouse(sorted_hand:list[Card]) -> list[Card] | None:
        """
        Checks whether a player's hand contains a full house.\n
        Returns a list of card values representing the full house if so, otherwise returns None.\n
        :param list sorted_hand: A list of 7 sorted cards - acceptable in either in normal or pip format.\n
        :returns list full_house: A list of values in this format - [(3, 3, 3), (5, 5)]"""
        
        pip_hand = [card.pip_value for card in sorted_hand]
        occurences_dict = Counter(pip_hand)
        full_house = [] 
        for card_value in occurences_dict:
            if (occurences_dict[card_value] == 3):
                triple_value = occurences_dict[card_value]
                three_piece = [card for card in sorted_hand if card.pip_value == triple_value]
                full_house = full_house = three_piece
                del occurences_dict[card_value]

        for card_value in occurences_dict:
            if (occurences_dict[card_value] == 2):
                pair_value = occurences_dict[card_value]
                pair = [card for card in sorted_hand if card.pip_value == pair_value]
                full_house = full_house + pair
            if len(full_house) == 5:
                return full_house
            
        return None
    
    @staticmethod
    def getTwoPair(sorted_hand:list) -> list[list[Card]] | None:
        """
        Checks whether a player's hand contains two pairs.\n
        Returns the two-pair hand as a list if so, in format [[value1, value1], [value2, value2]], otherwise returns None.\n
        :param list sorted_hand: A list of 7 sorted cards - acceptable in either in normal or pip format.\n"""
        pip_hand = [card.pip_value for card in sorted_hand]
        occurences_dict = Counter(pip_hand)
        pairs = []
        # find all pairs
        for card_value in occurences_dict:
            if occurences_dict[card_value] == 2:
                pair_to_add = [card for card in sorted_hand if card.pip_value == card_value]
                pairs.append(pair_to_add)
                del occurences_dict[card_value]
        if len(pairs) >= 2:
            return pairs
        return None
    
    @staticmethod
    def breakPairTie(players:list[Player]) -> list[Player]:
        ranker = PokerRanker
        rank = Poker.HANDS_TO_RANKS["pair"]
        players_to_hand_value = {
            # player: 5,
            # player2: 7,
        }

        def getBestPair(players_dict:dict[Player, int]) -> int:
            best_pair = 0
            for player in players_dict:
                pair = players_dict[player]
                if pair > best_pair:
                    best_pair = pair
            return best_pair
        
        def getLeftovers(player:Player, pair_val:int) -> list:
            leftovers = player.complete_hand
            
        # populate dict
        for player in players:
            hand_value = player.possible_hands[rank][0] # int
            players_to_hand_value[player] = hand_value

        # get best pair
        best_pair = getBestPair(players_to_hand_value)
        # remove players who don't have best pair
        for player in players_to_hand_value:
            player_pair = players_to_hand_value[player]
            if player_pair < best_pair:
                del players_to_hand_value[player]

        if len(players_to_hand_value) < 1:
            raise Exception("The developer (Parker) has made a grave mistake while coding this tie case. Please revise")
        elif len(players_to_hand_value) == 1:
            return list(players_to_hand_value.keys())
        
        else: # if len players with best value is greater than 1, get best kicker
            players_to_leftovers = {
            # player: [4, 5, 7, 9],
            }
            # populate players to kickers
            for player in players:
                leftovers = [card.pip_value for card in player.complete_hand if value != players_to_hand_value[player]]
                players_to_leftovers[player] = leftovers
            winners = ranker.getBestKicker(players_to_leftovers, 4)
            return winners
    
    @staticmethod
    def breakTwoPairTie(players:list[Player]) -> list[Player]:
        """
        Compares the input players' two pair values to get the best ranked player.\n
        If two pairs are equal, winner is determined by highest kicker."""
        ranker = PokerRanker
        rank = Poker.HANDS_TO_RANKS["two pair"]
        players_to_two_pair_values = {
            # player: [value1, value2],
        }

        def findBestPair(players_to_pairs:dict) -> int:
            best_pair_value = 0
            for player in players_to_pairs:
                for pair_val in players_to_pairs[player]:
                    if pair_val > best_pair_value:
                        best_pair_value = pair_val
            return best_pair_value
        
        ### needs to be revised
        def getLeftovers(player:Player, two_pair_vals:list) -> list:
            leftovers = player.complete_hand # player complete hand is a list of tuples: [(value, suit), (value, suit)]
            for i in range(2):
                leftovers.remove(two_pair_vals[0])
                leftovers.remove(two_pair_vals[1])
            return leftovers
        
        # populate dict with two-pair's values
        for player in players:
            value1 = player.possible_hands[rank][0][0]
            value2 = player.possible_hands[rank][1][0] 
            players_to_two_pair_values[player] = [value1, value2]

        # need to store the player with the highest pair1 value
            # if any players share the highest pair value, compare their next highest pairs
                # if still tied, compare kickers and return player with best kicker

        # get the best pair
        best_pair = findBestPair(players_to_two_pair_values)

        # store all players who have a pair the value of best pair, and remove this value from players who have it
        for player in players_to_two_pair_values:
            player_pairs = players_to_two_pair_values[player]
            if best_pair in player_pairs:
                players_to_two_pair_values[player].remove(best_pair) # remove instances of best value from players who have it
            elif best_pair not in player_pairs:
                del players_to_two_pair_values[player] # completely remove players who don't have the best value

        if len(players_to_two_pair_values) < 1:
            raise Exception("bruh moment")
        elif len(players_to_two_pair_values) == 1:
            return list(players_to_two_pair_values.keys())
        else:
            # get the next best pair (all instances of the last best pair were removed)
            best_pair = findBestPair(players_to_two_pair_values)

            # repeat steps used in previous half of method 
            for player in players_to_two_pair_values:
                player_pairs = players_to_two_pair_values[player]
                if best_pair in player_pairs:
                    players_to_two_pair_values[player].remove(best_pair)
                elif best_pair not in player_pairs:
                    del players_to_two_pair_values[player]

            if len(players_to_two_pair_values) < 1:
                raise Exception("The developer (Parker) has made a grave mistake while coding this tie case. Please revise")
            elif len(players_to_two_pair_values) == 1:
                return list(players_to_two_pair_values.keys())
            else: 
                # if there are still tied players, winner is determined by whoever has the best kicker
                players_to_leftovers = {
                # player: [4, 5, 7, 9],
                }
                # populate players to kickers
                for player in players:
                    leftovers = getLeftovers(player, players_to_two_pair_values[player])
                    players_to_leftovers[player] = leftovers
                # pass in 1 as 'remaining cards' since a hold em hand consists of 5 cards, so the only kicker would be the player's next highest card
                winners = ranker.getBestKicker(players_to_leftovers, 1)
                return winners
        
    @staticmethod
    def getHighCard(sorted_hand:list[Card]) -> int:
        """
        Returns the highest pip value of all cards in a player's hand with (value, suit) format.
        :param list sorted_hand: A list of cards sorted in ascending order - acceptable in either in normal or pip format.\n"""
        highest_card_val = 0
        for card in sorted_hand:
            card_val = card.pip_value 
            if card_val > highest_card_val:
                highest_card_val = card_val
        return highest_card_val


async def setup(bot):
    await bot.add_cog(PlayerQueue(bot))        

