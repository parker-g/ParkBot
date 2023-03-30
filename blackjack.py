import random
import pandas as pd
import datetime
import logging
from helper import countdown
from discord.ext.commands.cog import Cog
from discord.ext import commands
from discord import Member
from config.config import BANK_PATH

logger = logging.Logger('BJLog')

class Economy(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def withdraw_money(member:Member, money) -> None:
        bank_df = pd.read_csv(BANK_PATH, header="infer")
        users = bank_df.Usernames
        # if member isn't in dataframe already, put them in and give them 100 GleepCoins
        if member.name not in users:
            bank_df.loc[len(bank_df.index)] = [member.name, 100]
        current_balance = bank_df.loc[member.name, 'GleepCoins']
        bank_df.loc[member.name, "GleepCoins"] = current_balance - money
        bank_df.to_csv(BANK_PATH, index=False)

    @commands.command()
    async def award_money(self, member:Member, money):
        bank_df = pd.read_csv(BANK_PATH, header='infer')
        users = bank_df.Usernames
        if member.name not in users:
            bank_df.loc[len(bank_df.index)] = [member.name, 100]
        current_balance = bank_df.loc[member.name, 'GleepCoins']
        bank_df.loc[member.name, "GleepCoins"] = current_balance + money
        bank_df.to_csv(BANK_PATH, index=False)


        
        




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

    def getWinner(self, players:list[Player]) -> str:
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
        # check if more than one player share highest score

        if (len(winners) > 1):
            winners_string = ""
            for winner in winners:
                winners_string += f"{winner.name}, "
            return winners_string
        elif len(winners) == 1:
            winner = winner.name

         # if multiple winners, return a string of their names, else return string of sole winner name
        if players_busted == len(players):
            winner = "None"
        # ^ if all players busted, winner = "None"
        return winner, highest_score
        



class BlackJackGame(Cog):
    @commands.command("openJack")
    async def __init__(self, ctx, bot):
        self.bot = bot
        # timer is false, becomes true once countdown is over
        deck = Deck()
        deck.shuffle()
        self.players = []
        # for name in args:
        #     player = Player(name)
        #     self.players.append(player)
        self.dealer = Dealer(deck, self.players)
        await ctx.send("BlackJack game has been initialized. Please join queue with cocmmand `joinQ'.")
    
    @command.command()
    async def joinQ(self, ctx):
        new_player = Player(ctx)
        self.players.append(new_player)
        logger.log("New player added to blackjack queue.")
        


    def newRound(self, players:list[Player]) -> None:
        self.dealer.dealHands()
        for player in players:
            player.winner = False
            player.done = False
            player.bust = False
            player.blackJack = False

    def showHands(self, players:list[Player]):
        for player in players:
            print(f"\n{player.name} shows their cards. Their hand looks like this: {player.hand}. ")
    
    def takeTurn(self, player:Player, wantToHit:bool):
        if wantToHit is False:
            pass
        player.dealCard()

    def play(self):
        self.newRound(self.players)
        for player in self.players:
            print(f"\nIt's your turn, {player.name}!")
            while player.done != True:
                wannaGo = input(f"Your total right now is {player.sumCards()}. Hit or stay?: ")
                if wannaGo.lower() == "hit":
                    self.dealer.dealCard(player)
                    if player.isBust():
                        player.done = True
                        print(f"You busted! Your total is: {player.sumCards()}.")
                elif wannaGo.lower() != "hit":
                    player.done = True
        # when all players are done

        winner, highest_score = self.dealer.getWinner(self.players)   
        win_statement = f"\nAnd the winner for this hand is: {winner}"     
        sum_statement = f" with a sum of {highest_score}."    
        if highest_score != 0:
            print(win_statement + sum_statement)
        else:
            print(win_statement)
            
        print("\nHere's everyone's hands.\n")
        for player in self.players:
            print(player.name, player.hand, player.sumCards())







        
