import sys
import pygame
import os
import json
from functools import partial
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QPushButton, QButtonGroup
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from source_py.main import load_image, Tile, Level, MainEncoder, main_decoder
from source_py.main import MovingEnemy, Saw, RotatingSaw, HATSaw, HATEnemy, ShootingEnemy, Obstacle

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


def load_icon(name):
    return QIcon(f"../data/images/{name}")


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
        self.mark_group = [self.damage_active, self.speed_active,
                           self.points_active, self.chainlen_active,
                           self.direction_active, self.sides_active, self.bulletspeed_active,
                           self.smart_active]
        self.idle_marks = [0]
        self.shooting_marks = [0, 5, 6, 7]
        self.rotating_marks = [0, 1, 3, 4]
        self.moving_marks = [0, 1, 2]
        self.hat_marks = [0, 1]
        self.parameters = []
        self.sides = []
        self.points = []
        self.enemy_class = "Obstacles"
        self.bullet_image = "bullet.png"
        self.enemies_spritesheets = {"Obstacle": ["cats.png", "fire.png", "boshy.png"],
                                     "MovingEnemy": ["spike1.png", "flying_dragon.png"],
                                     "ShootingEnemy": [["elf.png", "bullet.png"],
                                                       ["spritesheet1.png", "bullet.png"]],
                                     "HATEnemy": ["cats.png", "krot.png"],
                                     "HATSaw": ["white_cat.png", "white_cat.png"],
                                     "RotatingSaw": ["white_cat.png", "white_cat.png"],
                                     "Saw": ["cats.png", "bag.png"],
                                     }
        self.obstacles_images = ["spike.png", "mini_spikes_image.png", "spike.png"]
        self.shooting_images = ["plant.png", "dragon_image.png"]
        self.hat_enemy_images = ["cat_image.png", "bag_image"]
        self.hat_saw_images = ["cat_image.png", "bag_image"]
        self.default_saw_images = ["player.png", "cat_image.png"]
        self.rotating_saw_images = ["player.png", "cat_image.png"]
        self.moving_images = ["twin_dragon_image.png", "dragon_image.png"]
        self.current_enemy = ""
        # self.shooting_marks = []
        self.initUI()
        self.resize_window()
        self.timer.start(10)

    def initUI(self):
        y_offset = self.height()
        self.resizeButton.clicked.connect(self.resize_window)
        self.arrows.buttonClicked.connect(self.move_surface)
        self.layerButtons.addButton(self.enemy_button)
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
        self.accept_button.clicked.connect(self.accept_points)
        self.init_enemy_buttons(self.obstacles, "Obstacle", self.obstacles_images,
                                self.create_obstacle, self.idle_marks)
        self.init_enemy_buttons(self.default_saw_group, "Saw", self.default_saw_images,
                                self.create_obstacle, self.idle_marks)
        self.init_enemy_buttons(self.shooting_group, "ShootingEnemy", self.shooting_images,
                                self.create_shooting_enemy, self.shooting_marks)
        self.init_enemy_buttons(self.rotating_group, "RotatingSaw", self.rotating_saw_images,
                                self.create_obstacle, self.rotating_marks)
        self.init_enemy_buttons(self.hat_enemy_group, "HATEnemy", self.hat_enemy_images,
                                self.create_obstacle, self.hat_marks)
        self.init_enemy_buttons(self.hat_saw_group, "HATSaw", self.hat_saw_images,
                                self.create_obstacle, self.hat_marks)
        self.init_enemy_buttons(self.moving_enemy_group, "MovingEnemy", self.moving_images,
                                self.create_moving_enemy, self.moving_marks)
        #self.init_enemy_buttons(self.shooting_group, "ShootingEnemy", "shooting_images",
        #                        "create_shooting_enemy")

    def correct_points(self, pos):
        pos = [pos[0] // self.level.CELL_SIZE, pos[1] // self.level.CELL_SIZE]
        if pos[0] >= self.level.grid_width:
            return False
        if self.points:
            print(self.points, pos)
            return pos[0] == self.points[-1][0] or pos[1] == self.points[-1][1]
        return True

    def get_point(self, pos):
        return [pos[0] // self.level.CELL_SIZE, pos[1] // self.level.CELL_SIZE]

    def accept_points(self):
        if self.points:
            self.push_moving_enemy()
            self.points = []
        else:
            print("Вы не назначили точки!")

    def hide_makrs(self):
        for mark in self.mark_group:
            mark.hide()

    def create_obstacle(self, name, marks):
        sender = self.sender()
        self.hide_makrs()
        for i in marks:
            self.mark_group[i].show()
        self.parameters = []
        self.enemy_class = name
        self.current_enemy = self.enemies_spritesheets[name][int(sender.text())]

    def create_shooting_enemy(self, name, marks):
        sender = self.sender()
        self.hide_makrs()
        for i in marks:
            self.mark_group[i].show()
        self.parameters = []
        self.sides = []
        self.enemy_class = name
        self.current_enemy = self.enemies_spritesheets[name][int(sender.text())][0]
        self.bullet_image = self.enemies_spritesheets[name][int(sender.text())][1]

    def create_moving_enemy(self, name, marks):
        sender = self.sender()
        self.hide_makrs()
        for i in marks:
            self.mark_group[i].show()
        self.parameters = []
        self.points = []
        self.enemy_class = name
        self.current_enemy = self.enemies_spritesheets[name][int(sender.text())]

    def push_moving_enemy(self):
        pos = self.points[0]
        self.parameters = [f"damage={self.DamageSpinBox.value()}",
                           f"x={pos[0] * self.level.CELL_SIZE}",
                           f"y={pos[1] * self.level.CELL_SIZE}",
                           f"spritesheet='{self.current_enemy}'",
                           f"speed={self.SpeedSpinBox.value()}",
                           f"points={self.points}"]
        self.add_sprite(pos)

    def push_rotating_saw(self, pos):
        self.parameters = [f"damage={self.DamageSpinBox.value()}",
                           f"x={pos[0] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"y={pos[1] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"spritesheet='{self.current_enemy}'",
                           f"length={self.ChainSpinBox.value()}",
                           f"direction={self.DirectionSpinBox.value()}",
                           f"speed={self.SpeedSpinBox.value()}"]
        self.add_sprite(pos)

    def push_hat_enemy(self, pos):
        print(pos[0] // self.level.CELL_SIZE * self.level.CELL_SIZE)
        self.parameters = [f"damage={self.DamageSpinBox.value()}",
                           f"x={pos[0] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"y={pos[1] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"spritesheet='{self.current_enemy}'",
                           f"speed={self.SpeedSpinBox.value()}"]
        self.add_sprite(pos)

    def push_obstacle(self, pos):
        print(pos[0] // self.level.CELL_SIZE * self.level.CELL_SIZE)
        self.parameters = [f"damage={self.DamageSpinBox.value()}",
                           f"x={pos[0] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"y={pos[1] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"spritesheet='{self.current_enemy}'"]
        self.add_sprite(pos)

    def push_shooting_enemy(self, pos):
        self.parameters = [f"damage={self.DamageSpinBox.value()}",
                           f"x={pos[0] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"y={pos[1] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"spritesheet='{self.current_enemy}'",
                           f"bullet_speed={self.BulletSpinBox.value()}",
                           f"bullet_image='{self.bullet_image}'"]
        if self.smartradioButton.isChecked():
            self.parameters.append("smart=True")
        else:
            for button in self.sides_group.buttons():
                if button.isChecked():
                    self.push_side(button.text())
            self.parameters.append(f"all_sides=[{', '.join(self.sides)}]")
            self.parameters.append("smart=False")
        self.add_sprite(pos)

    def push_side(self, number):
        if number not in self.sides:
            self.sides.append(number)

    def init_enemy_buttons(self, group, name, images, function, marks):
        i = 0
        for button in group.buttons():
            button.setText(f"{i}")
            button.setIcon(load_icon(images[i]))
            button.clicked.connect(partial(function, name, marks))
            i += 1

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
            if self.layer == self.level.enemy_group:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 or event.button == 4:
                        if self.enemy_class == "Obstacle" or self.enemy_class == "Saw":
                            self.push_obstacle(event.pos)
                            print(event.pos)
                        elif self.enemy_class == "ShootingEnemy":
                            self.push_shooting_enemy(event.pos)
                        elif self.enemy_class == "RotatingSaw":
                            self.push_rotating_saw(event.pos)
                        elif self.enemy_class == "HATEnemy" or self.enemy_class == "HATSaw":
                            self.push_hat_enemy(event.pos)
                        elif self.enemy_class == "MovingEnemy":
                            if self.correct_points(event.pos):
                                print(self.points)
                                self.points.append(self.get_point(event.pos))
                    elif event.button == 3 or event.button == 5:
                        self.push_obstacle(event.pos)
            else:
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
            for point in self.points:
                pygame.draw.line(self.screen, (0, 0, 255),
                                 (point[0] * self.level.CELL_SIZE + 3,
                                  point[1] * self.level.CELL_SIZE + 3),
                                 (point[0] * self.level.CELL_SIZE + self.level.CELL_SIZE - 6,
                                  point[1] * self.level.CELL_SIZE + self.level.CELL_SIZE - 4), 2)
                pygame.draw.line(self.screen, (0, 0, 255),
                                 (point[0] * self.level.CELL_SIZE + 3,
                                  point[1] * self.level.CELL_SIZE + self.level.CELL_SIZE - 4),
                                 (point[0] * self.level.CELL_SIZE + self.level.CELL_SIZE - 6,
                                  point[1] * self.level.CELL_SIZE + 3), 2)
        pygame.display.flip()

    def add_sprite(self, pos):
        x, y = pos
        x = x // self.level.CELL_SIZE * self.level.CELL_SIZE
        y = y // self.level.CELL_SIZE * self.level.CELL_SIZE
        if x // self.level.CELL_SIZE >= self.level.grid_width:
            return
        self.del_sprite(pos)
        if self.layer == self.level.enemy_group:
            self.parameters.append("groups=[self.level.all_sprites, self.level.enemy_group]")
            enemy = f"{self.enemy_class}({', '.join(self.parameters)})"
            print(enemy)
            exec(enemy)
        else:
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
