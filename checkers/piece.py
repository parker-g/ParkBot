# from board import Board
from board import Board
# def previous_and_next(some_iterable):
#     prevs, items, nexts = tee(some_iterable, 3)
#     prevs = chain([None], prevs)
#     nexts = chain(islice(nexts, 1, None), [None])
#     return zip(prevs, items, nexts)

class Checker:
    def _init_(self, board):
        self.board_list = [board.board.split('')]
        print(self.board_list)
        self.positions = []


b = Board()
checker = Checker(b)
print(checker.board_list)