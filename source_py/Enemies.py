import pygame
import os
import sys
import inspect
import time
from copy import deepcopy
from math import sin, cos

pygame.init()
WIDTH, HEIGHT = 1050, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
obstacles_group = pygame.sprite.Group()
FPS = 60
STEP = 50
FRAME = 0
MAX_BULLET_SPEED = 5
LAST_HIT_TIME = 0


def load_image(name, colorkey=None):
    # jpg, png, gif без анимации, bmp, pcx, tga, tif, lbm, pbm, xpm
    fullname = os.path.join("..\\", "data", "images", name)  # получение полного пути к файлу
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


def get_damage(damage):
    global LAST_HIT_TIME
    if time.time() - LAST_HIT_TIME >= 1.5:
        LAST_HIT_TIME = time.time()
        player.hp -= damage
        if player.hp > 0:
            pass
            # player.status = SpriteStates.GET_DAMAGE
            # player.update()
        else:
            player.kill()
            print("Убили!")
            # Game over



# Shooting
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
FRENDLY = True
#


class SpriteStates:
    IDLE = "1idle"
    FALLING = "2falling"
    JUMPING = "3jumping"
    MOVING = "4moving right"
    SLIDING = "5sliding left"
    DEAD = "8dead"

    @staticmethod
    def get_states():
        attributes = inspect.getmembers(SpriteStates, lambda a: not (inspect.isroutine(a)))
        attributes = sorted([a[1] for a in attributes if (not (a[0].startswith('__') and
                                                               a[0].endswith('__')))])
        return attributes


tile_images = {"wall": load_image("box.png"),
               "empty": load_image("grass.png")}
player_image = load_image('player.png', -1)
rat_image = load_image("mouse.png", -1)
rat_image = pygame.transform.scale(rat_image, (50, 50))
plant_image = load_image("plant.png", -1)
plant_image = pygame.transform.scale(plant_image, (50, 50))
bullet_image = load_image("bullet.png")
bullet_image = pygame.transform.scale(bullet_image, (10, 10))
tile_width = tile_height = 50


def real_coords(coord, x=False, y=False):
    if x and y:
        return coord * tile_width, coord * tile_height
    else:
        if x:
            return coord * tile_width
        if y:
            return coord * tile_height


def update_addition_center(unit):
    addition_y = unit.rect.centery // tile_height * tile_height + tile_height // 2 - unit.rect.centery
    addition_x = unit.rect.centerx // tile_width * tile_width + tile_width // 2 - unit.rect.centerx
    return addition_x, addition_y


def update_addition_all(width, height):
    return tile_width - width, tile_height - height


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, spritesheet, x, y, *groups):
        super().__init__(all_sprites, *groups)
        self.direction = True
        self.status = None
        self.current_sprite = 0
        self.sprites = dict()
        # Создаем ассоциативный массив спрайтов
        # Для каждого состояния анимации
        for state in SpriteStates.get_states():
            self.sprites[state] = list()
        self.slice_sprites(load_image(spritesheet))
        self.set_status(SpriteStates.IDLE)
        self.image = self.sprites[self.status][self.current_sprite]
        self.image = pygame.transform.flip(self.image, not self.direction, False)
        self.rect = self.image.get_rect().move(x, y)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        # Добавить контроль длительности анимации
        self.current_sprite = (self.current_sprite + 1) % len(self.sprites[self.status])
        self.update_sprite()

    def set_status(self, status, direction=True):
        """Смена режима анимации"""
        self.status = status
        self.direction = direction
        self.current_sprite = 0
        self.update_sprite()

    def update_sprite(self):
        """Изменение текущего спрайта"""
        self.image = self.sprites[self.status][self.current_sprite]
        self.image = pygame.transform.flip(self.image, not self.direction, False)
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
                        sprite = spritesheet.subsurface(pygame.Rect(left, top, right - left + 1,
                                                                    bottom - top + 1))
                        sprites[cur_row].append(sprite)
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


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        self.type = tile_type
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(pos_x * tile_width, pos_y * tile_height)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.hp = 3
        self.rect = self.image.get_rect().move(pos_x * tile_width + 15, pos_y * tile_height + 5)
        self.mask = pygame.mask.from_surface(self.image)


