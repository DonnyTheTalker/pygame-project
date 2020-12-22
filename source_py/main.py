import pygame, os, sys, time, inspect

pygame.init()
SIZE = WIDTH, HEIGHT = 800, 600
FPS = 60

screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()
tiles_sprites = pygame.sprite.Group()


def load_image(name, colorkey=None):
    # jpg, png, gif без анимации, bmp, pcx, tga, tif, lbm, pbm, xpm
    fullname = os.path.join("data", "images", name)  # получение полного пути к файлу
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


HP_SPRITE = load_image("heart.png")


class SpriteStates:
    IDLE = "idle"
    FALLING = "falling"
    MOVING_RIGHT = "moving right"
    MOVING_LEFT = "moving left"
    SLIDING_LEFT = "sliding left"
    SLIDING_RIGHT = "sliding right"
    DEAD = "dead"

    @staticmethod
    def get_states():
        attributes = inspect.getmembers(SpriteStates, lambda a: not (inspect.isroutine(a)))
        attributes = [a[1] for a in attributes if (not (a[0].startswith('__') and
                                                        a[0].endswith('__')))]
        return attributes


class Tile(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__(all_sprites, tiles_sprites)
        self.image = load_image(image)
        self.rect = self.image.get_rect().move(x, y)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(all_sprites)
        self.sprites = dict()
        # Создаем ассоциативный массив спрайтов
        # Для каждого состояния анимации
        for state in SpriteStates.get_states():
            self.sprites[state] = list()
        # ...

        # ...
        self.set_status(SpriteStates.IDLE)
        self.rect = self.image.get_rect().move(x, y)

    def update(self):
        # Добавить контроль длительности анимации
        self.current_sprite = (self.current_sprite + 1) % len(self.sprites[self.status])
        self.update_sprite()

    def set_status(self, status):
        """Смена режима анимации"""
        self.status = status
        self.current_sprite = 0
        self.update_sprite()

    def update_sprite(self):
        """Изменение текущего спрайта"""
        self.image = self.sprites[self.status][self.current_sprite]


class PlayerSprite(AnimatedSprite):
    def __init__(self, spritesheet, x, y):
        super().__init__(x, y)
        # Нарезка spritesheet для каждого SpriteStates


class Player(PlayerSprite):
    def __init__(self, spritesheet, x, y):
        super().__init__(spritesheet, x, y)
        self.health_points = 3
        self.hp = HP(10, 10, 10)

    def draw_hp(self, screen):
        self.hp.draw_hp(screen, self.health_points)


class HP(pygame.sprite.Sprite):
    def __init__(self, x, y, offset):
        super().__init__(all_sprites)
        self.image = HP_SPRITE
        self.x, self.y, self.offset = x, y, offset

    def draw_hp(self, screen, n_hp):
        for i in range(n_hp):
            screen.blit(self.image, (self.x + self.offset * i + self.image.w * i, self.y))


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    delay = clock.tick(FPS)
    # player.draw_hp(screen) - отрисовка хп
    screen.fill(pygame.Color("black"))
    pygame.display.flip()
