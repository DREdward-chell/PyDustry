import pygame
from TileClass import Tile


class Field:
    width: int
    w: int
    height: int
    h: int
    board: list

    def __init__(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        self.w, self.h = width, height
        self.board = [[None for _ in range(width)]] * height

    def __str__(self) -> str:
        return str(self.board)

    def __getitem__(self, key: tuple) -> int or Tile or None:
        x, y = key
        return self.board[x][y]

    def __setitem__(self, key: tuple, value: int or Tile or None) -> None:
        x, y = key
        self.board[x][y] = value

    def render(self, surface: pygame.Surface) -> None:
        pass

    def placeable(self, coord: tuple, object_size: tuple) -> bool:
        pass

    def check_neighbours(self, coord: tuple, ret: str = "integer") -> int or tuple:
        # if param == "integer":
        #     pass
        # elif param == "tuple":
        #     pass
        pass

    def __rshift__(self, surface: any) -> None:
        self.render(surface)
