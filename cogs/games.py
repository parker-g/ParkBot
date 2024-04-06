import csv
import random
import asyncio
from collections import Counter

from discord.ext import commands
from discord.ext.commands.cog import Cog
from discord import Member, Embed, TextChannel

from db import get_connection
from cogs.economy import Economy
from cogs.controller import Controller
from config.configuration import THREADS_PATH, DB_OPTION


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
        # store suit as string word, not symbol
        if suit in Card.SUIT_STRING_TO_SYMBOL:
            self.suit = suit
        elif suit in Card.SUIT_SYMBOL_TO_STRING:
            self.suit = Card.SUIT_SYMBOL_TO_STRING[suit]
        else:
            raise ValueError("Inappropriate value for `suit` argument. Refer to Card class for valid argument options.")
        
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
    
    def setValue(self, new_value:int) -> None:
        self.pip_value = new_value

    def getValuePip(self) -> int:
        return self.pip_value

    def getBlackJackValuePip(self) -> int:
        if self.pip_value > 10:
            return 10
        else:
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

    @staticmethod
    def bubbleSortCards(cards_list:list) -> None:
        """Function sorts a list of Card objects, in place."""
        n = len(cards_list)
        # optimize code, so if the array is already sorted, it doesn't need
        # to go through the entire process
        swapped = False
        # Traverse through all array elements
        for i in range(n-1):
            # range(n) also work but outer loop will
            # repeat one time more than needed.
            # Last i elements are already in place
            for j in range(0, n-i-1):
    
                # traverse the array from 0 to n-i-1
                # Swap if the element found is greater
                # than the next element
                if cards_list[j].pip_value > cards_list[j + 1].pip_value:
                    swapped = True
                    cards_list[j], cards_list[j + 1] = cards_list[j + 1], cards_list[j]
            
            if not swapped:
                # if we haven't needed to make a single swap, we
                # can just exit the main loop.
                return

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
                # iterate from 2 to 14, since ace's are worth 14 (not 1) in poker 
                for i in range(2, 15):
                    self.deck.append(Card(game, i, "spade"))
                    self.deck.append(Card(game, i, "club"))
                    self.deck.append(Card(game, i, "heart"))
                    self.deck.append(Card(game, i, "diamond"))

    def shuffle(self) -> None:
        random.shuffle(self.deck)


class Player:
    """
    The Player class represents a participant in any of the games in the games cog."""
    def __init__(self, ctx:commands.Context):
        self.name = ctx.author.name
        self.member = ctx.author
        self.hand:list[Card] = []
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
        # the combination of a player's cards and the community cards/ the board (7 cards) - stored in pip format
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

    # need to test if this works. Seems too simple right now, like it is only changing a surface level attribute that won't actually change the Poker pot (Idk if that makes sense)
    def pushToPot(self, poker_game) -> None:
        """
        Pushes a player's current bet to the input Poker game's pot, and clears the player's current bet."""
        poker_game.pot += self.bet
        self.bet = 0

    def sumCards(self) -> int:
        """
        Returns the sum of card values in the player's hand."""
        total = 0
        for card in self.hand:
            total += card.getBlackJackValuePip()
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
            pretty_string += f" {card.face_value} {suit_symbol}, "
        last_card = self.hand[-1]
        last_symbol = Card.SUIT_STRING_TO_SYMBOL[last_card.suit]
        pretty_string += f"{last_card.face_value} {last_symbol}"
        return pretty_string

    # used in Poker
    def addCardsToHand(self, community_cards:list) -> list[Card]: # tuple(value, int)
        """
        Combines a player's hand with the community cards on the table, returns them in a new list.\n
        I use the term 'complete hand' to refer to a hand which including BOTH the player's cards, and the community cards.\n
        """
        return self.hand + community_cards

    def removeCard(self, card_value:int) -> None:
        """
        Removes a card from the player's `complete_hand`, by pip value.\n
        If more than one card exists in the hand with the input card value, only the first instance will be removed."""
        for card in self.complete_hand:
            if card.pip_value == card_value:
                self.complete_hand.remove(card)
                break
        
    def removeCards(self, card_values:list[int]) -> None:
        """
        Removes cards from the player's `complete_hand`, pip values."""
        for value in card_values:
            self.removeCard(value)


