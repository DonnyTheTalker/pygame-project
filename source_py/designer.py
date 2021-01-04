import sys
import pygame
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QLabel, QLCDNumber, QButtonGroup
from PyQt5.QtWidgets import QCheckBox, QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import QtWidgets
from main import load_image, Tile


def slice_tiles(tiles_sheet, cell_size, columns, rows=1):
    image = load_image(tiles_sheet)
    rect = pygame.Rect(0, 0, image.get_width() // columns, image.get_height() // rows)
    tiles = list()  # список разрезанных тайлов
    j = 0
    for i in range(columns):
        frame_coords = (rect.w * i, rect.h * j)
        tiles.append(pygame.transform.scale(image.subsurface(pygame.Rect(frame_coords, rect.size)), cell_size))
    return tiles


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        pygame.init()
        # self.setupUi(self)
        uic.loadUi("../data/UI files/designer.ui", self)
        self.size = self.width, self.height = 16, 8
        self.CELL_SIZE = 32
        self.all_sprites = pygame.sprite.Group()
        self.names = ["g", "d", "u"]
        self.tiles = dict()  # словарь surface tile по его кодовому символу
        for i, tile_image in enumerate(slice_tiles("spritesheet1.png", (self.CELL_SIZE, self.CELL_SIZE), 3)):
            self.tiles[self.names[i]] = tile_image
        self.initUI()
        self.init_screen()
        self.timer.start(10)

    def initUI(self):
        self.resizeButton.clicked.connect(self.resize_window)
        self.saveButton.clicked.connect(self.save)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_events)
        self.tile_buttons = QButtonGroup(self)
        for i, tile_code in enumerate(self.tiles):
            button = QPushButton(tile_code, self)
            button.resize(self.CELL_SIZE, self.CELL_SIZE)
            # button.setIcon()
            button.move(20 + i * (self.CELL_SIZE + 10), 100)
            pixmap = QPixmap()
            pixmap.loadFromData(self.tiles[tile_code].get_buffer(), "PNG")
            button.setIcon(QIcon(pixmap))
            self.tile_buttons.addButton(button)
        self.tile_buttons.buttonClicked.connect(self.select_tile)
        self.tile_buttons.buttons()[0].click()

    def select_tile(self, button):
        self.current_tile = button.text()

    def init_screen(self):
        self.screen = pygame.display.set_mode((self.width * self.CELL_SIZE, self.height * self.CELL_SIZE))
        self.paint()

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
        self.all_sprites.draw(self.screen)
        color = pygame.Color("red")
        for i in range(1, self.width):
            pygame.draw.line(self.screen, color, (i * self.CELL_SIZE, 0),
                             (i * self.CELL_SIZE, self.height * self.CELL_SIZE), 1)
        for j in range(1, self.height):
            pygame.draw.line(self.screen, color, (0, j * self.CELL_SIZE),
                             (self.width * self.CELL_SIZE, j * self.CELL_SIZE), 1)
        pygame.display.flip()

    def add_sprite(self, pos):
        self.del_sprite(pos)
        x, y = pos
        x = x // self.CELL_SIZE * self.CELL_SIZE
        y = y // self.CELL_SIZE * self.CELL_SIZE
        Tile(self.tiles[self.current_tile], x, y, self.all_sprites)

    def del_sprite(self, pos):
        x, y = pos
        for sprite in self.all_sprites.sprites():
            if sprite.rect.collidepoint(x, y):
                sprite.kill()

    def resize_window(self):
        width, height = self.widthBox.value(), self.heightBox.value()
        self.size = self.width, self.height = width, height
        self.init_screen()
        for sprite in self.all_sprites.sprites():
            if sprite.rect.right > self.width * self.CELL_SIZE or sprite.rect.bottom > self.height * self.CELL_SIZE:
                sprite.kill()
        self.paint()

    def save(self):
        print(f'Засейвил "{self.nameEdit.text()}"')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.exit(app.exec())
