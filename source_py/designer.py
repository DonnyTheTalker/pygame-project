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
from source_py.main import *

pygame.init()


def load_icon(name):
    return QIcon(f"../data/images/{name}")


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        pygame.init()
        # self.setupUi(self)
        uic.loadUi("../data/UI files/designer.ui", self)
        self.names = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # кодовые символы
        self.level = Level()
        self.timer = QTimer(self)
        self.tile_buttons = QButtonGroup(self)
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
                                     "HATSaw": ["saw.png", "saw2.png"],
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
        self.initUI()
        self.get_size()
        self.timer.start(10)
        self.tiles_button.click()

    def initUI(self):
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
        for i, tile_code in enumerate(self.level.tiles):
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
        self.hide_makrs()
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

    def hide_makrs(self):
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
        self.hide_makrs()
        self.points = []
        for i in marks:
            self.mark_group[i].show()
        self.parameters = []
        self.enemy_class = name
        self.current_enemy = self.enemies_spritesheets[name][int(sender.text())]

    def create_shooting_enemy(self, name, marks):
        sender = self.sender()
        self.hide_makrs()
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
        self.current_tile = button.text()

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
            if event.type == pygame.MOUSEBUTTONUP:
                self.holding = None
            if self.layer == self.level.enemy_group:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
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
        if self.current_tile == "Start":
            image = Flag.image
        elif self.current_tile == "Finish":
            image = Scroll.image
        else:
            image = self.level.tiles[self.current_tile]
        self.screen.blit(image,
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
                image = self.level.tiles[self.current_tile]
                Tile(image, x, y, self.level.navigate[image], self.level.all_sprites, self.layer)

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
        with open(f'../data/levels/{name}.json', 'w', encoding='utf-8') as file:
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.exit(app.exec())
