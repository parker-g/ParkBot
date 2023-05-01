import random
import logging
import asyncio
from cogs.economy import Economy
from config.config import BANK_PATH
from discord.ext.commands.cog import Cog
from discord.ext import commands
from discord import Member, Embed
from helper import getUserAmount, readThreads, writePlayerAndThread, bubbleSort



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
        "♠": "black",
        "♣": "black",
        "♥": "red",
        "♦": "red",
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
            self.deck.append((Deck.card_legend[i], "♠"))
            self.deck.append((Deck.card_legend[i], "♣"))
            self.deck.append((Deck.card_legend[i], "♥"))
            self.deck.append((Deck.card_legend[i], "♦"))



    def isFlush(seven_sorted_cards:list):
        """Takes a sorted list consisting of both a player's hand and the community cards.
        Returns True if hand is a flush."""
    def checkCards(seven_sorted_cards:list):
        pass
    
    def isStraight(sorted_cards:list, prev_num = -999):
        """Takes a sorted list consisting of both a player's hand and the community cards.
        Returns True if hand is a straight."""
        consecutive_cards = []
        num_consecutive_cards = 0
        for num, suit in sorted_cards:
            if len(consecutive_cards) == 5:
                return consecutive_cards
            if prev_num == num - 1:
                prev_num = num
                Deck.isStraight(sorted_cards[1:], prev_num)
        # for every card in the deck, we want to check if the card with one value up exists in all_cards.
            # if so, then loop again, checking for the next highest value, repeat


    def formatCard(card_tuple:tuple) -> str:
        return f"{card_tuple[0].capitalize()} {card_tuple[1]}s"

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

    def resetPlayer(self):
        self.hand = []
        self.bet = 0
        self.done = False
        self.winner = False

    def pushToPot(self, pot):
        pot += self.bet
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
            pretty_string += f" {num} {suit}, "
        last_num, last_suit = self.hand[-1]
        pretty_string += f"{last_num} {last_suit}"
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

        # for player, member in self.q:
        #     if ctx.author.name == player.name:
        #         # if so, tell user that they're already in the queue
        #         message_str = f"{ctx.author.name} is already in queue."
        #         message = await ctx.send(embed = Embed(title=message_str))
        #         await message.delete(delay=5.0)
        #         return

        # so Q will be a list of tuples of (player object, discord.Member object)
        self.q.append((new_player, ctx.author))
        message_str = f"{ctx.author.name} has been added to players queue."
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

    async def _setBet(self, ctx, inputPlayer, bet:int):
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
        economy = Economy(self.bot)
        amount = random.randint(1, 20)
        await economy.giveMoney(ctx, float(amount))
        beg_message = await ctx.send(embed=Embed(title=f"{ctx.author.name} recieved {amount} GleepCoins from begging."))
        await beg_message.delete(delay=5.0)

    @commands.command()
    async def playJack(self, ctx):
        blackjack = BlackJackGame(self.bot, self)
        await blackjack.play(ctx)

    @commands.command()
    async def playPoker(self, ctx):
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


    def dealFlop(self, pokerGame):
        # throw out the top card
        self.deck.pop(0)
        self.dealPokerCommunityCard(pokerGame, 3)
        
    def dealPokerCommunityCard(self, pokerGame, cards = 1):
        for i in range(cards):
            pokerGame.community_cards.append(self.deck[0])
            self.deck.pop(0)


    def dealCard(self, player:Player):
        player.hand.append(self.deck[0])
        self.cards_in_play.append(self.deck[0])
        self.deck.remove(self.deck[0])

    def dealHands(self) -> None:
        for i in range(2):
            for player in self.players:
                self.dealCard(player)
    #return cards doesn't work, need to fix maybe

    def returnCardsToDeck(self):
        self.deck += self.cards_in_play
        self.cards_in_play = []

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

    def showHands(self, players:list[Player]) -> None:
        for player in players:
            print(f"\n{player.name} shows their cards. Their hand looks like this: {player.hand}. ")
    
    async def cashOut(self, ctx, players) -> None:
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
                    
    
    def getWinners(self, players:list[Player]) -> list[Player]:
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


# could lowkey create a Game super class that BlackJack and Poker would inherit from - simply making them share attributes such as the 
# bot, deck, player queue, players, and dealer.