class PlayerQueue(Cog):
    """
    The PlayerQueue class is used as a guild-level-distributor of the games available in the games.py 'cog'.\n
    self.q is a list[Card]. Each player is stored as a tuple of (Player, Discord.Member) objects so that we can easily access methods to discord members.
    Right now, I'm actually realizing that it would be much more simple if I instead just incorporated the discord.Member object into the Player class as an attribute. Removing the possibility of confusing others with tuples in the player queue."""
    def __init__(self, bot, guild):
        self.bot:commands.Bot = bot
        self.q:list[Player] = []
        self.guild = guild
        self.economy = Economy(self.bot, get_connection("Games cog - PlayerQueue"))
        self.poker = Poker(self.bot, self)
        self.blackjack = BlackJackGame(self.bot, self)

    async def _joinQueue(self, ctx):
        """
        This is a command giving Discord server members the ability to join the PlayerQueue, by executing the command in a text channel."""
        new_player = Player(ctx)
        # check if person using command is already in the player pool
        for player in self.q:
            if ctx.author.name == player.name:
                # if so, tell user that they're already in the queue
                message_str = f"{ctx.author.name} is already in queue."
                message = await ctx.send(embed = Embed(title=message_str))
                await message.delete(delay=5.0)
                return

        self.q.append(new_player)
        message_str = f"{ctx.author.name} has been added to players queue."
        message = await ctx.send(embed = Embed(title=message_str))
        await message.delete(delay=5.0)
        
    async def _leaveQueue(self, ctx):
        """
        This command gives users the ability to leave the PlayerQueue. If a player leaves the queue, any bet they had previously set will be returned to their bank."""
        # get player who used the command
        for player in self.q:
            if ctx.author.name == player.name:
                # return the person's bet money to them, and remove them from player pool
                await self.economy.give_money_player(ctx.author, player.bet)
                self.q.remove(player)
                message_str = f"{ctx.author.name} has been removed from the queue."
                message = await ctx.send(embed = Embed(title=message_str))
                await message.delete(delay=5.0)
                return
        # if command caller isn't in player pool, tell them
        message_str = f"{ctx.author.name} is not in the queue."
        message = await ctx.send(embed = Embed(title=message_str))
        await message.delete(delay=5.0)

    async def _clearQueue(self, ctx):
        """
        Discord server members can clear the PlayerQueue with this command."""
        for player in self.q:
            if player.bet > 0:
                await self.economy.give_money_player(player.member, player.bet)
                player.bet = 0
            self.q.remove(player)
            
        message = await ctx.send(embed= Embed(title = f"All players have been removed from queue."))
        await message.delete(delay=5.0)

    async def _showQueue(self, ctx):
        """
        This command provides users the ability to see who is currently in the PlayerQueue."""
        players_string = ""
        for player in self.q:
            players_string += f"{player.name}\n"
        em = Embed(title="Players in Queue", description=f"{players_string}")
        await ctx.send(embed = em)

    async def __setBet(self, ctx, inputPlayer, bet:int) -> bool:
        """
        Withdraws GleepCoins from a user's 'bank account', into a player's `player.bet` attribute.\n
        This method accomplishes the same thing as the setBet() method, without sending messages to the Discord chat."""
        bet = int(bet)
        success = False
        for player in self.q:
            if inputPlayer.name == player.name:
                # store players bet amount in corresponding player object
                try:
                    withdraw_success = await self.economy.withdraw_money_player(ctx, inputPlayer.member, bet)
                    player.bet = bet
                    success = withdraw_success
                except Exception as e:
                    print(f"Error setting bet for player, {player.name} : {e}")
        return success
    
    
    async def _setBet(self, ctx, bet:int):
        """
        Discord users who have joined the PlayerQueue can use this command to set a bet, valid for the next game of BlackJack.\n"""
        bet = int(bet)
        for player in self.q:
            if ctx.author.name == player.name:
                # store players bet amount in corresponding player object
                withdraw_success = await self.economy.withdraw_money_player(ctx, ctx.author, bet)
                player_balance = self.economy._get_balance(player.member)
                if withdraw_success is False:
                    broke_message = await ctx.send(embed = Embed(title=f"{ctx.author.name}, you're broke. Your current balance is {player_balance} GleepCoins."))
                    await broke_message.delete(delay=10.0)
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

    async def _beg(self, ctx):
        """
        Players who have exhausted their bank account can use this command to make money."""
        amount = random.randint(1, 20)
        await self.economy.give_money_player(ctx.author, amount)
        beg_message = await ctx.send(embed=Embed(title=f"{ctx.author.name} recieved {amount} GleepCoins from begging."))
        await beg_message.delete(delay=5.0)

    async def _playJack(self, ctx):
        """
        This command is the PlayerQueue's interface with a blackjack game. It begins a game of blackjack, using all the players in the queue."""
        await ctx.send(f"Attempting to start blackjack game.")
        try:
            if not self.blackjack.in_progress:
                await self.blackjack.play(ctx)
            else:
                await ctx.send("A blackjack game is already in progress.")
        except Exception as error:
            await ctx.send(f"An exception occured, {error}")

    async def _playPoker(self, ctx):
        """
        This command puts all players in the PlayerQueue in a game of Texas Hold'em Poker."""
        await ctx.send(f"Attempting to start Poker game.")
        try:
            if not self.poker.in_progress:
                await self.poker.play(ctx)
            else:
                await ctx.send("A poker game is already in progress.")
        except Exception as e:
            await ctx.send(f"An exception occured, {e}")


class GamesController(Controller):
    """High level controller of PlayerQueues. Assigns each guild a PlayerQueue, and routes requests from guilds to their respective PlayerQueue instance."""
    def __init__(self, bot):
        super().__init__(bot, PlayerQueue)
    
    
    @commands.command("joinQ")
    async def joinQueue(self, ctx) -> None:
        queue = self.getGuildClazz(ctx)
        await queue._joinQueue(ctx)

    @commands.command("leaveQ")
    async def leaveQueue(self, ctx):
        queue = self.getGuildClazz(ctx)
        await queue._leaveQueue(ctx)
    
    @commands.command("clearQ")
    async def clearQueue(self, ctx):
        queue = self.getGuildClazz(ctx)
        await queue._clearQueue(ctx)

    @commands.command("showPlayers")
    async def showQueue(self, ctx):
        queue = self.getGuildClazz(ctx)
        await queue._showQueue(ctx)
    
    @commands.command()
    async def setBet(self, ctx, bet) -> None:
        queue = self.getGuildClazz(ctx)
        await queue._setBet(ctx, bet)

    @commands.command()
    async def beg(self, ctx) -> None:
        queue = self.getGuildClazz(ctx)
        await queue._beg(ctx)
    
    @commands.command("playJack")
    async def playBlackJack(self, ctx) -> None:
        queue = self.getGuildClazz(ctx)
        await queue._playJack(ctx)
    
    @commands.command()
    async def playPoker(self, ctx) -> None:
        queue = self.getGuildClazz(ctx)
        await queue._playPoker(ctx)
    

class Dealer(Player):
    def __init__(self, deck:Deck, players:list[Player]):
        self.name = "Dealer"
        self.deck = deck.deck
        self.players = players
        self.cards_in_play = []
        self.hand = []
        self.complete_hand:list[Card] = []
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
        card = self.deck[0]
        player.hand.append(card)
        player.complete_hand.append(card)
        self.cards_in_play.append(card)
        self.deck.remove(card)

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
        self.economy = Economy(self.bot, get_connection("Games Cog - BlackJackGame"))
        self.in_progress = False

    def loadPlayers(self) -> None:
        for player in self.player_queue:
            if not player in self.players:
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
        for player in players:
            if player.winner:
                winnings = player.bet * 2
                await self.economy.give_money_player(player.member, winnings)
                if winnings != 0:
                    message = await ctx.send(embed = Embed(title=f"{player.name} won {winnings} GleepCoins."))
                    await message.delete(delay=5.0)
            elif player.tie:
                winnings = player.bet
                await self.economy.give_money_player(player.member, winnings)
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
        self.in_progress = True
        self.loadPlayers()
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

        await dealer_hand_message.edit(embed = Embed(title = f"Dealer's total is: {dealer.sumCards()}", description=f"The dealer's hand is: {dealer.prettyHand()}"))

        winners, ties = self.getWinners(self.players)
        await self.cashOut(ctx, self.players)
        # if there are no winners, and no ties, send "Everyone lost."
        # else if there are winners, send "Here are our winners: "
        # else if there are no winners but there are ties, send "These players tied:"
        if (len(winners) == 0) and (len(ties) == 0):
            await ctx.send(embed = Embed(title="You're All Losers!"))
        elif len(winners) > 0:  
            winner_string = f"" 
            for winner in winners[:-1]:
                winner_string += f"{winner.name}, "
            winner_string += f"{winners[-1].name}"
            await ctx.send(embed = Embed(title=f"Our Winners are: {winner_string}"))
        elif len(ties) > 0:
            tie_string = f"" 
            for tie in ties[:-1]:
                tie_string += f"{tie.name}, "
            tie_string += f"{ties[-1].name}"
            await ctx.send(embed = Embed(title=f"Our TieBabies are: {tie_string}"))
            
        await ctx.send("\nHere's everyone's hands.\n")
        long_ass_string = ""
        for player in self.players:
            long_ass_string += (f"{player.name} had: {player.prettyHand()}, with a total of {player.sumCards()}\n")
        em = Embed(title="All Hands:", description = long_ass_string)
        await ctx.send(embed = em)
        self.in_progress = False
        # empty players before giving opportunity for another round to start


