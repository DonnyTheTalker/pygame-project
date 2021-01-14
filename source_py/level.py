import pygame
import json
from main import Tile

pygame.init()


class Level:
    def __init__(self):
        self.CELL_SIZE = 32
        self.all_sprites = pygame.sprite.Group()
        self.background_group = pygame.sprite.Group()
        self.tiles_group = pygame.sprite.Group()
        self.frontground_group = pygame.sprite.Group()
        self.grid_size = self.grid_width, self.grid_height = None, None

    def load_level(self, dct: dict):
        if "__Level__" not in dct:
            return
        self.CELL_SIZE = dct["CELL_SIZE"]
        self.grid_size = self.grid_width, self.grid_height = dct["grid_size"]
        self.background_group = pygame.sprite.Group(dct["background_group"])
        self.tiles_group = pygame.sprite.Group(dct["tiles_group"])
        self.frontground_group = pygame.sprite.Group(dct["frontground_group"])
        self.all_sprites = pygame.sprite.Group()
        for group in [self.background_group, self.tiles_group, self.frontground_group]:
            self.all_sprites.add(*group.sprites())

    def draw(self, surface):
        self.background_group.draw(surface)
        self.tiles_group.draw(surface)
        self.frontground_group.draw(surface)


class MainEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Level):
            return {"__Level__": True, "grid_size": o.grid_size, "CELL_SIZE": o.CELL_SIZE,
                    "background_group": o.background_group.sprites(),
                    "tiles_group": o.tiles_group.sprites(),
                    "frontground_group": o.frontground_group.sprites()}
        elif isinstance(o, Tile):
            return {"__Tile__": True,
                    "image": o.image,
                    "x": o.rect.x,
                    "y": o.rect.y}
        elif isinstance(o, pygame.Surface):
            width, height = o.get_width(), o.get_height()
            pixels = [[o.get_at((i, j)) for j in range(height)] for i in range(width)]
            return {"__Surface__": True,
                    "width": width, "height": height, "pixels": pixels}
        elif isinstance(o, pygame.Color):
            return {"__Color__": True,
                    "rgba": (o.r, o.g, o.b, o.a)}
        else:
            json.JSONEncoder.default(self, o)


def main_decoder(dct):
    if "__Level__" in dct:
        level = Level()
        level.load_level(dct)
        return level
    elif "__Tile__" in dct:
        return Tile(dct["image"], dct["x"], dct["y"])
    elif "__Surface__" in dct:
        surf = pygame.Surface((dct["width"], dct["height"]))
        for i in range(dct["width"]):
            for j in range(dct["height"]):
                surf.set_at((i, j), pygame.Color(dct["pixels"][i][j]))
        return surf
    elif "__Color__" in dct:
        return pygame.Color(*dct["rgba"])
    else:
        return dct
