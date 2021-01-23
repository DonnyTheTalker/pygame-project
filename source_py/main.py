from typing import List, Any, Union

import pygame
import os
import sys
import time
import inspect
import json
from copy import deepcopy
from math import sin, cos

pygame.init()
SIZE = WIDTH, HEIGHT = 800, 600
tile_width = tile_height = 24
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

screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()


def terminate():
    pygame.quit()
    sys.exit()


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


def cut_sheets(sheet, names, cell_size, columns, rows):
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
    tiles = dict()  # словарь surface tile по его кодовому символу
    for i, tile_image in enumerate(frames):
        tiles[names[i]] = tile_image
    return tiles, navigate, rnavigate


def real_coords(coord, x=False, y=False):
    if x and y:
        return coord * tile_width, coord * tile_height
    else:
        if x:
            return coord * tile_width
        if y:
            return coord * tile_height


def update_addition_center(unit):
    addition_y = (unit.rect.centery // tile_height * tile_height +
                  tile_height // 2 - unit.rect.centery)
    addition_x = (unit.rect.centerx // tile_width * tile_width +
                  tile_width // 2 - unit.rect.centerx)
    return addition_x, addition_y


def update_addition_all(width, height):
    return tile_width - width, tile_height - height


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
                    "names": o.names,
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
            print(self.hp)
            if self.hp > 0:
                pass
                # self.status = SpriteStates.GET_DAMAGE
                # self.update()
            else:
                self.kill()
                self.level.spawn_player()
                print("Убили!")
                # Game over

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
        self.rect.center = (x + tile_width // 2, y + tile_height // 2)
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
        self.rect = self.image.get_rect().move(x + tile_width // 2 - self.rect.width // 2,
                                               y + tile_height // 2 - self.rect.height // 2)
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
        # if self.rect.height < tile_height:
        #    self.image.get_rect().move(self.rect.x, self.rect.y + tile_height - self.rect.height)
        self.addition_x, self.addition_y = update_addition_all(self.rect.w, self.rect.h)
        self.rect = self.image.get_rect().move(self.rect.x + self.addition_x // 2,
                                               self.rect.y + self.addition_y)
        self.damage = damage


class Saw(Obstacle):
    def __init__(self, x, y, damage, spritesheet, groups=None):
        if groups is None:
            groups = list()
        super().__init__(x, y, damage, spritesheet, groups)
        self.rect.center = (x + tile_width // 2, y + tile_height // 2)


class RotatingSaw(Saw):
    def __init__(self, x, y, damage, length, spritesheet, groups=None, speed=3, direction=1):
        if groups is None:
            groups = list()
        super().__init__(x, y, damage, spritesheet, groups)
        self.center_x = x + tile_width // 2
        self.center_y = -(y + tile_height // 2)
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
        self.names = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.grid_size = self.grid_width, self.grid_height = None, None
        self.start = None
        self.finish = None
        self.player = None
        self.tiles, self.navigate, self.rnavigate = cut_sheets(self.spritesheet, self.names,
                                                               self.CELL_SIZE, 10, 4)

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


if __name__ == "__main__":
    background_sound = "../data/sounds/background.mp3"
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.music.load(background_sound)
    pygame.mixer.music.set_volume(50)
    pygame.mixer.music.play(-1)
    # while True:
    #     select = input("Какой цикл запустить? (1, 2, 3)").strip()
    #     if select in ['1', '2', '3']:
    #         break
    #     else:
    #         print("Ошибка ввода. Повторите ввод")
    select = '2'
    if select == '1':
        pass
        # running = True
        # for i, cur_state in enumerate(SpriteStates.get_states()):
        #     if i < 5:
        #         player = Player("spritesheet1.png", 40 + i * 70, 40)
        #         player.set_status(cur_state)
        #         player = Player("spritesheet1.png", 40 + i * 70, 150)
        #         player.set_status(cur_state, False)
        #
        # while running:
        #     for event in pygame.event.get():
        #         if event.type == pygame.QUIT:
        #             running = False
        #     delay = clock.tick(FPS)
        #     screen.fill(pygame.Color("white"))
        #     for sprite in player_sprites.sprites():
        #         pygame.draw.rect(screen, "red", sprite.rect)
        #         print(sprite.rect)
        #     for sprite in player_sprites.sprites():
        #         sprite.animate()
        #     all_sprites.draw(screen)
        #     pygame.display.flip()
        # terminate()
    elif select == '2':
        level_name = "saws2"
        path = f"../data/levels/{level_name}.json"
        with open(path, 'r', encoding='utf-8') as file:
            # noinspection PyMethodFirstArgAssignment
            level = json.load(file, object_hook=main_decoder)
            level.spawn_player()
        screen = pygame.display.set_mode((level.grid_width * tile_width,
                                          level.grid_height * tile_height))
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
        terminate()
        # running = True
        # while running:
        #     for event in pygame.event.get():
        #         if event.type == pygame.QUIT:
        #             running = False
        #     FRAME = (FRAME + 1) % MAX_BULLET_SPEED
        #     pygame.display.flip()
        #     clock.tick(FPS)
        # terminate()
