from typing import List, Any, Union
import pygame
import os
import sys
import time
import json
import inspect
from copy import deepcopy
from math import sin, cos
from functools import partial
from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QPushButton, QButtonGroup
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PIL import Image, ImageQt

os.environ['SDL_VIDEO_WINDOW_POS'] = '0,30'
pygame.init()
screen = pygame.display.set_mode((1, 1))

TILE_WIDTH = TILE_HEIGHT = 24
GAME_NAME = "Первый научный платформер"

FPS = 60
EAST = 0
SE = 1
SOUTH = 2
SW = 3
WEST = 4
NW = 5
NORTH = 6
NE = 7
SHOOTING_SIDES = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]]
SHOOT_AROUND = [i for i in range(8)]
SHOOT_FOUR_SIDES = [0, 2, 4, 6]
SHOOT_FOUR_SIDES_45 = [1, 3, 5, 7]
FRAME = 0
MAX_BULLET_SPEED = 5
LAST_HIT_TIME = 0


def load_icon(name):
    return QIcon(f"../data/images/{name}")


class Designer(QMainWindow):
    current_tile: str

    def __init__(self, parent=None):
        super().__init__(parent)
        pygame.init()
        self.screen = pygame.display.set_mode((1, 1))
        # self.setupUi(self)
        uic.loadUi("../data/UI files/designer.ui", self)
        self.names = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # кодовые символы
        self.timer = QTimer(self)
        self.tile_buttons = QButtonGroup(self)
        self.button_coords = dict()
        self.holding = None
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
        self.enemies_spritesheets = {"Obstacle": ["spike1.png", "fire1.png", "kust3.png"],
                                     "MovingEnemy": ["bag.png", "flying_dragon1.png"],
                                     "ShootingEnemy": [["black_hole.png", "bullet.png"],
                                                       ["black_hole2.png", "bat2.png"]],
                                     "HATEnemy": ["big_cats.png", "skeleton.png"],
                                     "HATSaw": ["hat_saw.png", "hat_saw2.png"],
                                     "RotatingSaw": ["saw.png", "saw2.png"],
                                     "Saw": ["saw.png", "saw2.png"],
                                     }
        self.obstacles_images = ["spike.png", "fire_image.png", "kust_image.png"]
        self.shooting_images = ["black_hole_image.png", "black_hole_2_image.png"]
        self.hat_enemy_images = ["big_cat_image.png", "skeleton_image.png"]
        self.hat_saw_images = ["saw_image.png", "saw2_image.png"]
        self.default_saw_images = ["saw_image.png", "saw2_image.png"]
        self.rotating_saw_images = ["saw_image.png", "saw2_image.png"]
        self.moving_images = ["bag_image.png", "dragon_image.png"]
        self.current_enemy = ""
        self.level = Level()
        self.initUI()
        self.get_size()
        self.timer.start(10)
        self.tiles_button.click()

    def initUI(self):
        self.setWindowTitle("Дизайнер уровней")
        self.setGeometry(1200, 200, self.width(), self.height())
        y_offset = self.height()
        self.resizeButton.clicked.connect(self.get_size)
        self.arrows.buttonClicked.connect(self.move_surface)
        self.layerButtons.addButton(self.enemy_button)
        self.layerButtons.buttonClicked.connect(self.change_layer)
        self.timer.timeout.connect(self.check_events)
        self.actionopen.triggered.connect(self.open)
        self.actionsave.triggered.connect(self.save)
        self.playerButtons.buttonClicked.connect(self.select_tile)
        self.clear_points.clicked.connect(self.clear_all_points)
        self.tile_buttons.buttonClicked.connect(self.select_tile)
        self.accept_button.clicked.connect(self.accept_points)
        self.hide_marks()
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
        self.generate_tiles_buttons()

    def generate_tiles_buttons(self):
        y_offset = self.height()
        between_offset = 5
        button_size = self.level.CELL_SIZE + between_offset
        for button in self.tile_buttons.buttons():
            y_offset = min(y_offset, button.y())
            button.close()
        self.button_coords.clear()
        spritesheet_image = Image.open(f"../data/images/{self.level.spritesheet}")
        spritesheet_image = spritesheet_image.resize((self.level.spritesheet_width *
                                                      self.level.CELL_SIZE,
                                                      self.level.spritesheet_height *
                                                      self.level.CELL_SIZE))
        for row in range(self.level.spritesheet_height):
            for column in range(self.level.spritesheet_width):
                button = QPushButton(self)
                self.button_coords[button] = (row, column)
                button.resize(self.level.CELL_SIZE, self.level.CELL_SIZE)
                button.move(20 + column * button_size,
                            y_offset + row * button_size)
                left, up = self.level.CELL_SIZE * column, self.level.CELL_SIZE * row
                button_image = ImageQt.ImageQt(spritesheet_image.crop((left, up,
                                                                       left + self.level.CELL_SIZE,
                                                                       up + self.level.CELL_SIZE)))
                button.setIcon(QIcon(QPixmap.fromImage(button_image)))
                self.tile_buttons.addButton(button)
        self.setFixedSize(max(self.width(), self.level.spritesheet_width * button_size),
                          y_offset + self.level.spritesheet_height * button_size)
        self.tile_buttons.buttons()[0].click()

    def correct_points(self, pos):
        pos = [pos[0] // self.level.CELL_SIZE, pos[1] // self.level.CELL_SIZE]
        if pos[0] >= self.level.grid_width:
            return False
        if self.points:
            return pos[0] == self.points[-1][0] or pos[1] == self.points[-1][1]
        return True

    def get_point(self, pos):
        return [pos[0] // self.level.CELL_SIZE, pos[1] // self.level.CELL_SIZE]

    def print_points(self):
        print(self.points)

    def clear_all_points(self):
        self.points.clear()

    def accept_points(self):
        if len(self.points) >= 2:
            self.push_moving_enemy()
            self.points = []
        else:
            print("Надо назначить 2 и более точек")

    def hide_marks(self):
        for mark in self.mark_group:
            mark.hide()

    def set_state(self, group, val):
        enemy_buttons_groups = [self.obstacles.buttons(), self.default_saw_group.buttons(),
                                self.shooting_group.buttons(), self.hat_enemy_group.buttons(),
                                self.rotating_group.buttons(), self.hat_saw_group.buttons(),
                                self.moving_enemy_group.buttons(), self.control_buttons.buttons(),
                                self.sides_group.buttons(),
                                [self.DamageSpinBox, self.SpeedSpinBox, self.ChainSpinBox,
                                 self.DirectionSpinBox, self.BulletSpinBox, self.smartradioButton]]
        tiles_buttons_groups = [self.playerButtons.buttons()]
        alltiles_buttons_groups = ([self.arrows.buttons(), self.tile_buttons.buttons()] +
                                   tiles_buttons_groups)
        for buttons_group in (alltiles_buttons_groups if group == 'alltiles' else
        (tiles_buttons_groups if group == "tiles" else enemy_buttons_groups)):
            for button in buttons_group:
                button.setEnabled(val)

    def create_obstacle(self, name, marks):
        sender = self.sender()
        self.hide_marks()
        self.points = []
        for i in marks:
            self.mark_group[i].show()
        self.parameters = []
        self.enemy_class = name
        self.current_enemy = self.enemies_spritesheets[name][int(sender.text())]

    def create_shooting_enemy(self, name, marks):
        sender = self.sender()
        self.hide_marks()
        self.points = []
        for i in marks:
            self.mark_group[i].show()
        self.parameters = []
        self.sides = []
        self.enemy_class = name
        self.current_enemy = self.enemies_spritesheets[name][int(sender.text())][0]
        self.bullet_image = self.enemies_spritesheets[name][int(sender.text())][1]

    def create_moving_enemy(self, name, marks):
        sender = self.sender()
        self.hide_marks()
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
        self.parameters = [f"damage={self.DamageSpinBox.value()}",
                           f"x={pos[0] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"y={pos[1] // self.level.CELL_SIZE * self.level.CELL_SIZE}",
                           f"spritesheet='{self.current_enemy}'",
                           f"speed={self.SpeedSpinBox.value()}"]
        self.add_sprite(pos)

    def push_obstacle(self, pos):
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

    @staticmethod
    def init_enemy_buttons(group, name, images, function, marks):
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

    def get_size(self):
        width, height = self.widthBox.value(), self.heightBox.value()
        self.level.grid_size = self.level.grid_width, self.level.grid_height = width, height
        self.resize_window()

    def resize_window(self):
        self.init_screen()
        self.delete_abroad()
        self.paint()

    def change_layer(self, button):
        if button.text() == "enemy":
            self.set_state("enemy", True)
            self.set_state("alltiles", False)
        elif button.text() == 'tiles':
            self.set_state("enemy", False)
            self.set_state("alltiles", True)
        else:
            self.set_state("enemy", False)
            self.set_state("alltiles", True)
            self.set_state("tiles", False)
        query = f'self.layer = self.level.{button.text()}_group'
        exec(query)

    def select_tile(self, button):
        if button.text():
            self.current_tile = button.text()
        else:
            self.current_tile = self.button_coords[button]

    def get_tile_image(self):
        if self.current_tile == "Start":
            return Flag.image
        if self.current_tile == "Finish":
            return Scroll.image
        return self.level.rnavigate[self.current_tile]

    def move_surface(self, key):
        encode = {"↑": (0, -1), "→": (1, 0), "↓": (0, 1), "←": (-1, 0)}
        dx, dy = encode[key.text()]
        for sprite in self.layer.sprites():
            sprite.rect = sprite.rect.move(dx * self.level.CELL_SIZE, dy * self.level.CELL_SIZE)
        self.delete_abroad()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return
            if event.type == pygame.MOUSEBUTTONUP:
                self.holding = None
            if self.layer == self.level.enemy_group:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.enemy_class == "Obstacle" or self.enemy_class == "Saw":
                            self.push_obstacle(event.pos)
                        elif self.enemy_class == "ShootingEnemy":
                            self.push_shooting_enemy(event.pos)
                        elif self.enemy_class == "RotatingSaw":
                            self.push_rotating_saw(event.pos)
                        elif self.enemy_class == "HATEnemy" or self.enemy_class == "HATSaw":
                            self.push_hat_enemy(event.pos)
                        elif self.enemy_class == "MovingEnemy":
                            if self.correct_points(event.pos):
                                self.points.append(self.get_point(event.pos))
                    elif event.button == 3:
                        self.del_sprite(event.pos)
            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.holding = event.button
                    if self.holding == 1:
                        self.add_sprite(event.pos)
                    elif self.holding == 3:
                        self.del_sprite(event.pos)
                if event.type == pygame.MOUSEMOTION and not (self.holding is None):
                    if self.holding == 1:
                        self.add_sprite(event.pos)
                    elif self.holding == 3:
                        self.del_sprite(event.pos)
        self.paint()

    def paint(self):
        self.screen.fill(pygame.Color("white"))
        if self.displayMode.isChecked():
            # for sprite in self.level.all_sprites.sprites():
            # pygame.draw.rect(self.screen, "red", sprite.rect)
            self.level.draw(self.screen)
            if self.level.start:
                self.screen.blit(Flag.image, (self.level.start.rect.x, self.level.start.rect.y))
        else:
            self.layer.draw(self.screen)
        self.screen.blit(self.get_tile_image(),
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
            exec(enemy)
            pygame.sprite.spritecollide(self.level.enemy_group.sprites()[-1],
                                        self.level.tiles_group, True)
        else:
            if self.current_tile == "Start":
                if self.layer == self.level.tiles_group:
                    if (x + Flag.image.get_width() >
                            self.level.grid_width * self.level.CELL_SIZE or
                            y + Flag.image.get_height() >
                            self.level.grid_height * self.level.CELL_SIZE):
                        return
                    if self.level.start:
                        self.level.start.kill()
                        self.level.start = None
                    self.level.start = Flag(x, y, self.level.all_sprites)
                    pygame.sprite.spritecollide(self.level.start, self.level.tiles_group, True)
            elif self.current_tile == "Finish":
                if self.layer == self.level.tiles_group:
                    if (x + Scroll.image.get_width() >
                            self.level.grid_width * self.level.CELL_SIZE or
                            y + Scroll.image.get_height() >
                            self.level.grid_height * self.level.CELL_SIZE):
                        return
                    if self.level.finish:
                        self.level.finish.kill()
                        self.level.finish = None
                    self.level.finish = Scroll(x, y, self.level.all_sprites)
                    pygame.sprite.spritecollide(self.level.finish, self.level.tiles_group, True)
            else:
                Tile(self.get_tile_image(), x, y, self.current_tile,
                     self.level.all_sprites, self.layer)

    def del_sprite(self, pos):
        x, y = pos
        x = x // self.level.CELL_SIZE * self.level.CELL_SIZE
        y = y // self.level.CELL_SIZE * self.level.CELL_SIZE
        for sprite in self.layer.sprites():
            if sprite.rect.collidepoint(pos[0], pos[1]):
                sprite.kill()
        if self.layer == self.level.tiles_group:
            if self.level.start and self.level.start.rect.collidepoint(x, y):
                self.level.start.kill()
                self.level.start = None
            if self.level.finish and self.level.finish.rect.collidepoint(x, y):
                self.level.finish.kill()
                self.level.finish = None

    def delete_abroad(self):
        if (self.level.start and
                not ((self.level.start.rect.left >= 0 and
                      self.level.start.rect.right <=
                      self.level.grid_width * self.level.CELL_SIZE) and
                     (self.level.start.rect.top >= 0 and
                      self.level.start.rect.bottom <=
                      self.level.grid_height * self.level.CELL_SIZE))):
            self.level.start.kill()
            self.level.start = None
        if (self.level.finish and
                not ((self.level.finish.rect.left >= 0 and
                      self.level.finish.rect.right <=
                      self.level.grid_width * self.level.CELL_SIZE) and
                     (self.level.finish.rect.top >= 0 and
                      self.level.finish.rect.bottom <=
                      self.level.grid_height * self.level.CELL_SIZE))):
            self.level.finish.kill()
            self.level.finish = None
        for sprite in self.level.all_sprites.sprites():
            if not ((sprite.rect.left >= 0 and
                     sprite.rect.right <= self.level.grid_width * self.level.CELL_SIZE) and
                    (sprite.rect.top >= 0 and
                     sprite.rect.bottom <= self.level.grid_height * self.level.CELL_SIZE)):
                sprite.kill()

    def save(self):
        name = self.nameEdit.text()
        if not name:
            print("Ошибка ввода имени")
            return
        if not (self.level.start and self.level.finish):
            self.statusBar().showMessage("Не выбраны точки старта и финиша")
            return
        self.statusBar().hide()
        with open(f'../data/custom_levels/{name}.json', 'w', encoding='utf-8') as file:
            json.dump(self.level, file, cls=MainEncoder)

    def open(self):
        path = QFileDialog.getOpenFileName(self, 'Выбрать уровень', '')[0]
        if not path:
            print("Ошибка выбора файла")
            return
        with open(path, 'r', encoding='utf-8') as file:
            self.level = json.load(file, object_hook=main_decoder)
        self.tiles_button.click()
        self.resize_window()
        self.nameEdit.setText(path.split('/')[-1].split('.')[0])
        self.widthBox.setValue(self.level.grid_width)
        self.heightBox.setValue(self.level.grid_height)

    def closeEvent(self, event):
        self.timer.stop()
        pygame.quit()
        if self.parent():
            self.parent().show()
        super().closeEvent(event)


class Selecter(QMainWindow):
    def __init__(self, dir="custom_levels", parent=None):
        super().__init__(parent)
        self.path = f"../data/{dir}/"
        # self.setupUi(self)
        uic.loadUi("../data/UI files/selecter.ui", self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Выбор уровня")
        self.levels_list.itemDoubleClicked.connect(self.select_level)
        self.levels_list.addItems(map(lambda name: name.split(".")[0],
                                      os.listdir(self.path)))

    def select_level(self, item):
        self.hide()
        self.parent().load_level(self.path + item.text())
        self.close()

    def closeEvent(self, event):
        if self.parent():
            self.parent().show()
        super().closeEvent(event)


# Меню настройки приложения
# Используется большинством окон
def setup_frame(widget, main_frame):
    # Убираем фон и заглавие окна
    widget.setWindowFlag(QtCore.Qt.FramelessWindowHint)
    widget.setAttribute(QtCore.Qt.WA_TranslucentBackground)

    # Настраиваем тень от окна - для красоты
    widget.shadow = QGraphicsDropShadowEffect(widget)
    widget.shadow.setBlurRadius(30)
    widget.shadow.setXOffset(0)
    widget.shadow.setYOffset(0)
    widget.shadow.setColor(QColor(0, 0, 0, 60))
    main_frame.setGraphicsEffect(widget.shadow)


class MenuUI(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 760)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.main_frame = QtWidgets.QFrame(self.centralwidget)
        self.main_frame.setStyleSheet("QFrame \n"
                                      "{\n"
                                      "    background-color: rgb(49, 52, 117); \n"
                                      "    color: rbg(220, 220, 220); \n"
                                      "    border-radius: 20px;\n"
                                      "}")
        self.main_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.main_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.main_frame.setObjectName("main_frame")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.main_frame)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(180, 180, 631, 561))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.startButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(32)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(75)
        font.setStrikeOut(False)
        font.setKerning(True)
        self.startButton.setFont(font)
        self.startButton.setStyleSheet("QPushButton{ \n"
                                       "    border-radius: 10;\n"
                                       "    border: 4px solid rgb(238, 217, 94);\n"
                                       "    color: rgb(238, 214, 115);\n"
                                       "    background-color: rgb(41, 35, 117)\n"
                                       "}\n"
                                       "\n"
                                       "QPushButton::pressed\n"
                                       "{\n"
                                       "    color: black;\n"
                                       "    background-color: rgb(238, 214, 115)\n"
                                       "}")
        self.startButton.setObjectName("startButton")
        self.verticalLayout_2.addWidget(self.startButton)
        self.loadButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(32)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(75)
        font.setStrikeOut(False)
        font.setKerning(True)
        self.loadButton.setFont(font)
        self.loadButton.setStyleSheet("QPushButton{ \n"
                                      "    border-radius: 10;\n"
                                      "    border: 4px solid rgb(238, 217, 94);\n"
                                      "    color: rgb(238, 214, 115);\n"
                                      "    background-color: rgb(41, 35, 117)\n"
                                      "}\n"
                                      "\n"
                                      "QPushButton::pressed\n"
                                      "{\n"
                                      "    color: black;\n"
                                      "    background-color: rgb(238, 214, 115)\n"
                                      "}")
        self.loadButton.setObjectName("loadButton")
        self.verticalLayout_2.addWidget(self.loadButton)
        self.createButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(32)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(75)
        font.setStrikeOut(False)
        font.setKerning(True)
        self.createButton.setFont(font)
        self.createButton.setStyleSheet("QPushButton{ \n"
                                        "    border-radius: 10;\n"
                                        "    border: 4px solid rgb(238, 217, 94);\n"
                                        "    color: rgb(238, 214, 115);\n"
                                        "    background-color: rgb(41, 35, 117)\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton::pressed\n"
                                        "{\n"
                                        "    color: black;\n"
                                        "    background-color: rgb(238, 214, 115)\n"
                                        "}")
        self.createButton.setObjectName("createButton")
        self.verticalLayout_2.addWidget(self.createButton)
        self.exitButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(32)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(75)
        font.setStrikeOut(False)
        font.setKerning(True)
        self.exitButton.setFont(font)
        self.exitButton.setStyleSheet("QPushButton{ \n"
                                      "    border-radius: 10;\n"
                                      "    border: 4px solid rgb(238, 217, 94);\n"
                                      "    color: rgb(238, 214, 115);\n"
                                      "    background-color: rgb(41, 35, 117)\n"
                                      "}\n"
                                      "\n"
                                      "QPushButton::pressed\n"
                                      "{\n"
                                      "    color: black;\n"
                                      "    background-color: rgb(238, 214, 115)\n"
                                      "}")
        self.exitButton.setObjectName("exitButton")
        self.verticalLayout_2.addWidget(self.exitButton)
        self.gameTitleLabel = QtWidgets.QLabel(self.main_frame)
        self.gameTitleLabel.setGeometry(QtCore.QRect(20, 50, 941, 61))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(32)
        font.setBold(True)
        font.setWeight(75)
        self.gameTitleLabel.setFont(font)
        self.gameTitleLabel.setStyleSheet("border: 0px;\n"
                                          "color: rgb(238, 214, 115)")
        self.gameTitleLabel.setTextFormat(QtCore.Qt.AutoText)
        self.gameTitleLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.gameTitleLabel.setObjectName("gameTitleLabel")
        self.verticalLayout.addWidget(self.main_frame)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.startButton.setText(_translate("MainWindow", "Начать Игру"))
        self.loadButton.setText(_translate("MainWindow", "Загрузить Уровень"))
        self.createButton.setText(_translate("MainWindow", "Создать Уровень"))
        self.exitButton.setText(_translate("MainWindow", "Выйти"))
        self.gameTitleLabel.setText(_translate("MainWindow", "Первый Научный Платформер"))


class Menu(QMainWindow, MenuUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()

    def initUI(self):
        setup_frame(self, self.main_frame)
        self.setWindowTitle(GAME_NAME)
        self.startButton.clicked.connect(partial(self.select_level, "story_levels"))
        self.loadButton.clicked.connect(partial(self.select_level, "custom_levels"))
        self.createButton.clicked.connect(self.start_creating)
        self.exitButton.clicked.connect(self.close)

    def start_creating(self):
        designer = Designer(self)
        designer.show()
        self.hide()

    def select_level(self, dir="custom_levels"):
        selecter = Selecter(dir, self)
        selecter.show()
        self.hide()

    @staticmethod
    def load_level(path):
        global FRAME
        pygame.init()
        screen = pygame.display.set_mode((1, 1))
        background_sound = "../data/sounds/background.mp3"
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.music.load(background_sound)
        pygame.mixer.music.set_volume(50)
        pygame.mixer.music.play(-1)
        path += '.json'
        with open(path, 'r', encoding='utf-8') as file:
            level = json.load(file, object_hook=main_decoder)
            level.spawn_player()
        screen = pygame.display.set_mode((level.grid_width * TILE_WIDTH,
                                          level.grid_height * TILE_HEIGHT))
        pygame.display.set_caption(GAME_NAME)
        clock = pygame.time.Clock()
        running = True
        delay = clock.tick(FPS)
        while running:
            for cur_event in pygame.event.get():
                if cur_event.type == pygame.QUIT:
                    running = False
                if cur_event.type == pygame.KEYDOWN or cur_event.type == pygame.KEYUP:
                    level.event_handling(cur_event)
            level.update()
            level.check_enemies()
            screen.fill(pygame.Color("white"))
            level.draw(screen)
            delay = clock.tick(FPS)
            pygame.display.flip()
            if level.check_scroll():
                print("YOU WIN")
                running = False
            FRAME = (FRAME + 1) % MAX_BULLET_SPEED
        pygame.quit()


def terminate():
    pygame.quit()
    sys.exit()


def render_text(content, size, x, y):
    font = pygame.font.Font(MAIN_FONT, size)
    surface = font.render(content, True, FONT_COLOR)
    text = surface.get_rect()
    text.center = (x, y)
    screen.blit(surface, text)


def load_image(name, colorkey=None):
    # jpg, png, gif без анимации, bmp, pcx, tga, tif, lbm, pbm, xpm
    fullname = os.path.join("..", "data", "images", name)  # получение полного пути к файлу
    if not os.path.isfile(fullname):  # если файл не найден
        print(f"Файл с изображением {fullname} не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:  # пусть colorkey будет (0, 0) пикселем
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def cut_sheets(sheet, cell_size, columns, rows):
    sheet = load_image(sheet)
    rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
    frames = list()
    navigate = dict()  # ключ - Surface, значение - положение на spritesheet
    rnavigate = dict()  # обратный словарь
    for j in range(rows):
        for i in range(columns):
            frame_coords = rect.w * i, rect.h * j
            frames.append(pygame.transform.scale(sheet.subsurface(pygame.Rect(frame_coords,
                                                                              rect.size)),
                                                 (cell_size, cell_size)))
            navigate[frames[-1]] = (j, i)
            rnavigate[(j, i)] = frames[-1]
    return navigate, rnavigate


def real_coords(coord, x=False, y=False):
    if x and y:
        return coord * TILE_WIDTH, coord * TILE_HEIGHT
    else:
        if x:
            return coord * TILE_WIDTH
        if y:
            return coord * TILE_HEIGHT


def update_addition_center(unit):
    addition_y = (unit.rect.centery // TILE_HEIGHT * TILE_HEIGHT +
                  TILE_HEIGHT // 2 - unit.rect.centery)
    addition_x = (unit.rect.centerx // TILE_WIDTH * TILE_WIDTH +
                  TILE_WIDTH // 2 - unit.rect.centerx)
    return addition_x, addition_y


def update_addition_all(width, height):
    return TILE_WIDTH - width, TILE_HEIGHT - height


def main_decoder(dct):
    if "__Level__" in dct:
        new_level = Level()
        new_level.load_level(dct)
        return new_level
    if "__Obstacle__" in dct:
        return Obstacle(dct["x"], dct["y"], dct["damage"], dct["spritesheet"])
    if "__Saw__" in dct:
        return Saw(dct["x"], dct["y"], dct["damage"], dct["spritesheet"])
    if "__ShootingEnemy__" in dct:
        return ShootingEnemy(dct['x'], dct['y'], dct['damage'], dct['spritesheet'],
                             dct['bullet_image'], list(), bullet_speed=dct['bullet_speed'],
                             all_sides=dct['all_sides'], smart=dct['smart'])
    if "__RotatingSaw__" in dct:
        return RotatingSaw(dct['x'], dct['y'], dct['damage'], dct['length'], dct['spritesheet'],
                           list(), dct['speed'], dct['direction'])
    if "__HATEnemy__" in dct:
        return HATEnemy(dct['spritesheet'], dct['x'], dct['y'], dct['damage'],
                        dct['speed'], list())
    if "__HATSaw__" in dct:
        return HATSaw(dct['spritesheet'], dct['x'], dct['y'], dct['damage'], dct['speed'], list())
    if "__MovingEnemy__" in dct:
        return MovingEnemy(dct['x'], dct['y'], dct['damage'], dct['speed'], dct['points'],
                           dct['spritesheet'], list())
    if "__Flag__" in dct:
        return Flag(dct["x"], dct["y"])
    if "__Scroll__" in dct:
        return Scroll(dct["x"], dct["y"])
    else:
        return dct


class MainEncoder(json.JSONEncoder):
    def default(self, o):
        name = type(o).__name__
        if name == "Level":
            return {"__Level__": True, "grid_size": o.grid_size, "CELL_SIZE": o.CELL_SIZE,
                    "background_group": o.background_group.sprites(),
                    "tiles_group": o.tiles_group.sprites(),
                    "frontground_group": o.frontground_group.sprites(),
                    "enemy_group": o.enemy_group.sprites(),
                    "spritesheet": o.spritesheet,
                    "start": o.start,
                    "finish": o.finish}
        elif name == "Tile":
            return {"x": o.rect.x,
                    "y": o.rect.y,
                    "coords": o.coords}
        elif name == "Obstacle":
            return {"__Obstacle__": True,
                    "x": o.x,
                    "y": o.y,
                    "damage": o.damage,
                    "spritesheet": o.spritesheet}
        elif name == "Saw":
            return {"__Saw__": True,
                    "x": o.x,
                    "y": o.y,
                    "damage": o.damage,
                    "spritesheet": o.spritesheet}
        elif name == "ShootingEnemy":
            return {"__ShootingEnemy__": True,
                    "x": o.x,
                    "y": o.y,
                    "damage": o.damage,
                    "spritesheet": o.spritesheet,
                    "bullet_image": o.bullet_image,
                    "bullet_speed": o.bullet_speed,
                    "all_sides": o.all_sides,
                    "smart": o.smart}
        elif name == "RotatingSaw":
            return {"__RotatingSaw__": True,
                    "x": o.x,
                    "y": o.y,
                    "damage": o.damage,
                    "length": o.length,
                    "spritesheet": o.spritesheet,
                    "speed": o.speed,
                    "direction": o.direction}
        elif name == "HATEnemy":
            return {"__HATEnemy__": True,
                    "spritesheet": o.spritesheet,
                    "x": o.x,
                    "y": o.y,
                    "damage": o.damage,
                    "speed": o.speed}
        elif name == "HATSaw":
            return {"__HATSaw__": True,
                    "spritesheet": o.spritesheet,
                    "x": o.x,
                    "y": o.y,
                    "damage": o.damage,
                    "speed": o.speed}
        elif name == "MovingEnemy":
            return {"__MovingEnemy__": True,
                    "x": o.x,
                    "y": o.y,
                    "damage": o.damage,
                    "points": o.points,
                    "spritesheet": o.spritesheet}
        elif name == "Flag":
            return {"__Flag__": True,
                    "x": o.x,
                    "y": o.y}
        elif name == "Scroll":
            return {"__Flag__": True,
                    "x": o.x,
                    "y": o.y}
        else:
            json.JSONEncoder.default(self, o)


class SpriteStates:
    IDLE = "1idle"
    FALLING = "2falling"
    JUMPING = "3jumping"
    MOVING = "4moving right"
    SLIDING = "5sliding right"

    @staticmethod
    def get_states():
        attributes = inspect.getmembers(SpriteStates, lambda a: not (inspect.isroutine(a)))
        attributes = sorted([a[1] for a in attributes if (not (a[0].startswith('__') and
                                                               a[0].endswith('__')))])
        return attributes


class Collision:
    @staticmethod
    def get_collision(rect, obj_list):
        collision_detected = list()
        for obj in obj_list:
            if rect.colliderect(obj.rect):
                collision_detected.append(obj)
        return collision_detected


class Scroll(pygame.sprite.Sprite):
    image = load_image("scroll.png")

    def __init__(self, x, y, *groups):
        self.x = x
        self.y = y
        super().__init__(*groups)
        self.rect = self.image.get_rect().move(x, y)


class Flag(pygame.sprite.Sprite):
    image = load_image("start_flag.png")

    def __init__(self, x, y, *groups):
        self.x = x
        self.y = y
        super().__init__(*groups)
        self.rect = self.image.get_rect().move(x, y)


class Tile(pygame.sprite.Sprite):
    def __init__(self, image, x, y, coords, *groups):
        super().__init__(*groups)
        self.image = image
        self.coords = coords
        self.rect = self.image.get_rect().move(x, y)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, spritesheet, x, y, *groups):
        super().__init__(*groups)
        self.x = x
        self.y = y
        self.spritesheet = spritesheet
        self.direction = True
        self.status = None
        self.current_sprite = 0
        self.sprites = dict()
        # Создаем ассоциативный массив спрайтов
        # Для каждого состояния анимации
        for state in SpriteStates.get_states():
            self.sprites[state] = list()
        self.slice_sprites(load_image(spritesheet))
        self.width = max(max([cur_sprite.get_width() for cur_sprite in self.sprites[state]] +
                             [0])
                         for state in self.sprites) + 2
        self.height = max(max([cur_sprite.get_height() for cur_sprite in self.sprites[state]] +
                              [0])
                          for state in self.sprites)
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.rect.width, self.rect.height = self.width, self.height
        self.set_status(SpriteStates.IDLE)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, *args):
        # Добавить контроль длительности анимации
        self.current_sprite = (self.current_sprite + 1) % len(self.sprites[self.status])
        self.update_sprite()

    def set_status(self, status, direction=True):
        """Смена режима анимации"""
        if status != self.status or direction != self.direction:
            self.status = status
            self.direction = direction
            self.current_sprite = 0
            # self.width = max(max([sprite.get_width() for sprite in self.sprites[self.status]] +
            #                      [0]), 0)
            self.update_sprite()

    def update_sprite(self):
        """Изменение текущего спрайта"""
        self.image = self.sprites[self.status][self.current_sprite]
        self.image = pygame.transform.flip(self.image, not self.direction, False)
        surface = pygame.Surface((self.rect.width, self.rect.height))
        surface.fill((255, 255, 255, 0))
        surface.set_colorkey((255, 255, 255))
        if self.status in [SpriteStates.SLIDING, SpriteStates.MOVING] or True:
            surface.blit(self.image,
                         (self.rect.width - self.image.get_width()
                          if ((self.direction and self.status != SpriteStates.SLIDING) or
                              (not self.direction and self.status == SpriteStates.SLIDING))
                          else 0,
                          self.height - self.image.get_height()))
        elif self.status == SpriteStates.MOVING:
            surface.blit(self.image,
                         (self.rect.width - self.width if self.direction
                          else 0,
                          self.height - self.image.get_height()))
        else:
            surface.blit(self.image,
                         ((self.rect.width - self.width) // 2,
                          self.height - self.image.get_height()))
        self.image = surface
        self.mask = pygame.mask.from_surface(self.image)

    def slice_sprites(self, spritesheet):
        """Генерирует сетку спрайтов, найденных в spritesheet"""
        sprites = list()  # Сетка обрезанных спрайтов
        top, bottom = None, None
        cur_row = -1
        for y in range(spritesheet.get_height()):
            empty_row = not any(spritesheet.get_at((x, y))[3] > 0
                                for x in range(spritesheet.get_width()))
            if empty_row and top:
                bottom = y - 1
                cur_row += 1
                sprites.append(list())
                right, left = None, None
                cur_column = -1
                for x in range(spritesheet.get_width()):
                    empty_column = not any(spritesheet.get_at((x, y))[3] > 0
                                           for y in range(top, bottom + 1))
                    if empty_column and left:
                        right = x - 1
                        cur_column += 1
                        new_sprite = spritesheet.subsurface(pygame.Rect(left, top, right - left + 1,
                                                                        bottom - top + 1))
                        sprites[cur_row].append(new_sprite)
                        right, left = None, None
                    elif not empty_column and not left:
                        left = x
                top, bottom = None, None
            elif not empty_row and not top:
                top = y
        for i, key in enumerate(self.sprites):
            if i < len(sprites):
                self.sprites[key] = sprites[i].copy()
            else:
                break


class Player(AnimatedSprite):
    has_extra_jump: bool
    in_air: bool
    is_sliding: bool
    cur_rotation: int
    jump_count: int
    sliding_right: bool
    sliding_left: bool
    max_speed_sliding: List[int]
    max_speed: List[int]
    gravity: float
    velocity: List[int]
    speed: List[int]
    moving_left: bool
    moving_right: bool
    LEFT = -1
    RIGHT = 1

    def __init__(self, parent_level, spritesheet, x, y, *groups):
        self.level = parent_level
        super().__init__(spritesheet, x, y, *groups)
        self.setup_movement()
        self.hp = 100

    # Базовые параметры физики персонажа
    def setup_movement(self):
        self.speed = [0, 0]
        self.velocity = [3, 3]
        self.gravity = 0.3
        self.max_speed = [4, 16]
        self.max_speed_sliding = [4, 4]

        self.moving_left, self.moving_right = False, False
        self.sliding_left, self.sliding_right = False, False

        self.jump_count = 2
        self.cur_rotation = Player.RIGHT

        self.is_sliding = False
        self.in_air = False
        self.has_extra_jump = False

        # Применение параметров ускорения для персонажа

    def update_movement(self):
        self.speed = [0, 0]
        # Применение горизонтального ускорения
        if self.moving_right:
            self.speed[0] += self.velocity[0]
        if self.moving_left:
            self.speed[0] -= self.velocity[0]

        # Применение вертикального ускорения, учет гравитации и нормализация вертикального ускорения
        self.speed[1] += self.velocity[1]
        self.velocity[1] += self.gravity
        self.velocity[1] = min(self.velocity[1], self.max_speed[1])

        # Дополнительная нормализация вертикальной скорости и ускорения в зависимости от того
        # Находится ли в данный момент персонаж в состоянии скольжения
        if self.is_sliding:
            self.speed[1] = min(self.speed[1], self.max_speed_sliding[1])
            self.velocity[1] = min(self.velocity[1], self.max_speed_sliding[1])
        else:
            self.speed[1] = min(self.speed[1], self.max_speed[1])

    # Функция перемещения персонажа - с учётом и компенсацией возможных столкновений по всем осям
    def move(self):
        collision = {"top": False, "right": False, "left": False, "bottom": False}

        # Перемещаем персонажа и проверяем столкновения по горизонтальной оси
        self.rect.x += int(self.speed[0])
        collided = Collision.get_collision(self.rect, self.level.tiles_group)
        for obj in collided:
            if self.speed[0] > 0:
                self.rect.right = obj.rect.left
                collision["right"] = True
            else:
                self.rect.left = obj.rect.right
                collision["left"] = True

        # Перемещаем персонажа и проверяем столкновения по вертикальной оси
        self.rect.y += int(self.speed[1])
        collided = Collision.get_collision(self.rect, self.level.tiles_group)
        for obj in collided:
            if self.speed[1] > 0:
                self.rect.bottom = obj.rect.top
                collision["bottom"] = True
            else:
                self.rect.top = obj.rect.bottom
                collision["top"] = True

        # При отстутствии столкновения по вертикальной оси и наличием минимального вертикального
        # Ускорения - считаем, что игрок находится в воздухе
        if not collision["bottom"] and self.velocity[1] > 1.75:
            self.in_air = True

        # При столкновении по вертикальной оси с полом
        # Обнуляем характеристики sliding
        # Обнуляем количество возможных прыжков
        # Обнуляем вертикальное ускорение
        if collision["bottom"]:
            self.in_air = False
            self.jump_count = 2
            self.velocity[1] = 0
            self.sliding_right = False
            self.sliding_left = False
            self.is_sliding = False

        # При столкновении со стеной слева и при отсутствии предшедствующего скольжения слева
        # Обнуляем количество допустимых прыжков, разрешаем дополнительный прыжок от стены
        # Устанавливаем параметры sliding
        elif collision["left"] and not self.sliding_left:
            self.jump_count = 0
            self.has_extra_jump = True
            self.sliding_left = True
            self.sliding_right = False
            self.is_sliding = True

        # При столкновении со стеной справа и при отсутствии предшедствующего скольжения справа
        # Обнуляем количество допустимых прыжков, разрешаем дополнительный прыжок от стены
        # Устанавливаем параметры sliding
        elif collision["right"] and not self.sliding_right:
            self.jump_count = 0
            self.has_extra_jump = True
            self.sliding_right = True
            self.sliding_left = False
            self.is_sliding = True

        # При отсутствии столкновений по горизонтальной оси, но предшедствующем скольжении
        # Отключаем возможность дополнительного прыжка от стены
        # Нормализируем вертикальное ускорение
        elif not collision["right"] and not collision["left"]:
            if self.is_sliding:
                self.is_sliding = False
                self.has_extra_jump = False
                self.velocity[1] = min(self.velocity[1], self.max_speed_sliding[1])
            offset = 4
            if not Collision.get_collision(self.rect.move(-offset, 0), self.level.tiles_group):
                self.sliding_left = False
            if not Collision.get_collision(self.rect.move(offset, 0), self.level.tiles_group):
                self.sliding_right = False

        # При столкновении с потолком - обнуляем вертикальное ускорение
        if collision["top"]:
            self.velocity[1] = 0

        self.update_status(self.is_sliding, self.in_air, self.cur_rotation,
                           self.velocity[1] > 0, self.moving_right ^ self.moving_left)

    # Обновление положения, статуса (в воздухе, процессе скольжения), персонажа
    # С учётом клавиатурного ввода

    def get_damage(self, damage):
        global LAST_HIT_TIME
        if time.time() - LAST_HIT_TIME >= 1.5:
            LAST_HIT_TIME = time.time()
            self.hp -= damage
            if self.hp > 0:
                pass
                # self.status = SpriteStates.GET_DAMAGE
                # self.update()
            else:
                self.kill()
                self.level.spawn_player()

    def event_handling(self, event):
        if event.type == pygame.KEYDOWN:
            # При перемещении влево или вправо - меняем текущее направление персонажа
            # Также начианем движение персонажа в соответствующую сторону
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.moving_right = True
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.moving_left = True
            # При попытке прыжка - проверяем на наличие дополнительного прыжка (при скольжении)
            # Или при наличии второго прыжка (self.jump_count)
            elif event.key == pygame.K_UP or pygame.key == pygame.K_w:
                if self.jump_count > 0 or self.has_extra_jump:
                    self.in_air = True
                    self.has_extra_jump = False
                    self.velocity[1] = -7.5
                    self.jump_count = max(self.jump_count - 1, 0)
        # При отпускании клавиши - останавливаем движение персонажа
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.moving_right = False
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.moving_left = False
        if self.moving_left or self.moving_right:
            self.cur_rotation = Player.RIGHT if self.moving_right else Player.LEFT

    def update_status(self, is_sliding, in_air, cur_rotation, falling, moving):
        if is_sliding and in_air:
            super().set_status(SpriteStates.SLIDING, not cur_rotation == Player.RIGHT)
        elif in_air:
            if falling:
                super().set_status(SpriteStates.FALLING, cur_rotation == Player.RIGHT)
            else:
                super().set_status(SpriteStates.JUMPING, cur_rotation == Player.RIGHT)
        elif moving:
            super().set_status(SpriteStates.MOVING, cur_rotation == Player.RIGHT)
        else:
            super().set_status(SpriteStates.IDLE, cur_rotation == Player.RIGHT)

    def update(self, *args):
        self.update_movement()
        self.move()
        super().update(*args)


class MovingEnemy(AnimatedSprite):
    def __init__(self, x, y, damage, speed, points, spritesheet, groups):
        super().__init__(spritesheet, x, y, *groups)
        self.damage = damage
        self.points = points
        self.next_point = points[0]
        self.speed = speed
        self.all_states = [[]]
        self.generate_states()
        self.state = deepcopy(self.all_states[0])
        self.state_number = 0
        self.point_number = 0
        self.side_point = 1
        self.side_state = 1
        self.set_status(self.all_states[0][0])
        self.rect.center = (x + TILE_WIDTH // 2, y + TILE_HEIGHT // 2)
        self.addition_x, self.addition_y = update_addition_center(self)

    def generate_states(self):
        for i in range(1, len(self.points)):
            if self.points[i][0] != self.points[i - 1][0]:
                difference = self.points[i][0] - self.points[i - 1][0]
                self.all_states.append([SpriteStates.MOVING, [difference // abs(difference), 0]])
            else:
                difference = self.points[i][1] - self.points[i - 1][1]
                self.all_states.append([SpriteStates.JUMPING, [0, difference // abs(difference)]])
        self.all_states[0] = self.all_states[1]

    def change_state(self, direction=False):
        self.state_number += self.side_state
        if self.state_number == len(self.all_states) or self.state_number <= 0:
            self.side_state *= -1
            self.state_number += self.side_state
        self.state = deepcopy(self.all_states[self.state_number])
        if self.side_state < 0 and self.state_number:
            self.state[1][0] *= -1
            self.state[1][1] *= -1
        if self.state[0] == SpriteStates.MOVING:
            if self.state[1] == [1, 0]:
                direction = True
            elif self.state[1] == [-1, 0]:
                direction = False
        else:
            direction = True
        self.set_status(self.state[0], direction)

    def change_point(self):
        self.point_number += self.side_point
        if self.point_number == len(self.points) or self.point_number < 0:
            self.side_point *= -1
            self.point_number += 2 * self.side_point
        self.next_point = self.points[self.point_number]

    def check_state(self):
        if self.state[0] == SpriteStates.MOVING:
            if self.state[1][0] > 0:
                if self.rect.x >= real_coords(self.next_point[0], x=True):
                    self.change_point()
                    self.change_state()
            elif self.state[1][0] < 0:
                if self.rect.x <= real_coords(self.next_point[0], x=True):
                    self.change_point()
                    self.change_state()
        elif self.state[0] == SpriteStates.JUMPING:
            if self.state[1][1] < 0:
                if self.rect.y <= real_coords(self.next_point[1], y=True):
                    self.change_point()
                    self.change_state()
            elif self.state[1][1] > 0:
                if self.rect.y >= real_coords(self.next_point[1], y=True):
                    self.change_point()
                    self.change_state()

    def update(self):
        self.rect.x += int(self.state[1][0] * self.speed)
        self.rect.y += int(self.state[1][1] * self.speed)
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y)
        self.check_state()
        super().update()
        self.addition_x, self.addition_y = update_addition_center(self)
        if self.state[0] == SpriteStates.JUMPING:
            self.rect = self.image.get_rect().move(self.rect.x + self.addition_x, self.rect.y)
        elif self.state[0] == SpriteStates.MOVING:
            self.rect = self.image.get_rect().move(self.rect.x, self.rect.y + self.addition_y)


class ShootingEnemy(AnimatedSprite):
    def __init__(self, x, y, damage, spritesheet, bullet_image, groups, bullet_speed=1,
                 all_sides=None, smart=False):
        super().__init__(spritesheet, x, y, *groups)
        if all_sides is None:
            all_sides = [EAST]
        self.smart = smart
        self.bullet_image = bullet_image
        self.all_sides = all_sides
        self.last_shoot_time = 0
        self.bullet_speed = bullet_speed
        self.addition_x, self.addition_y = update_addition_all(self.rect.w, self.rect.h)
        self.rect = self.image.get_rect().move(self.rect.x + self.addition_x // 2,
                                               self.rect.y + self.addition_y)
        self.damage = damage

    def update(self):
        if time.time() - self.last_shoot_time > 10:
            self.last_shoot_time = time.time()
            if not self.smart:
                for _ in self.all_sides:
                    Bullet(self.rect.x, self.rect.y, self.bullet_speed, self.damage, "bat2.png")
            else:
                SmartBullet(self.rect.x, self.rect.y, self.bullet_speed, self.damage, "bat2.png")
        super().update()


class HATEnemy(AnimatedSprite):
    def __init__(self, spritesheet, x, y, damage, speed, groups):
        self.speed = speed
        self.gravity = 5
        self.damage = damage
        super().__init__(spritesheet, x, y, *groups)
        self.set_status(SpriteStates.MOVING, True if self.speed > 0 else False)
        self.addition_x, self.addition_y = update_addition_all(self.rect.w, self.rect.h)
        self.rect = self.image.get_rect().move(self.rect.x + self.addition_x // 2,
                                               self.rect.y + self.addition_y)

    def get_collisions(self):
        return pygame.sprite.spritecollide(self, tiles_sprites, False)

    def hat(self):
        collisions = self.get_collisions()
        if collisions:
            for _ in collisions:
                self.speed *= -1
                self.rect = self.image.get_rect().move(self.rect.x + self.speed, self.rect.y)
                self.set_status(self.status, True if self.speed > 0 else False)
                break

    def gravitation(self):
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y + self.gravity)
        collisions = self.get_collisions()
        if collisions:
            for _ in collisions:
                self.rect = self.image.get_rect().move(self.rect.x, self.rect.y - self.gravity)
                break

    def update(self):
        self.hat()
        self.gravitation()
        self.rect = self.image.get_rect().move(self.rect.x + self.speed, self.rect.y)
        self.gravity = 0
        super().update()


class HATSaw(HATEnemy):
    def __init__(self, spritesheet, x, y, damage, speed, groups):
        super().__init__(spritesheet, x, y, damage, speed, groups)
        self.set_status(SpriteStates.IDLE)

    def update(self):
        super().update()


class Bullet(AnimatedSprite):
    def __init__(self, x, y, speed, damage, spritesheet, sides=None):
        super().__init__(spritesheet, -100, -100, bullet_group)
        self.rect = self.image.get_rect().move(x + TILE_WIDTH // 2 - self.rect.width // 2,
                                               y + TILE_HEIGHT // 2 - self.rect.height // 2)
        if sides is None:
            sides = [1, 1]
        self.status = SpriteStates.IDLE
        self.damage = damage
        self.side_x = sides[0]
        self.side_y = sides[1]
        self.speed_x = speed
        self.speed_y = speed
        self.last_time = 0

    def update(self):
        if self.speed_x > FRAME:
            self.rect.x += int(self.side_x)
        if self.speed_y > FRAME:
            self.rect.y += int(self.side_y)
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y)
        # Анимация взрыва
        # self.status = SpriteStates.DEAD
        # super().update()
        # self.kill()
        collides = pygame.sprite.spritecollide(self, tiles_sprites, False)
        if collides:
            # Анимация взрыва
            self.kill()
        super().update()


class SmartBullet(Bullet):
    def __init__(self, x, y, speed, damage, spritesheet):
        super().__init__(x, y, speed, damage, spritesheet)

    def update(self):
        x = self.rect.x + self.rect.w // 2 - (player.rect.x + player.rect.w // 2)
        y = self.rect.y + self.rect.h // 2 - (player.rect.y + player.rect.h // 2)
        if x:
            self.side_x = -x // abs(x)
            diff_y = abs(y) / abs(x)
        else:
            diff_y = 5
        if y:
            diff_x = abs(x) / abs(y)
            self.side_y = -y // abs(y)
        else:
            diff_x = 5
        if diff_y > diff_x and not x:
            diff_x = diff_y * diff_x
        elif not y:
            diff_y = diff_x * diff_y
        self.speed_x = diff_x
        self.speed_y = diff_y
        super().update()


class Obstacle(AnimatedSprite):
    def __init__(self, x, y, damage, spritesheet, groups=None):
        if groups is None:
            groups = list()
        super().__init__(spritesheet, x, y, *groups)
        # if self.rect.height < TILE_HEIGHT:
        #    self.image.get_rect().move(self.rect.x, self.rect.y + TILE_HEIGHT - self.rect.height)
        self.addition_x, self.addition_y = update_addition_all(self.rect.w, self.rect.h)
        self.rect = self.image.get_rect().move(self.rect.x + self.addition_x // 2,
                                               self.rect.y + self.addition_y)
        self.damage = damage


class Saw(Obstacle):
    def __init__(self, x, y, damage, spritesheet, groups=None):
        if groups is None:
            groups = list()
        super().__init__(x, y, damage, spritesheet, groups)
        self.rect.center = (x + TILE_WIDTH // 2, y + TILE_HEIGHT // 2)


class RotatingSaw(Saw):
    def __init__(self, x, y, damage, length, spritesheet, groups=None, speed=3, direction=1):
        if groups is None:
            groups = list()
        super().__init__(x, y, damage, spritesheet, groups)
        self.center_x = x + TILE_WIDTH // 2
        self.center_y = -(y + TILE_HEIGHT // 2)
        self.length = max(length, 100)
        self.saw_x = self.center_x - length
        self.saw_y = -self.center_y
        self.angle = 0
        self.speed = speed
        self.direction = direction

    def update(self):
        self.angle += 0.01 * self.speed * self.direction
        if self.angle > 360:
            self.angle = 0
        elif self.angle < 0:
            self.angle = 360
        self.saw_x = self.length * sin(self.angle) + self.center_x
        self.saw_y = -self.length * cos(self.angle) + self.center_y
        self.draw_chain()
        self.draw_base()
        self.rect = self.image.get_rect().move(self.saw_x - self.rect.w // 2,
                                               -self.saw_y - self.rect.h // 2)
        super().update()

    def draw_chain(self):
        for i in range(0, self.length, 6):
            pygame.draw.circle(screen, "black", ((self.length - i) * sin(self.angle)
                                                 + self.center_x,
                                                 -((-self.length + i) * cos(self.angle)
                                                   + self.center_y)), 2)

    def draw_base(self):
        pygame.draw.rect(screen, "black", (self.center_x - 7, -self.center_y - 7, 14, 14), 0)


class Level:
    def __init__(self):
        self.all_sprites = pygame.sprite.Group()
        self.background_group = pygame.sprite.Group()
        self.tiles_group = pygame.sprite.Group()
        self.frontground_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.CELL_SIZE = 24
        self.spritesheet = "forest_spritesheet.png"
        self.spritesheet_width, self.spritesheet_height = 10, 8
        self.grid_size = self.grid_width, self.grid_height = None, None
        self.start = None
        self.finish = None
        self.player = None
        self.navigate, self.rnavigate = cut_sheets(self.spritesheet, self.CELL_SIZE,
                                                   self.spritesheet_width,
                                                   self.spritesheet_height)

    def load_tiles_group(self, tiles_info, *groups):
        for tile_info in tiles_info:
            Tile(self.rnavigate[tuple(tile_info["coords"])], tile_info["x"], tile_info["y"],
                 tile_info["coords"], *groups)

    def load_level(self, dct: dict):
        self.CELL_SIZE = dct["CELL_SIZE"]
        self.grid_size = self.grid_width, self.grid_height = dct["grid_size"]
        self.load_tiles_group(dct["background_group"], self.all_sprites, self.background_group)
        self.load_tiles_group(dct["tiles_group"], self.all_sprites, self.tiles_group)
        self.load_tiles_group(dct["frontground_group"], self.all_sprites, self.frontground_group)
        for enemy in dct["enemy_group"]:
            self.enemy_group.add(enemy)
            self.all_sprites.add(enemy)
        self.start = dct["start"]
        self.finish = dct["finish"]

    def spawn_player(self):
        if not self.start:
            print("Нет точки появления игрока!")
            return
        self.player = Player(self, "spritesheet1.png", self.start.x, self.start.y, self.all_sprites)

    def update(self):
        self.all_sprites.update()

    def draw(self, surface):
        # for sprite in self.all_sprites:
        #     pygame.draw.rect(surface, pygame.Color("red"), sprite.rect)
        self.background_group.draw(surface)
        self.tiles_group.draw(surface)
        if self.finish:
            surface.blit(Scroll.image, (self.finish.rect.x, self.finish.rect.y))
        if self.player:
            surface.blit(self.player.image, (self.player.rect.x, self.player.rect.y))
        self.enemy_group.draw(surface)
        self.frontground_group.draw(surface)

    def event_handling(self, event):
        if self.player:
            self.player.event_handling(event)

    def check_scroll(self):
        return self.player and pygame.sprite.collide_rect(self.player, self.finish)

    def check_enemies(self):
        if self.player:
            for enemy in self.enemy_group:
                if pygame.sprite.collide_mask(self.player, enemy):
                    self.player.get_damage(enemy.damage)


pygame.quit()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Menu()
    ex.show()
    sys.exit(app.exec())
