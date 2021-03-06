from lib.data.model.shared.abstract_board import AbstractBoard
from lib.data.model.shared.cell import Cell
from lib.data.model.shared.player import Player

class TicTacToeBoard(AbstractBoard):

    def __init__(self, size):
        self.height = self.width = size
        self.board = [[Cell(j, i) for i in range(size)] for j in range(size)]