import sys
import pygame
import os
import json
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QPushButton, QButtonGroup
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import QTimer
from main import load_image, Tile, Level, MainEncoder, main_decoder

pygame.init()


def cut_sheets(sheet, names, cell_size, columns, rows):
    rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
    frames = list()
    for j in range(rows):
        for i in range(columns):
            frame_coords = rect.w * i, rect.h * j
            frames.append(pygame.transform.scale(sheet.subsurface(pygame.Rect(frame_coords,
                                                                              rect.size)),
                                                 (cell_size, cell_size)))
    tiles = dict()  # словарь surface tile по его кодовому символу
    for i, tile_image in enumerate(frames):
        tiles[names[i]] = tile_image
    reversed_tiles = {sprite: key for key, sprite in tiles.items()}
    return tiles, reversed_tiles


def load_sprites_from_grid(tiles, names, cell_size, grid_width, grid_height, grid, *groups):
    for i, line in enumerate(grid):
        for j, symb in enumerate(line):
            if symb != '.':
                Tile(tiles[symb], j * cell_size, i * cell_size, *groups)


class Main(QMainWindow):
    def __init__(self, spritesheet):
        super().__init__()
        pygame.init()
        # self.setupUi(self)
        uic.loadUi("../data/UI files/designer.ui", self)
        self.spritesheet = load_image(spritesheet)
        self.level = Level()
        self.layer = self.level.tiles_group
        self.names = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # кодовые символы
        self.tiles, self.reversed_tiles = cut_sheets(self.spritesheet, self.names,
                                                     self.level.CELL_SIZE, 10, 4)
        self.initUI()
        self.resize_window()
        self.timer.start(10)

    def initUI(self):
        y_offset = self.height()
        self.resizeButton.clicked.connect(self.resize_window)
        self.arrows.buttonClicked.connect(self.move_surface)
        self.layerButtons.buttonClicked.connect(self.change_layer)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_events)
        self.actionopen.triggered.connect(self.open)
        self.actionsave.triggered.connect(self.save)
        self.tile_buttons = QButtonGroup(self)
        for i, tile_code in enumerate(self.tiles):
            button = QPushButton(tile_code, self)
            button.resize(self.level.CELL_SIZE, self.level.CELL_SIZE)
            button.move(20 + i % 10 * (self.level.CELL_SIZE + 10),
                        y_offset + i // 10 * (self.level.CELL_SIZE + 10))
            self.tile_buttons.addButton(button)
        self.setFixedSize(max(self.width(), 20 + 10 * (self.level.CELL_SIZE + 10)),
                          y_offset + i // 10 * (self.level.CELL_SIZE + 10) + button.height() + 10)
        self.tile_buttons.buttonClicked.connect(self.select_tile)
        self.tile_buttons.buttons()[0].click()

    def init_screen(self):
        self.screen = pygame.display.set_mode(
            ((self.level.grid_width + 1) * self.level.CELL_SIZE,
             self.level.grid_height * self.level.CELL_SIZE))
        self.paint()

    def resize_window(self):
        width, height = self.widthBox.value(), self.heightBox.value()
        self.level.grid_size = self.level.grid_width, self.level.grid_height = width, height
        self.init_screen()
        self.delete_abroad()
        self.paint()

    def change_layer(self, button):
        query = f'self.layer = self.level.{button.text()}_group'
        exec(query)

    def select_tile(self, button):
        self.current_tile = button.text()

    def move_surface(self, key):
        encode = {"↑": (0, -1), "→": (1, 0), "↓": (0, 1), "←": (-1, 0)}
        dx, dy = encode[key.text()]
        for sprite in self.layer.sprites():
            sprite.rect = sprite.rect.move(dx * self.level.CELL_SIZE, dy * self.level.CELL_SIZE)
        self.delete_abroad()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 or event.button == 4:
                    self.add_sprite(event.pos)
                elif event.button == 3 or event.button == 5:
                    self.del_sprite(event.pos)
        self.paint()

    def paint(self):
        self.screen.fill(pygame.Color("white"))
        if self.displayMode.isChecked():
            self.level.draw(self.screen)
        else:
            self.layer.draw(self.screen)
        self.screen.blit(self.tiles[self.current_tile],
                         (self.level.grid_width * self.level.CELL_SIZE, 0))
        if self.gridMode.isChecked():
            color = pygame.Color("red")
            for i in range(1, self.level.grid_width + 1):
                pygame.draw.line(self.screen, color,
                                 (i * self.level.CELL_SIZE, 0),
                                 (i * self.level.CELL_SIZE,
                                  self.level.grid_height * self.level.CELL_SIZE), 1)
            for j in range(1, self.level.grid_height):
                pygame.draw.line(self.screen, color, (0, j * self.level.CELL_SIZE),
                                 (self.level.grid_width * self.level.CELL_SIZE,
                                  j * self.level.CELL_SIZE), 1)
        pygame.display.flip()

    def add_sprite(self, pos):
        x, y = pos
        x = x // self.level.CELL_SIZE * self.level.CELL_SIZE
        y = y // self.level.CELL_SIZE * self.level.CELL_SIZE
        if x // self.level.CELL_SIZE >= self.level.grid_width:
            return
        self.del_sprite(pos)
        Tile(self.tiles[self.current_tile], x, y, self.level.all_sprites, self.layer)

    def del_sprite(self, pos):
        x, y = pos
        for sprite in self.layer.sprites():
            if sprite.rect.collidepoint(x, y):
                sprite.kill()

    def delete_abroad(self):
        for sprite in self.level.all_sprites.sprites():
            if not (0 <= sprite.rect.x <= (self.level.grid_width - 1) * self.level.CELL_SIZE and
                    0 <= sprite.rect.y <= (self.level.grid_height - 1) * self.level.CELL_SIZE):
                sprite.kill()

    def save(self):
        name = self.nameEdit.text()
        if not name:
            print("Ошибка ввода имени")
            return
        with open(f'../data/levels/{name}.json', 'w', encoding='utf-8') as file:
            json.dump(self.level, file, cls=MainEncoder)

    def open(self):
        path = QFileDialog.getOpenFileName(self, 'Выбрать уровень', '')[0]
        if not path:
            print("Ошибка выбора файла")
            return
        with open(path, 'r', encoding='utf-8') as file:
            self.level = json.load(file, object_hook=main_decoder)
        self.tiles, self.reversed_tiles = cut_sheets(self.spritesheet, self.names,
                                                     self.level.CELL_SIZE, 10, 4)
        self.layer = self.level.tiles_group


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Main("forest_spritesheet.png")
    ex.show()
    sys.exit(app.exec())