class Poker(commands.Cog):
    """
    The Poker class stores the sequential steps necessary for carrying out a game of texas hold'em poker. The logic used to evaluate which hand is the winner in a game of Poker, is all stored in the PokerRanker class.
    
    attributes required for construction:
    :discord.ext.commands.Bot bot: A discord Bot object, used to communicate with Discord servers.
    :Deck deck: A Deck object representing two decks to be used in a poker game.
    :PlayerQueue player_queue: A PlayerQueue object which is used to access the players who are in the game.
    :list players: The list that becomes populated with any players in the game whenever a Poker game is constructed.
    :Dealer dealer: A Dealer is used to deal cards to the community and to the rest of the players in the Poker game.
    
    attributes instantiated upon construction:
    :list[Card] community_cards: The cards available to any player in the game to help them form the best hand possible.\n
    :int small_blind: Used to store the small blind, set during a game of Poker.\n
    :int big_blind: Used to store the big blind, set during a game of Poker.\n
    :int small_blind_idx: The index of the player in self.players who sets the small blind.\n
    :int big_blind_idx: The index of the player in self.players who sets the big blind.\n
    :dict[str, discord.Thread] threads: A dictionary used to store private threads for each player in the game. These threads are used to privately send players their poker hand.\n
    :int pot: Represents the pot of chips to be won in a game of Poker.\n
    :bool earlyFinish: A boolean used to control state of poker game - becomes True if only one player remains in the game before betting rounds have finished.\n
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

    RANKS_TO_HANDS = {
        0: "royal flush",
        1: "straight flush",
        2: "four of a kind",
        3: "full house",
        4: "flush",
        5: "straight",
        6: "three of a kind",
        7: "two pair",
        8: "pair", 
        9: "high card",
    }

    def __init__(self, bot, player_queue:PlayerQueue):
        self.bot = bot
        self.deck = Deck("poker")
        self.deck.shuffle()
        self.player_queue = player_queue
        self.players:list[Player] = []
        for player in self.player_queue.q:
            self.players.append(player)
        self.dealer = Dealer(self.deck, self.players)
        self.economy = Economy(self.bot, get_connection("Games Cog - Poker game"))
        
        # poker specific attributes 
        self.community_cards:list[Card] = []
        self.small_blind = 0
        self.big_blind = 0
        self.small_blind_idx = None
        self.big_blind_idx = 0
        self.threads:dict[str, int] = {} # contains player names as keys, and discord.Thread IDs as values - used to send private messages to players
        self.pot = 0 # holds all bets
        self.early_finish = False # responsible for state of whether a game has ended early (due to all but 1 player folding)
        self.in_progress = False

    async def resetPlayers(self) -> None:
        """
        Resets all of the Poker player's attributes relating to their game state."""
        for player in self.players:
            if player.name == "Dealer":
                self.players.remove(player)
        if self.players:
            for player in self.players:
                player.winner = False
                player.done = False
                player.hand = []
                player.ranked_hand.clear()
                player.complete_hand.clear()
                player.possible_hands.clear()
                player.button = False
                player.thread = None
                player.folded = False
                if player.bet > 0:
                    await self.economy.give_money_player(player.member, player.bet)
                    player.bet = 0

    def getPot(self) -> int:
        """
        Returns the Poker game's current pot."""
        return self.pot
    
    def pushToPot(self, player:Player) -> None:
        """
        Pushes a player's current bet to the Poker game's pot."""
        self.pot += player.bet
        player.bet = 0

    def getCommunityCardsString(self) -> str:
        """
        Returns the community cards in one long string."""
        pretty_string = ""
        for card in self.community_cards:
            pretty_string += f"{(card.stringify())}\n"
        return pretty_string

    def areAllPlayersDone(self) -> bool:
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
        with open(THREADS_PATH, "r") as file:
            threads_dict = {}
            reader = csv.reader(file) 
            #skip first row of csv
            next(reader)
            for row in reader:
                threads_dict[row[0]] = int(row[1])
        self.threads = threads_dict
        return

    def writeNewThread(self, player, thread_id:int) -> None:
        """
        Writes a username and their discord thread identifier to the threads.csv file.
        """
        with open(THREADS_PATH, "a") as file:
            file.write(f"\n{player.name},{thread_id}")
        return
    
    def setPlayersNotDone(self, players:list[Player]) -> None:
        """
        Resets input Poker players' .done attribute to False."""
        for player in players:
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
        channel = await self.getPokerChannel()
        for player in self.players:
            member = [user for user in self.player_queue.q if user.name == player.name][0].member
            if not player.name in self.threads:
                # print(f"creating thread for {player.name}")
                thread = await channel.create_thread(name="Your Poker Hand", reason = "poker hand", auto_archive_duration = 60)
                self.threads[player.name] = thread.id
                self.writeNewThread(player, thread.id)
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

    async def getPokerChannel(self) -> TextChannel:
        """
        Returns text channel named "poker" in your Discord server where the bot will send poker related messages, necesary to run the game.\n"""
        async for guild in self.bot.fetch_guilds():
            if guild.name == "Orlando Come":
                self.guild = guild
                channels = await guild.fetch_channels()
                for channel in channels:
                    if channel.name == "poker":
                        return channel
        raise Exception("Your guild isn't named Orlando Come, or you don't have a text channel named poker. Please change this code Parker to be more easy to use for other people. Perhaps create a new channel named poker and then access that one after its created.")
    
    async def sendPotMessage(self, ctx) -> None:
        await ctx.send(embed=Embed(title=f"Current Pot: {self.pot} GleepCoins"))

    async def sendBrokeMessage(self, ctx, player:Player, economy:Economy) -> None:
        await ctx.send(embed=Embed(title=f"Get ya money up, not ya funny up.", description=f"Transaction failed, {player.name}. Maybe it's because you only got {economy._get_balance(player.member)}.\nTry again, with a lower amount, or you might have to fold."))

    # currently having an issue that the pot is raised much higher than it should after assigning big blind.
    async def assignButtonAndPostBlinds(self, ctx):
        """
        Assigns the button to a random player, and takes the blinds from the players directly after and 2 players after the button player."""
        num_players = len(self.players)
        print(f"number of players: {num_players}")
        if num_players < 2:
            await ctx.send(f"You don't have enough players to play Poker. You need 2 or more players.")
        i = random.randint(0, num_players-1)
        self.players[i].button = True
        button_msg = await ctx.send(embed=Embed(title=f"{self.players[i].name} holds the button this round."))
        await button_msg.delete(delay=10.0)
        if i == num_players - 1:
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
        await ctx.send(embed=Embed(title=f"Game Info: ", description= f"{self.players[i].name} holds the button this game.\n{small_blind_player.name} will set the small blind,\nand {big_blind_player.name} will set the big blind."))
        input_message = await ctx.send(embed = Embed(title=f"Post the small blind, {small_blind_player.name}.", description=f"{small_blind_player.name}, type the amount of GleepCoins to set as small blind."))
        while self.small_blind == 0:
            message = await self.bot.wait_for("message", timeout = None)
            if message.author.name == small_blind_player.name:
                try:
                    small_blind = int(message.content)
                    is_success = await self.player_queue.__setBet(ctx, small_blind_player, small_blind)
                    # if the withdrawal was successful, (player's bet amount increased from 0), continue
                    if is_success is True:
                        self.small_blind = small_blind
                        self.pushToPot(small_blind_player)
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
                        success = await self.player_queue.__setBet(ctx, big_blind_player, big_blind)
                        if success is True:
                            self.big_blind = big_blind
                            self.min_bet = self.big_blind
                            big_blind_alert = await ctx.send(embed = Embed(title=f"Big blind posted at {big_blind} GleepCoins."))
                            self.pushToPot(big_blind_player)
                            await big_blind_alert.delete(delay = 7.0)
                        else:
                            balance = self.economy._get_balance(big_blind_player.member)
                            await ctx.send(embed = Embed(title=f"Your transaction failed.", description=f"{big_blind_player.name}, your balance is {balance}"))
                            continue
                except ValueError or TypeError:
                    int_error = await ctx.send(embed = Embed(title=f"Please type a valid integer."))
                    await int_error.delete(delay = 7.0)
                    continue
        return

    # need to push players bets to pot after each raise, call, or fold.
    async def takePreFlopBets(self, ctx):
        if self.early_finish is not True:
            self.setPlayersNotDone(self.players)
            max_idx = len(self.players)
            initial_bet = self.big_blind
            min_bet = initial_bet
            
            for i in range(100): # make iteration unreasonably high to ensure we don't reach it's limit
                player_idx = i + self.big_blind_idx
                if player_idx >= max_idx:
                    player_idx = player_idx % max_idx 

                player = self.players[player_idx]
                member = [user for user in self.player_queue.q if user.name == player.name][0].member
                
                if player.bet < min_bet:
                    player.done = False
                
                message_embed = Embed(title=f"Pre-Flop Betting", description=f"{member.mention}\nWould you like to call {min_bet} 📞, raise 🆙, or fold 🏃‍♂️?")
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
                                    isSuccess = await self.player_queue.__setBet(ctx, player, min_bet)
                                    if isSuccess:
                                        call_msg = await ctx.send(embed=Embed(title=f"{player.name} called the bet, {min_bet} GleepCoins."))
                                        await call_msg.delete(delay=5.0)
                                        player.done = True
                                        self.pushToPot(player)
                                    else:
                                        await self.sendBrokeMessage(ctx, player, self.economy)
                                        continue

                                case "🆙":
                                    await ctx.send(embed=Embed(title=f"Okay, set a bet higher than {min_bet}.", description=f"Please type your bet to raise."))
                                    raise_message = await self.bot.wait_for("message")
                                    try:
                                        raise_amount = int(raise_message.content)
                                        if raise_amount <= min_bet:
                                            await ctx.send(embed=Embed(title=f"That bet was too small. Please react and try again."))
                                        else:
                                            isSuccess = await self.player_queue.__setBet(ctx, player, raise_amount)
                                            if isSuccess:
                                                await ctx.send(embed=Embed(title=f"{player.name} raised {raise_amount} GleepCoins."))
                                                self.pushToPot(player)
                                                self.setPlayersNotDone(self.players)
                                                min_bet = raise_amount
                                                player.done = True
                                            else:
                                                await self.sendBrokeMessage(ctx, player, self.economy)
                                                continue

                                    except ValueError as e:
                                        print(f"Error casting your message to integer:", e)
                                        await ctx.send(f"That was an invalid integer. Please react and then try again.")
                                        continue
                                case "🏃‍♂️":
                                    # in a fold, mans doesnt place a bet, he just is done betting, and leaves the active players.
                                    leave_message = await ctx.send(embed=Embed(title=f"{player.name} folded.", description=f"You forfeited {player.bet} GleepCoins to the pot."))
                                    await leave_message.delete(delay=5.0)
                                    self.pushToPot(player)
                                    self.players.remove(player)
                                    max_idx -= 1
                                    player.done = True
     
                    except asyncio.TimeoutError:
                        self.pushToPot(player)
                        self.players.remove(player)
                        max_idx -= 1
                        player.done = True
                        await ctx.send(embed=Embed(title=f"You took too long, dummy (baltimore accent).", description=f"You automatically folded."))  
                
                await self.sendPotMessage(ctx) # show the pot at the end of each player's turn  
                if (len(self.players) == 1):
                    self.players[0].winner = True
                    await ctx.send(embed=Embed(title=f"{self.players[0].name} is the last player standing.", description=f"{self.players[0].name} will receive the pot of {self.pot} GleepCoins."))
                    self.early_finish = True    

                if self.areAllPlayersDone():
                    break

            pf_msg = await ctx.send(embed=Embed(title=f"Pre flop betting has come to an end.", description=f"Current Pot: {self.pot} GleepCoins."))
            await pf_msg.delete(delay=10.0)
            return
        else:
            return
        
    async def takePostFlopBets(self, ctx, name_of_betting_round):
        if self.early_finish is not True:
            self.setPlayersNotDone(self.players)
            max_idx = len(self.players)
            min_bet = 0
            print(f"Max index: {max_idx}")

            for i in range(100): # make iteration unreasonably high to ensure we don't reach it's limit
                # reassign max index after every player goes, in case a player folds
                max_idx = len(self.players)
                player_idx = i + self.big_blind_idx
                if player_idx >= max_idx:
                    player_idx = player_idx % max_idx 

                player = self.players[player_idx]
                member = [user for user in self.player_queue.q if user.name == player.name][0].member
                
                if player.bet < min_bet:
                    player.done = False

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
                            # if min bet is 0 : players can raise, check, or fold, but not call
                            # if min bet is > 0: players can call, raise, or fold. can't check
                            # min bet should be renamed min_bet_for_the_current_rotation - bets should continue until a round has passed where everyone has checked.
                            # this means I will probably need to set each player to not-done every time someone raises.
                            # i Think this is what I need to do to fix Post flop betting.

                            # also - would help for clarity to break this method up into more manageable chunks if possible.
                            match emoji:
                                case "📞":
                                    if min_bet > 0:
                                        isSuccess = await self.player_queue.__setBet(ctx, player, min_bet)
                                        if isSuccess:
                                            await ctx.send(embed=Embed(title=f"{player.name} called the bet, {min_bet} GleepCoins."))
                                            self.pushToPot(player)
                                            player.done = True
                                        else:
                                            await self.sendBrokeMessage(ctx, player, self.economy)
                                    else:
                                        await ctx.send(Embed(title=f"You can't call right now.", description=f"No one in this round has bet yet. Select a different option."))
                                        continue

                                case "🆙":
                                    await ctx.send(embed=Embed(title=f"Okay, set a bet higher than {min_bet}.", description=f"Please type your bet to raise."))
                                    raise_message = await self.bot.wait_for("message")
                                    try:
                                        raise_amount = int(raise_message.content)
                                        if raise_amount <= min_bet:
                                            await ctx.send(embed=Embed(title=f"That bet was too small. Please react and try again."))
                                        else:
                                            isSuccess = await self.player_queue.__setBet(ctx, player, raise_amount) 
                                            if isSuccess:
                                                await ctx.send(embed=Embed(title=f"{player.name} raised {raise_amount}."))
                                                self.pushToPot(player)
                                                min_bet = raise_amount
                                                player.done = True
                                                # reset all other players' done status, since they now need to call, raise the raise, or fold
                                                other_players = [participant for participant in self.players if participant != player]
                                                self.setPlayersNotDone(other_players)
                                            else:
                                                await self.sendBrokeMessage(ctx, player, self.economy)
                                                continue
                                    except ValueError as e:
                                        print(f"Error casting your message to integer:", e)
                                        await ctx.send(f"That was an invalid integer. Please react and then try again.")
                                        continue
                                case "✔️":
                                    # a player can only check if the min bet is 0, otherwise they must call or fold
                                    if min_bet == 0:
                                        player.done = True
                                        check_msg = await ctx.send(embed=Embed(title=f"{player.name} checked."))
                                        await check_msg.delete(delay=7.0)
                                    else:
                                        await ctx.send(embed=Embed(title=f"You can't check right now.", description=f"You must call the raised bet, fold, or raise the raise."))
                                        continue
                                case "🏃‍♂️":
                                    # in a fold, mans doesnt place a bet, he just is done betting, and leaves the active players.
                                    self.pushToPot(player)
                                    self.players.remove(player)
                                    max_idx -= 1
                                    leave_message = await ctx.send(embed=Embed(title=f"{player.name} folded. Nice."))
                                    await leave_message.delete(delay=5.0)
                                    player.done = True

                            await self.sendPotMessage(ctx)
                    except asyncio.TimeoutError:
                        self.players.remove(player)
                        max_idx -= 1
                        player.done = True
                        await ctx.send(embed=Embed(title=f"You took too long, dummy (baltimore accent).", description=f"You automatically folded."))  
                if (len(self.players) == 1):
                    self.players[0].winner = True
                    await ctx.send(embed=Embed(title=f"{self.players[0].name} is the last player standing."))
                    self.early_finish = True    

                if self.areAllPlayersDone():
                    break

            pf_msg = await ctx.send(embed=Embed(title=f"Post flop betting has come to an end.", description = f"Current pot: {self.pot} GleepCoins."))
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
        possible_hands:dict[int, list[Card]] = {
            # 0: [], #royal flush [10, 11, 12, 13, 14]
            # 1: [],
            # 2: [],
            # 3: [],
            # 4: [],
            # 5: [],
            # 6: [],
            # 7: [],
            # 8: [],
            # 9: [], # high card
        }
        ranker = PokerRanker
        player.complete_hand = player.complete_hand + self.community_cards # add board to complete hand
        player_hand = player.complete_hand # all 7 cards

        Deck.bubbleSortCards(player_hand)
        print(f"{player.name}'s complete, sorted hand: {[card.stringify() for card in player.complete_hand]}")

        flushes = ranker.getFlushes(player_hand)
        straights = ranker.getStraights(player_hand)
        if (flushes is not None) and (straights is not None):
            straight_flushes = ranker.getStraightFlushes(straights, flushes)
            if straight_flushes is not None:
                royal_flush = ranker.getRoyalFlush(straight_flushes)
                if royal_flush is not None:
                    rank = 0 # royal flush
                    possible_scores.append(rank) 
                    possible_hands[rank] = royal_flush
                else:
                    rank = 1 # straight flush
                    possible_scores.append(rank) 
                    possible_hands[rank] = ranker.getBestStraightFlush(straight_flushes)
        elif straights is not None:
            rank = 5 # straight
            possible_scores.append(rank) 
            possible_hands[rank] = ranker.getBestStraight(straights)
        elif flushes is not None:
            rank = 4 # flush
            possible_scores.append(rank)
            possible_hands[rank] = ranker.getBestFlush(flushes)
        full_house = ranker.getFullHouse(player_hand)
        if full_house is not None:
            rank = 3 # full house
            possible_scores.append(rank) 
            possible_hands[rank] = full_house 

        max_occurences = ranker.getMaxOccurences(player_hand)
        if max_occurences <= 4:
            match max_occurences:
                case 4:
                    rank = 2 # 4 of a kind
                    player_hand = ranker.getNofAKind(max_occurences, player_hand)
                case 3:
                    rank = 6 # three of a kind.hand
                    player_hand = ranker.getNofAKind(max_occurences, player_hand)
                case 2: # if there's a max of 2 occurences, the hand could contain a solo pair OR a two pair
                    two_pair = ranker.getTwoPair(player_hand)
                    if two_pair is not None:
                        rank = 7 # two pair
                        player_hand = two_pair 
                    else:
                        rank = 8 # 2 of a kind
                        player_hand = ranker.getBestPair(player_hand)
                case _: 
                    rank = 9 # high card
                    player_hand = ranker.getHighCard(player.hand)
            possible_scores.append(rank) 
            possible_hands[rank] = player_hand
        
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
        # get the best (lowest) score
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
                    winners = ranker.breakHighCardTie(interim_winners)
        
        return winners

    async def getWinners(self) -> list[Player]:
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

        # if more than one winner, split the pot rounding to the nearest whole number, give each winner their split
        if len(winners) > 1:
            cut = self.pot // len(winners)
        elif len(winners) == 1:
            cut = self.pot
        else:
            cut = 0
            await ctx.send(f"The amount of winners was less than 1. Please fix this, bro")

        for winner in winners:
            await self.economy.give_money_player(winner.member, cut)
            await ctx.send(embed=Embed(title=f"Congratulations, {winner.name}! You won {cut} GleepCoins!", description=f"You had a {Poker.RANKS_TO_HANDS[winner.hand_rank]}."))

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
        self.in_progress = True
        await self.resetPlayers()
        self.getThreads()
        if len(self.players) < 2:
            await ctx.send(embed = Embed(title=f"You need at least 2 players to run a game of Poker. Please populate the PlayerQueue and try again."))
            self.in_progress = False
            return
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
        determine_winner = self.getWinners()
        self.in_progress = False
       
        

        # scheduling each task in the right order, handling states when necessary
        await asyncio.wait_for(first_blind, timeout=45.0)
        self.dealer.dealHands()
        await asyncio.wait_for(show_cards, timeout=None)
        await asyncio.wait_for(preflop_bets, timeout=None)
        await asyncio.wait_for(flop, timeout=None)
        self.setPlayersNotDone(self.players)
        await asyncio.wait_for(turn_bets, timeout=None)
        await asyncio.wait_for(turn, timeout=None)
        self.setPlayersNotDone(self.players)
        await asyncio.wait_for(river_bets, timeout=None)
        await asyncio.wait_for(river, timeout=None)
        await asyncio.wait_for(hand_reveal, timeout=None)
        # next, program logic for calculating winner
        winners = await asyncio.wait_for(determine_winner, timeout=None)
        reward_da_boys = self.rewardWinners(ctx, winners)
        await asyncio.wait_for(reward_da_boys, timeout=None)


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
            best_card = ranker.getHighCardVal(flush)
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
    def getStraights(sorted_cards:list[Card]) -> list[list[Card]]| None:
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
            straight = player.possible_hands[rank] # get player's best straight
            player_high_card = ranker.getHighCardVal(straight)
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
    def getBestStraight(possible_straights:list[list[Card]]) -> list[Card]:
        # (last possible straight will have highest value since the input cards are sorted)
        return possible_straights[-1]

    @staticmethod
    def getStraightFlushes(possible_straights:list[list[Card]], possible_flushes:list[list[Card]]) -> list[list[Card]] | None:
        # check if any of the straights also exist in flushes
        possible_straight_flushes = []
        # n^2 time complexity at least, since iteration increases exponentially as the size of input lists grow
        for straight in possible_straights:
            for flush in possible_flushes:
                check = all(card in straight for card in flush)
                if check is True:
                    possible_straight_flushes.append(flush)

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
            if ranker.getHighCardVal(straight_flush) == ranker.getHighCardVal(best_straight_flush):
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
                if ranker.getHighCardVal(flush) > ranker.getHighCardVal(best_one):
                    best_one = flush
        return best_one

    @staticmethod
    def getRoyalFlush(straight_flushes:list[list[Card]]) -> list | None:
        """
        If hand contains a Royal Flush, returns the royal flush. Otherwise, returns None."""
        royal_flush_key = [10, 11, 12, 13, 14]
        # convert each straight flush to a list of its pip values
        flush_num_values = []
        for flush in straight_flushes:
            pip_flush = [] 
            for card in flush:
                pip_flush = pip_flush + [card.pip_value]
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
        ranker = PokerRanker
        player_to_foak_value:dict[Player, int] = {
            # player: 3, 
            # player2: 6, 
        }
        best_foak_value = 0
        
        def getLeftovers(player:Player, player_foak_value:int):
            """
            Returns the player's complete hand with their four-of-a-kind cards removed."""
            leftovers = player.complete_hand
            for card in leftovers:
                if card.pip_value == player_foak_value:
                    leftovers.remove(card)
            return leftovers

        # populate dict and get best foak value
        for player in players:
            foak_value = player.possible_hands[rank][0].pip_value
            player_to_foak_value[player] = foak_value
            if foak_value > best_foak_value:
                best_foak_value = foak_value
        
        # remove players who don't have best foak value
        for player in players:
            if player_to_foak_value[player] != best_foak_value:
                del player_to_foak_value[player]
        
        # check length of remaining players, if more than one, get best kicker
        remaining_players = len(player_to_foak_value)
        if remaining_players > 1:
            players_to_leftovers = {}
            for player in player_to_foak_value:
                players_to_leftovers[player] = getLeftovers(player, player_to_foak_value[player])
            best_kickers = ranker.getBestKicker(players_to_leftovers, 1)
            return best_kickers
        elif remaining_players == 1:
            return [player for player in player_to_foak_value] # should just be one player
        else:
            raise Exception("Boiiii how did you end up with 0 remaining players? FOAK")

    
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
            if len(full_house) > 0:
                # since triple is assigned to full_house before the double, 
                # we can get the vallue of the triple cards by taking one of the first three cards value,
                # and the pair's value from one of the last two cards.
                # probably not safe, but I think it will work 
                triple_value = full_house[0].pip_value 
                dub_value = full_house[-1].pip_value
                players_to_houses[player] = [triple_value, dub_value]
            else:
                continue
        if len(players_to_houses) == 1:
            return list(players_to_houses.keys())
        
        
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
    def getNofAKind(num_occurences:int, sorted_hand: list[Card]) -> list[Card]:
        """
        Returns a list of of same-valued cards, if those cards exist in the given `sorted_hand`."""
        pip_hand = [card.pip_value for card in sorted_hand] 
        values_to_occurences = Counter(pip_hand)

        for value in values_to_occurences:
            if values_to_occurences[value] == num_occurences:
                # return the value which occurs the same amount as num_occurences
                return [card for card in sorted_hand if card.pip_value == value]
        raise ValueError(f"No value in the input hand, {sorted_hand}, contained {num_occurences} occurences.")        

    @staticmethod
    def getBestKicker(players_to_leftovers:dict[Player, list[Card]], remaining_cards:int) -> list[Player]:
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

        def removeCard(hand:list[Card], value:int):
            """
            Removes a single Card from the input list of cards, by pip value."""
            for card in hand:
                if card.pip_value == value:
                    hand.remove(card)
                    break

        # get each players best kicker
        for player in players_to_leftovers:
            leftovers = players_to_leftovers[player]
            best_kicker = ranker.getHighCardVal(leftovers)
            removeCard(players_to_leftovers[player], best_kicker)
            players_to_kickers[player] = best_kicker
        remaining_cards -= 1

        # find the best kicker, and store players who have the best kicker
        remaining_players:list[Player] = []
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
            players = list(players_to_kickers.keys())
            # remove players who aren't in remaining players from players_to_leftovers, and then call getBestKicker with tihs modified dict
            for player in players:
                if player not in remaining_players:
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
        players_to_hand_values:dict[Player, int] = {
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
            hand_value = player.possible_hands[rank][0].pip_value # get value of one of the three cards
            players_to_hand_values[player] = hand_value

        best_triple_value = getBestTrip(players_to_hand_values)

        # remove players who dont have the best 3 of a kind
        for player in players:
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
    def getMaxOccurences(sorted_hand: list[Card]) -> int:
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
        occurences_list = list(occurences_dict.keys())
        full_house:list[Card] = [] 

        # add three piece to full_house
        for card_value in occurences_list:
            if (occurences_dict[card_value] == 3):
                triple_value = occurences_dict[card_value]
                three_piece = [card for card in sorted_hand if card.pip_value == triple_value]
                full_house = full_house = three_piece
                # can't delete a dictionary entry while iterating through the dictionary. used this a lot and need it fix it everywhere
                del occurences_dict[card_value]
                break
        # add pair to full_house
        for card_value in occurences_list:
            if (occurences_dict[card_value] == 2):
                pair_value = occurences_dict[card_value]
                pair = [card for card in sorted_hand if card.pip_value == pair_value]
                full_house = full_house + pair
                break

        if len(full_house) == 5:
            return full_house
            
        return None
    
    @staticmethod
    def getTwoPair(sorted_hand:list[Card]) -> list[Card] | None:
        """
        Checks whether a player's hand contains two pairs.\n
        Returns the two-pair hand as a list if so, in format [[value1, value1], [value2, value2]], otherwise returns None.\n
        :param list sorted_hand: A list of 7 sorted cards - acceptable in either in normal or pip format.\n"""
        ranker = PokerRanker
        pip_hand:list[int] = [card.pip_value for card in sorted_hand]
        occurences_dict = Counter(pip_hand)
        pairs:list[Card] = []
        # find all pairs
        occurences_list = list(occurences_dict.keys())
        for card_value in occurences_list:
            if occurences_dict[card_value] == 2:
                pair_to_add = [card for card in sorted_hand if card.pip_value == card_value]
                pairs = pairs + pair_to_add
                del occurences_dict[card_value]
        if len(pairs) == 4:
            return pairs
        elif len(pairs) > 4:
            # get the best two pairs
            best_pair1 = ranker.getBestPair(pairs)
            for card in pairs:
                if card.pip_value == best_pair1[0].pip_value:
                    pairs.remove(card)
            best_pair2 = ranker.getBestPair(pairs)
            return best_pair1 + best_pair2
        else:
            return None
    
    @staticmethod 
    def getBestPair(sorted_hand:list[Card]) -> list[Card]: 
        """
        Gets the first pair in a sorted hand, if a pair exists."""
        pip_hand:list[int] = [card.pip_value for card in sorted_hand]
        occurences_dict = Counter(pip_hand)
        possible_pairs:list[list[Card]] = []

        # get any possible pairs
        for card_value in occurences_dict:
            if occurences_dict[card_value] == 2:
                pair = [card for card in sorted_hand if card.pip_value == card_value]
                possible_pairs.append(pair)
        
        # return highest value pair if there's more than one
        best_pair = possible_pairs[0] # list of list of cards
        best_pair_val = best_pair[0].pip_value 
        for pair in possible_pairs:
            pair_val = pair[0].pip_value
            if pair_val > best_pair_val:
                best_pair_val = pair_val
        
        # get best pair
        for pair in possible_pairs:
            if pair[0].pip_value == best_pair_val:
                best_pair = pair
        
        return best_pair


    @staticmethod
    def breakPairTie(players:list[Player]) -> list[Player]:
        ranker = PokerRanker
        rank = Poker.HANDS_TO_RANKS["pair"]
        players_to_hand_value:dict[Player, int] = {
            # player: 5,
        }

        def getBestPairVal(players_dict:dict[Player, int]) -> int:
            best_pair_val = 0
            for player in players_dict:
                pair_val = players_dict[player]
                if pair_val > best_pair_val:
                    best_pair_val = pair_val
            return best_pair_val
            
        # populate dict
        for player in players:
            hand_value = player.possible_hands[rank][0].pip_value # int
            players_to_hand_value[player] = hand_value
        # get best pair
        best_pair_val = getBestPairVal(players_to_hand_value)
        # remove players who don't have best pair
        for player in players:
            player_pair = players_to_hand_value[player]
            if player_pair < best_pair_val:
                del players_to_hand_value[player]

        if len(players_to_hand_value) < 1:
            raise Exception("The developer (Parker) has made a grave mistake while coding this tie case. Please revise")
        elif len(players_to_hand_value) == 1:
            return list(players_to_hand_value.keys())
        
        else: # if len players with best value is greater than 1, get best kicker
            players_to_leftovers:dict[Player, list[Card]] = {
            # player: [4, 5, 7, 9],
            }
            # populate players to kickers
            for player in players:
                leftovers = [card for card in player.complete_hand if card.pip_value != players_to_hand_value[player]]
                players_to_leftovers[player] = leftovers
            winners = ranker.getBestKicker(players_to_leftovers, 5)
            return winners
    
    @staticmethod
    def breakTwoPairTie(players:list[Player]) -> list[Player]:
        """
        Compares the input players' two pair values to get the best ranked player.\n
        If two pairs are equal, winner is determined by highest kicker."""
        ranker = PokerRanker
        rank = Poker.HANDS_TO_RANKS["two pair"]
        players_to_two_pair_values:dict[Player, list[int]] = {
            # player: [value1, value2],
        }

        def findBestPair(players_to_pairs:dict) -> int:
            best_pair_value = 0
            for player in players_to_pairs:
                for pair_val in players_to_pairs[player]:
                    if pair_val > best_pair_value:
                        best_pair_value = pair_val
            return best_pair_value
        
        def removeCard(hand:list[Card], value:int):
            for card in hand:
                if card.pip_value == value:
                    hand.remove(card)
                    break

        def getLeftovers(player:Player, two_pair_vals:list) -> list[Card]:
            leftovers = [card for card in player.complete_hand] # player complete hand is a list of cards
            pair1_val = two_pair_vals[0]
            pair2_val = two_pair_vals[1]
            for i in range(2):
                removeCard(leftovers, pair1_val)
                removeCard(leftovers, pair2_val)
            return leftovers
        
        # populate dict with two-pair's values
        for player in players:
            value1 = player.possible_hands[rank][0].pip_value
            value2 = player.possible_hands[rank][1].pip_value
            players_to_two_pair_values[player] = [value1, value2]

        # need to store the player with the highest pair1 value
            # if any players share the highest pair value, compare their next highest pairs
                # if still tied, compare kickers and return player with best kicker

        # get the best pair
        best_pair_val = findBestPair(players_to_two_pair_values)

        # store all players who have a pair the value of best pair, and remove this value from players who have it
        for player in players:
            player_pairs = players_to_two_pair_values[player]
            if best_pair_val in player_pairs:
                players_to_two_pair_values[player].remove(best_pair_val) # remove instances of best value from players who have it
            elif best_pair_val not in player_pairs:
                del players_to_two_pair_values[player]
                 # completely remove players who don't have the best value

        remaining_players = [player for player in players_to_two_pair_values]

        if len(remaining_players) < 1:
            raise Exception("bruh moment")
        elif len(remaining_players) == 1:
            return remaining_players
        else:
            # if more than one player remains, compare the players' next pair
            best_pair_val = findBestPair(players_to_two_pair_values)

            # repeat steps used to compare first pair
            for player in remaining_players:
                player_pairs = players_to_two_pair_values[player]
                if best_pair_val in player_pairs:
                    players_to_two_pair_values[player].remove(best_pair_val)
                elif best_pair_val not in player_pairs:
                    del players_to_two_pair_values[player]

            remaining_players = [player for player in players_to_two_pair_values]

            if len(remaining_players) < 1:
                raise Exception("The developer (Parker) has made a grave mistake while coding this tie case. Please revise")
            elif len(remaining_players) == 1:
                return remaining_players
            else: 
                # if there are still tied players, winner is determined by whoever has the best kicker
                players_to_leftovers:dict[Player, list[Card]] = {
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
    def getHighCard(sorted_hand:list[Card]) -> list[Card]:
        """
        Returns the highest value card from a list of Cards."""
        highest_card = sorted_hand[0]
        for card in sorted_hand:
            card_val = card.pip_value 
            if card_val > highest_card.pip_value:
                highest_card = card
        return [highest_card]

    @staticmethod
    def getHighCardVal(hand:list[Card]) -> int:
        """
        Returns the highest pip value of all cards in a player's hand.
        :param list sorted_hand: A list of cards.\n"""
        highest_card_val = 0
        for card in hand:
            card_val = card.pip_value 
            if card_val > highest_card_val:
                highest_card_val = card_val
        return highest_card_val

    @staticmethod
    def breakHighCardTie(players:list[Player]) -> list[Player]:
        ranker = PokerRanker
        # wrap up logic in a function since we will have to execute the exact same thing again twice if players are tied after the first go
        def getBestPlayers(players:list[Player]):
            players_to_best_val:dict[Player, int] = {}
            best_val = 0
            for player in players:
                best_card = ranker.getHighCard(player.hand)[0] # highest card will be last since cards are sorted in ascending order
                players_to_best_val[player] = best_card.pip_value
                if best_card.pip_value > best_val:
                    best_val = best_card.pip_value
                player.hand.remove(best_card)
            #compare best vals, keep only the players who have the highest value
            for player in players:
                if players_to_best_val[player] != best_val:
                    del players_to_best_val[player]
            return players_to_best_val
        

        players_to_best_val = getBestPlayers(players)
        if len(players_to_best_val) > 1:
            final_players = list(players_to_best_val.keys())
            final_winners = getBestPlayers(final_players)
            return list(final_winners.keys()) # return the players who remain in the dict, as a list
            
        elif len(players_to_best_val) == 1:
            return list(players_to_best_val.keys())

        else:
            raise Exception("Boi how tf did you return no winners during a high card comparison. You are wild")
            

        
        # need to compare the two cards players are dealt.
        # if players tie with these two cards, then return them both, because that means the rest of their cards
        # (the community cards) will be the same, resulting in a tie.


async def setup(bot):
    await bot.add_cog(GamesController(bot))        

