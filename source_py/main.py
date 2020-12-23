import pygame
import os
import sys
import time
import inspect

pygame.init()
SIZE = WIDTH, HEIGHT = 800, 600
FPS = 15

screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()
tiles_sprites = pygame.sprite.Group()


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


HP_SPRITE = load_image("spritesheet1.png")


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


class Tile(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__(all_sprites, tiles_sprites)
        self.image = load_image(image)
        self.rect = self.image.get_rect().move(x, y)


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
        self.rect = self.image.get_rect().move(x, y)

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


class PlayerSprite(AnimatedSprite):
    def __init__(self, spritesheet, x, y):
        super().__init__(spritesheet, x, y)


class Player(PlayerSprite):
    def __init__(self, spritesheet, x, y):
        super().__init__(spritesheet, x, y)
        self.health_points = 3
        self.hp = HP(10, 10, 10)

    def draw_hp(self, screen):
        self.hp.draw_hp(screen, self.health_points)


class HP(pygame.sprite.Sprite):
    def __init__(self, x, y, offset):
        super().__init__()
        self.image = HP_SPRITE
        self.x, self.y, self.offset = x, y, offset

    def draw_hp(self, screen, n_hp):
        for i in range(n_hp):
            screen.blit(self.image, (self.x + self.offset * i + self.image.w * i, self.y))


running = True
for i, state in enumerate(SpriteStates.get_states()):
    if i < 4:
        player = Player("player_spritesheet.png", 40 + i * 70, 40)
        player.set_status(state)
        player = Player("player_spritesheet.png", 40 + i * 70, 150)
        player.set_status(state, False)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    delay = clock.tick(FPS)
    screen.fill(pygame.Color("white"))
    all_sprites.draw(screen)
    all_sprites.update()
    # player.draw_hp(screen) - отрисовка хп
    pygame.display.flip()
terminate()
