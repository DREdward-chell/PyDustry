import pygame
import os
import sys


def load_image(name: str) -> pygame.Surface:
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


def neighbour(x: int, y: int, array: list) -> int:
    try:
        assert x >= 0 and y >= 0
        if array[x][y] is not None:
            return 1
        else:
            return 0
    except IndexError or AssertionError:
        return 0
