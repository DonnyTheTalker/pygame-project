import sys
import pygame
import os
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QLabel, QLCDNumber, QButtonGroup
from PyQt5.QtWidgets import QCheckBox, QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5 import QtWidgets
from main import load_image, Tile


def cut_sheets(sheet, cell_size, columns, rows):
    rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
    frames = list()
    for j in range(rows):
        for i in range(columns):
            frame_coords = rect.w * i, rect.h * j
            frames.append(pygame.transform.scale(sheet.subsurface(pygame.Rect(frame_coords, rect.size)),
                                                 (cell_size, cell_size)))
    return frames


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        pygame.init()
        # self.setupUi(self)
        uic.loadUi("../data/UI files/designer.ui", self)
        self.CELL_SIZE = 32
        self.all_sprites = pygame.sprite.Group()
        self.background_group = pygame.sprite.Group()
        self.tiles_group = pygame.sprite.Group()
        self.frontground_group = pygame.sprite.Group()
        self.layer = self.tiles_group
        self.display_mode = [self.background_group, self.tiles_group, self.frontground_group]
        self.names = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # кодовые символы
        self.tiles = dict()  # словарь surface tile по его кодовому символу
        for i, tile_image in enumerate(cut_sheets(load_image("forest_spritesheet.png"), self.CELL_SIZE, 10, 4)):
            self.tiles[self.names[i]] = tile_image
        self.reversed_tiles = {image: key for key, image in self.tiles.items()}
        self.initUI()
        self.resize_window()
        self.timer.start(10)

    def initUI(self):
        y_offset = self.height()
        self.resizeButton.clicked.connect(self.resize_window)
        self.saveButton.clicked.connect(self.save)
        self.arrows.buttonClicked.connect(self.move_surface)
        self.layerButtons.buttonClicked.connect(self.change_layer)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_events)
        self.tile_buttons = QButtonGroup(self)
        for i, tile_code in enumerate(self.tiles):
            button = QPushButton(tile_code, self)
            button.resize(self.CELL_SIZE, self.CELL_SIZE)
            button.move(20 + i % 10 * (self.CELL_SIZE + 10), y_offset + i // 10 * (self.CELL_SIZE + 10))
            self.tile_buttons.addButton(button)
        self.setFixedSize(20 + 10 * (self.CELL_SIZE + 10),
                          y_offset + i // 10 * (self.CELL_SIZE + 10) + button.height() + 10)
        self.tile_buttons.buttonClicked.connect(self.select_tile)
        self.tile_buttons.buttons()[0].click()

    def init_screen(self):
        self.screen = pygame.display.set_mode(
            ((self.grid_width + 1) * self.CELL_SIZE, self.grid_height * self.CELL_SIZE))
        self.paint()

    def resize_window(self):
        width, height = self.widthBox.value(), self.heightBox.value()
        self.grid_size = self.grid_width, self.grid_height = width, height
        self.init_screen()
        self.delete_abroad()
        self.paint()

    def change_layer(self, button):
        query = f'self.layer = self.{button.text()}_group'
        exec(query)
        if self.layer is self.background_group:
            print("Выбрал background")
        elif self.layer is self.tiles_group:
            print("Выбрал tiles")
        elif self.layer is self.frontground_group:
            print("Выбрал frontground")
        else:
            print("Ачё я выбрал?")

    def select_tile(self, button):
        self.current_tile = button.text()

    def move_surface(self, key):
        encode = {"↑": (0, -1), "→": (1, 0), "↓": (0, 1), "←": (-1, 0)}
        dx, dy = encode[key.text()]
        for sprite in self.layer.sprites():
            sprite.rect = sprite.rect.move(dx * self.CELL_SIZE, dy * self.CELL_SIZE)
        self.delete_abroad()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.add_sprite(event.pos)
                elif event.button == 3:
                    self.del_sprite(event.pos)
        self.paint()

    def paint(self):
        self.screen.fill(pygame.Color("white"))
        if self.displayMode.isChecked():
            self.background_group.draw(self.screen)
            self.tiles_group.draw(self.screen)
            self.frontground_group.draw(self.screen)
        else:
            self.layer.draw(self.screen)
        self.screen.blit(self.tiles[self.current_tile], (self.grid_width * self.CELL_SIZE, 0))
        if self.gridMode.isChecked():
            color = pygame.Color("red")
            for i in range(1, self.grid_width + 1):
                pygame.draw.line(self.screen, color, (i * self.CELL_SIZE, 0),
                                 (i * self.CELL_SIZE, self.grid_height * self.CELL_SIZE), 1)
            for j in range(1, self.grid_height):
                pygame.draw.line(self.screen, color, (0, j * self.CELL_SIZE),
                                 (self.grid_width * self.CELL_SIZE, j * self.CELL_SIZE), 1)
        pygame.display.flip()

    def add_sprite(self, pos):
        x, y = pos
        x = x // self.CELL_SIZE * self.CELL_SIZE
        y = y // self.CELL_SIZE * self.CELL_SIZE
        if x // self.CELL_SIZE >= self.grid_width:
            return
        self.del_sprite(pos)
        Tile(self.tiles[self.current_tile], x, y, self.all_sprites, self.layer)

    def del_sprite(self, pos):
        x, y = pos
        for sprite in self.layer.sprites():
            if sprite.rect.collidepoint(x, y):
                sprite.kill()

    def delete_abroad(self):
        for sprite in self.all_sprites.sprites():
            if not (0 <= sprite.rect.x <= (self.grid_width - 1) * self.CELL_SIZE and
                    0 <= sprite.rect.y <= (self.grid_height - 1) * self.CELL_SIZE):
                sprite.kill()

    def save(self):
        name = self.nameEdit.text()
        if not name:
            return
        os.mkdir(f'../data/levels/{name}')
        for layer in ["background", "tiles", "frontground"]:
            with open(f'../data/levels/{name}/{layer}.txt', 'w', encoding='utf-8') as file:
                grid = [["."] * self.grid_width for i in range(self.grid_height)]
                exec(f'self.current_group = self.{layer}_group')
                for sprite in self.current_group.sprites():
                    x, y = sprite.rect.x // self.CELL_SIZE, sprite.rect.y // self.CELL_SIZE
                    grid[y][x] = self.reversed_tiles[sprite.image]
                file.write("\n".join("".join(line) for line in grid))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.exit(app.exec())