class MovingEnemy(AnimatedSprite):
    def __init__(self, x, y, damage, speed, points, spritesheet):
        super().__init__(spritesheet, x * tile_width, y * tile_height, enemy_group)
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
        self.rect.center = (x * tile_width + tile_width // 2, y * tile_height + tile_height // 2)
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
        collisions = pygame.sprite.spritecollideany(self, player_group)
        if collisions:
            get_damage(self.damage)
        self.check_state()
        super().update()
        self.addition_x, self.addition_y = update_addition_center(self)
        if self.state[0] == SpriteStates.JUMPING:
            self.rect = self.image.get_rect().move(self.rect.x + self.addition_x, self.rect.y)
        elif self.state[0] == SpriteStates.MOVING:
            self.rect = self.image.get_rect().move(self.rect.x, self.rect.y + self.addition_y)


class StaticEnemies(AnimatedSprite):
    def __init__(self, x, y, damage, spritesheet):
        super().__init__(spritesheet, x * tile_width, y * tile_height, enemy_group)
        self.damage = damage


class ShootingEnemy(StaticEnemies):
    def __init__(self, x, y, damage, spritesheet, bullet_image, bullet_speed=1,
                 all_sides=None, smart=False):
        super().__init__(x, y, damage, spritesheet)
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

    def update(self):
        if time.time() - self.last_shoot_time > 10:
            self.last_shoot_time = time.time()
            if not self.smart:
                for i in self.all_sides:
                    Bullet(self.rect.x, self.rect.y, self.bullet_speed, self.damage, "bat2.png")
            else:
                SmartBullet(self.rect.x, self.rect.y, self.bullet_speed, self.damage, "bat2.png")
        collisions = pygame.sprite.spritecollideany(self, player_group)
        if collisions:
            get_damage(self.damage)
        super().update()


class HATEnemy(AnimatedSprite):
    def __init__(self, spritesheet, x, y, damage, speed):
        super().__init__(spritesheet, x * tile_width, y * tile_height, enemy_group)
        self.damage = damage
        self.addition_x, self.addition_y = update_addition_all(self.rect.w, self.rect.h)
        self.rect = self.image.get_rect().move(self.rect.x + self.addition_x // 2,
                                               self.rect.y + self.addition_y)
        self.speed = speed
        self.set_status(SpriteStates.MOVING, True if self.speed > 0 else False)
        self.gravity = 5

    def get_collisions(self):
        return pygame.sprite.spritecollide(self, tiles_group, False)

    def hat(self):
        collisions = self.get_collisions()
        if collisions:
            for collision in collisions:
                if collision.type == "wall":
                    self.speed *= -1
                    self.rect = self.image.get_rect().move(self.rect.x + self.speed, self.rect.y)
                    self.set_status(self.status, True if self.speed > 0 else False)
                    break

    def gravitation(self):
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y + self.gravity)
        collisions = self.get_collisions()
        if collisions:
            for collision in collisions:
                if collision.type == "wall":
                    self.rect = self.image.get_rect().move(self.rect.x, self.rect.y - self.gravity)
                    break

    def update(self):
        self.hat()
        self.gravitation()
        if pygame.sprite.spritecollideany(self, player_group):
            get_damage(self.damage)
        self.rect = self.image.get_rect().move(self.rect.x + self.speed, self.rect.y)
        self.gravity = 0
        super().update()


class HATSaw(HATEnemy):
    def __init__(self, spritesheet, x, y, damage, speed):
        super().__init__(spritesheet, x, y, damage, speed)
        self.set_status(SpriteStates.IDLE, True if self.speed > 0 else False)

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
        if pygame.sprite.collide_mask(self, player):
            # Анимация взрыва
            #self.status = SpriteStates.DEAD
            #super().update()
            get_damage(self.damage)
            self.kill()
        collides = pygame.sprite.spritecollide(self, tiles_group, False)
        for collide in collides:
            if collide.type == "wall":
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
    def __init__(self, x, y, damage, spritesheet):
        super().__init__(spritesheet, x * tile_width, y * tile_height, obstacles_group)
        if self.rect.height < tile_height:
            self.image.get_rect().move(self.rect.x, self.rect.y + tile_height - self.rect.height)
        self.addition_x, self.addition_y = update_addition_all(self.rect.w, self.rect.h)
        self.rect = self.image.get_rect().move(self.rect.x + self.addition_x // 2,
                                               self.rect.y + self.addition_y)
        self.damage = damage

    def update(self):
        if pygame.sprite.collide_mask(self, player):
            get_damage(self.damage)
        super().update()


