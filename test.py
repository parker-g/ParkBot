import pandas as pd
from cogs.blackjack import Dealer, Deck
# created this file to test requesting an image from url, opening it,
# saving it, and returning image url

# def img_test0():
#     image_url = ''
#     response = requests.get(image_url) # collect image data from url
#     destination_url = 'images/image.png'
#     with open(destination_url, 'wb') as file:
#         file.write(response.content)
#     return destination_url

class PlayerTest:

    def __init__(self):
        self.hand = []
        self.bust = False

    def isBust(self):
        if self.bust is True:
            return True
        return False


deck = Deck()
deck.shuffle()
players = []
for i in range(3):
    player = PlayerTest()
    players.append(player)

dealer = Dealer(deck, players)


dealer.bust = True
players.append(dealer)
print(players)
dealer.dealHands()
dealer.dealToSelf()

for player in players:
    print(player.hand)
print()



#############################################################
# results = Dealer.isBust() method isn't working properly. 
# could be because dealer isn't properly dealing cards to self? If this was case though, then dealer hand wouldn't be getting dealt in the beginning of rounds



# def test(players):
#     for player in players:
#         if player.isBust():
#             print(f"{player} busted.")
#         else:
#             print(f"{player} hasn't busted.")

# test(players)