class Poker(commands.Cog):
    def __init__(self, bot, player_queue:PlayerQueue):
        self.bot = bot
        self.deck = Deck()
        self.deck.shuffle()
        self.player_queue = player_queue
        self.players = []
        for player, member in self.player_queue.q:
            self.players.append(player)
        self.dealer = Dealer(self.deck, self.players)
        
        # poker specific attributes 
        self.community_cards = []
        self.small_blind = 0
        self.big_blind = 0
        self.small_blind_idx = None
        self.big_blind_idx = None
        self.channel = None
        self.threads = {} # contains player names as keys, and discord.Thread objects as values - used to send private messages to players
        self.pot = 0 # holds all bets
        self.post_flop = False # used to modify the self.takeBets() method to make it appropriate for a pre-flop vs a post flop betting round
        self.early_finish = False # responsible for state of whether a game has ended early (due to all but 1 player folding)


    def resetPlayers(self) -> None:
        economy = Economy()
        for player in self.players:
            player.winner = False
            player.done = False
            player.hand = []
            player.button = False
            player.thread = None
            player.folded = False
            if player.bet > 0:
                economy.giveMoneyPlayer(player, player.bet)
                player.bet = 0
            

    def setPlayersNotDone(self):
        for player in self.players:
            player.done = False

    def getCommunityCardsString(self):
        pretty_string = ""
        for card in self.community_cards:
            pretty_string += f"{Deck.formatCard(card)}\n"
        return pretty_string

    def allPlayersDone(self) -> bool:
        for player in self.players:
            if player.done == False:
                return False
        return True

    def getThreads(self):
        self.threads = readThreads()
        return

    def writeNewThread(self, player, thread_id:int):
        writePlayerAndThread(player.name, thread_id)
        return
    
    def setPlayersNotDone(self):
        for player in self.players:
            player.done = False

    async def showAllHands(self, ctx):
        all_hands = ""
        for player in self.players:
            all_hands += f"{player.name}: {player.prettyHand()}\n"
        await ctx.send(embed=Embed(title=f"Everyone's Hand", description=all_hands))

    async def showHands(self):
        for player in self.players:
            member = [user for user in self.player_queue.q if user[0].name == player.name][0][1]
            # player.name == member.name
            if not player.name in self.threads:
                # print(f"creating thread for {player.name}")
                thread = await self.channel.create_thread(name="Your Poker Hand", reason = "poker", auto_archive_duration = 60)
                self.threads[player.name] = thread
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

    async def getPokerChannel(self, ctx):
        async for guild in self.bot.fetch_guilds():
            if guild.name == "Orlando Come":
                self.guild = guild
                channels = await guild.fetch_channels()
                for channel in channels:
                    if channel.name == "poker":
                        return channel
    
    async def assignButtonAndPostBlinds(self, ctx):
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

    async def takePreFlopBets(self, ctx, name_of_betting_round:str):
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
                    self.player[0].winner = True
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
                    self.player[0].winner = True
                    await ctx.send(embed=Embed(title=f"{self.players[0].name} is the last player standing."))
                    self.early_finish = True    
                
            pf_msg = await ctx.send(embed=Embed(title=f"Pre flop betting has come to an end."))
            await pf_msg.delete(delay=10.0)
            return
        else:
            return
        
    async def getWinners(self, players):
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
            # only do all the important stuff if there's more than one player who made it this far
            for player in self.players:
                # run through a list of functions that will help determine the player's ranking for their current hand.
                pass
        pass


    async def flop(self, ctx):
        self.dealer.dealFlop(self)
        cards_string = self.getCommunityCardsString()
        await ctx.send(embed=Embed(title=f"Community Cards", description = cards_string))

    async def dealCommunityCard(self, ctx):
        if self.early_finish is not True:
            self.dealer.dealPokerCommunityCard(self)
            cards_string = self.getCommunityCardsString()
            await ctx.send(embed=Embed(title=f"Community Cards", description = cards_string))
        else:
            return
    
    async def play(self, ctx):
        # setup
        self.resetPlayers()
        self.post_flop = False
        self.getThreads()
        self.channel = await self.getPokerChannel(ctx)

        # turning each async function into a task
        first_blind = self.assignButtonAndPostBlinds(ctx)
        show_cards = self.showHands()
        preflop_bets = self.takePreFlopBets(ctx, "flop")
        flop = self.flop(ctx)
        turn_bets = self.takePostFlopBets(ctx, "turn")
        turn = self.dealCommunityCard(ctx)
        river_bets = self.takePostFlopBets(ctx, "river")
        river = self.dealCommunityCard(ctx)
        hand_reveal = self.showAllHands(ctx)
        
        # executing each task in the right order, handling states when necessary
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





    
    
async def setup(bot):
    await bot.add_cog(PlayerQueue(bot))        