class Saw(AnimatedSprite):
    def __init__(self, x, y, damage, spritesheet):
        super().__init__(spritesheet, x * tile_width,
                         y * tile_height, obstacles_group)
        self.damage = damage
        self.rect.center = (x * tile_width + tile_width // 2, y * tile_height + tile_height // 2)

    def update(self):
        if pygame.sprite.collide_mask(self, player):
            get_damage(self.damage)
        super().update()


class RotatingSaw(Saw):
    def __init__(self, x, y, damage, length, spritesheet, speed=3, direction=1):
        super().__init__(x * tile_width + tile_width // 2,
                         y * tile_height + tile_height // 2, damage, spritesheet)
        self.center_x = x * tile_width + tile_width // 2
        self.center_y = -(y * tile_height + tile_height // 2)
        self.length = max(length, 100)
        self.x = self.center_x - length
        self.y = -self.center_y
        self.angle = 0
        self.speed = speed
        self.direction = direction

    def update(self):
        self.angle += 0.01 * self.speed * self.direction
        if self.angle > 360:
            self.angle = 0
        elif self.angle < 0:
            self.angle = 360
        self.x = self.length * sin(self.angle) + self.center_x
        self.y = -self.length * cos(self.angle) + self.center_y
        self.draw_chain()
        self.draw_base()
        self.rect = self.image.get_rect().move(self.x - self.rect.w // 2,
                                               -self.y - self.rect.h // 2)
        super().update()

    def draw_chain(self):
        for i in range(0, self.length, 6):
            pygame.draw.circle(screen, "black", ((self.length - i) * sin(self.angle)
                                                 + self.center_x,
                                                 -((-self.length + i) * cos(self.angle)
                                                     + self.center_y)), 2)

    def draw_base(self):
        pygame.draw.rect(screen, "black", (self.center_x - 7, -self.center_y - 7, 14, 14), 0)


def move_player(player_moved, move_type, last_x, last_y):
    if move_type == 1:
        player_moved.rect.x -= STEP
    elif move_type == 2:
        player_moved.rect.x += STEP
    elif move_type == 3:
        player_moved.rect.y -= STEP
    elif move_type == 4:
        player_moved.rect.y += STEP
    if pygame.sprite.spritecollide(player_moved, tiles_group, False)[0].type == "wall":
        player_moved.rect = player_moved.image.get_rect().move(last_x, last_y)


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    text = ["Приветствую", "", "Правила игры",
            "Если в правилах несколько строк,", "приходится выводить их построчно"]
    bg = pygame.transform.scale(load_image("fon.jpg"), (WIDTH, HEIGHT))
    screen.blit(bg, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 100
    for line in text:
        string_render = font.render(line, True, pygame.Color("black"))
        string_rect = string_render.get_rect()
        text_coord += 10
        string_rect.top = text_coord
        string_rect.x = 10
        text_coord += string_rect.height
        screen.blit(string_render, string_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


def load_level(filename):
    filename = '../data/levels/' + filename
    with open(filename, "r") as map_file:
        level_map = [line.strip() for line in map_file]
        max_width = max(map(len, level_map))
    return list(map(lambda line: line.ljust(max_width, "."), level_map))


def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == ".":
                Tile("empty", x, y)
            elif level[y][x] == "#":
                Tile("wall", x, y)
            if level[y][x] == "@":
                Tile("empty", x, y)
                new_player = Player(x, y)
            if level[y][x] == "R":
                Tile("empty", x, y)
                MovingEnemy(x, y, 1, 1, [[x, y], [0, 13], [7, 13], [7, 5], [10, 5], [10, 13],
                                         [8, 13], [8, 3], [13, 3], [13, 7], [10, 7]],
                            "bag.png")
            if level[y][x] == "T":
                Tile("empty", x, y)
                ShootingEnemy(x, y, 1, "bag.png", bullet_image, 1, smart=True)
            if level[y][x] == "S":
                Tile("wall", x, y)
                RotatingSaw(x, y, 3, 100, "bag.png", speed=3, direction=-1)
                Saw(x, y, 3, "bag.png")
                Obstacle(x + 1, y + 1, 3, "bag.png")
            if level[y][x] == "H":
                Tile("empty", x, y)
                HATSaw("cats.png", x, y, 3, 2)
    return new_player, x, y


player, level_x, level_y = generate_level(load_level("level2.txt"))


start_screen()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                move_player(player, 1, player.rect.x, player.rect.y)
            elif event.key == pygame.K_RIGHT:
                move_player(player, 2, player.rect.x, player.rect.y)
            elif event.key == pygame.K_UP:
                move_player(player, 3, player.rect.x, player.rect.y)
            elif event.key == pygame.K_DOWN:
                move_player(player, 4, player.rect.x, player.rect.y)
    screen.fill(pygame.Color('black'))
    player_group.update()
    enemy_group.update()
    bullet_group.update()
    tiles_group.draw(screen)
    player_group.draw(screen)
    bullet_group.draw(screen)
    enemy_group.draw(screen)
    obstacles_group.update()
    obstacles_group.draw(screen)
    FRAME = (FRAME + 1) % MAX_BULLET_SPEED
    pygame.display.flip()
    clock.tick(FPS)
terminate()
