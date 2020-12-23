import pygame, os, sys, time
from main import SpriteStates, AnimatedSprite

# Добавить константы стандартного ускорения, скорости, гравитации персонажа
# Протестировать и посмотреть, чтобы динамика игры соответствовала этим скоростям
# Добавить прыжки, отскоки от стен, подогнать их под (пока не существующую) систему анимаций

pygame.init()
SIZE = WIDTH, HEIGHT = 800, 600
FPS = 60

screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()

level_map = ['............................',
             '............................',
             '#....#................#....#',
             '#....#................#....#',
             '#....#................#....#',
             '#....#................#....#',
             '#....#................#....#',
             '#....#................#....#',
             '#..........................#',
             '#..........................#',
             '.###...................###.',
             '........##........##........',
             '#..........................#',
             '#.............@............#',
             '############################']


def load_image(name, colorkey=None):
    # jpg, png, gif без анимации, bmp, pcx, tga, tif, lbm, pbm, xpm
    fullname = os.path.join("..\data", "images", name)  # получение полного пути к файлу
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


tiles = {'wall': load_image("box.png"), 'empty': load_image("grass.png")}
player_spritesheet = "player_spritesheet.png"
tile_width, tile_height = 25, 40

all_sprites = pygame.sprite.Group()
tile_sprites = pygame.sprite.Group()
player_sprites = pygame.sprite.Group()


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, x, y):
        super().__init__(tile_sprites, all_sprites)
        self.type = tile_type
        self.image = pygame.transform.scale(tiles[tile_type], (tile_width, tile_height))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x * tile_width, y * tile_height


class Collision:
    @staticmethod
    def get_collision(rect, obj_list):
        collision_detected = list()
        for obj in obj_list:
            if rect.colliderect(obj.rect):
                collision_detected.append(obj)
        return collision_detected


class Unit(AnimatedSprite):
    LEFT = -1
    RIGHT = 1

    def __init__(self, spritesheet, x, y, *groups):
        super().__init__(spritesheet, x, y, *groups)

    def setup_movemet(self):
        pass

    def update_movement(self):
        pass

    def move(self):
        pass

    def update_status(self, is_sliding, in_air, cur_rotation, falling, moving):
        if is_sliding and in_air:
            super().set_status(SpriteStates.SLIDING, not self.cur_rotation == Unit.RIGHT)
        elif in_air:
            if falling:
                super().set_status(SpriteStates.FALLING, cur_rotation == Unit.RIGHT)
            else:
                super().set_status(SpriteStates.JUMPING, cur_rotation == Unit.RIGHT)
        elif moving:
            super().set_status(SpriteStates.MOVING, cur_rotation == Unit.RIGHT)
        else:
            super().set_status(SpriteStates.IDLE, cur_rotation == Unit.RIGHT)


class Player(Unit):
    def __init__(self, x, y):
        super().__init__(player_spritesheet, x * tile_width, y * tile_height, (player_sprites,))
        self.setup_movement()

    def setup_movement(self):
        self.speed = [0, 0]
        self.velocity = [3, 3]
        self.gravity = 0.3
        self.max_speed = [4, 16]
        self.max_speed_sliding = [4, 4]

        self.moving_left, self.moving_right = False, False
        self.sliding_left, self.sliding_right = False, False

        self.jump_count = 2
        self.is_sliding = False
        self.in_air = False
        self.cur_rotation = Unit.RIGHT

    def update_movement(self):
        self.speed = [0, 0]
        if self.moving_right:
            self.speed[0] += self.velocity[0]
        if self.moving_left:
            self.speed[0] -= self.velocity[0]

        self.speed[1] += self.velocity[1]

        self.velocity[1] += self.gravity
        self.velocity[1] = min(self.velocity[1], self.max_speed[1])

        if self.is_sliding:
            self.speed[1] = min(self.speed[1], self.max_speed_sliding[1])
            self.velocity[1] = min(self.velocity[1], self.max_speed_sliding[1])
        else:
            self.speed[1] = min(self.speed[1], self.max_speed[1])

    def move(self):
        collision = {"top": False, "right": False, "left": False, "bottom": False}

        self.rect.x += int(self.speed[0])
        collided = Collision.get_collision(self.rect, tile_sprites)
        for obj in collided:
            if self.speed[0] > 0:
                self.rect.right = obj.rect.left
                collision["right"] = True
            else:
                self.rect.left = obj.rect.right
                collision["left"] = True

        self.rect.y += int(self.speed[1])
        collided = Collision.get_collision(self.rect, tile_sprites)
        for obj in collided:
            if self.speed[1] > 0:
                self.rect.bottom = obj.rect.top
                collision["bottom"] = True
            else:
                self.rect.top = obj.rect.bottom
                collision["top"] = True

        if not collision["bottom"] and self.velocity[1] > 1.75:
            self.in_air = True
        if collision["bottom"]:
            self.in_air = False
            self.jump_count = 2
            self.velocity[1] = 0
            self.sliding_right = False
            self.sliding_left = False
            self.is_sliding = False
        elif collision["left"] and not self.sliding_left:
            self.jump_count = 1
            self.sliding_left = True
            self.sliding_right = False
            self.is_sliding = True
            # if self.in_air:
            #     self.cur_rotation = {Unit.RIGHT: Unit.LEFT, Unit.LEFT: Unit.RIGHT}[
            #         self.cur_rotation]
        elif collision["right"] and not self.sliding_right:
            self.sliding_right = True
            self.sliding_left = False
            self.is_sliding = True
            self.jump_count = 1
            # if self.in_air:
            #     self.cur_rotation = {Unit.RIGHT: Unit.LEFT, Unit.LEFT: Unit.RIGHT}[
            #         self.cur_rotation]
        elif not collision["right"] and not collision["left"]:
            if self.is_sliding:
                self.is_sliding = False
                self.velocity[1] = min(self.velocity[1], self.max_speed_sliding[1])

        if collision["top"]:
            self.velocity[1] = 0
        self.update_status(self.is_sliding, self.in_air, self.cur_rotation,
                           self.velocity[1] > 0, self.moving_right ^ self.moving_left)

    def update(self, *args):
        if len(args) > 0:
            event = args[0]
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.moving_right = True
                    self.cur_rotation = Unit.RIGHT
                elif event.key == pygame.K_LEFT:
                    self.moving_left = True
                    self.cur_rotation = Unit.LEFT
                elif event.key == pygame.K_UP:
                    if p.jump_count > 0:
                        self.in_air = True
                        p.velocity[1] = -7.5
                        p.jump_count -= 1
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    p.moving_right = False
                elif event.key == pygame.K_LEFT:
                    p.moving_left = False

    def animation(self):
        AnimatedSprite.update(self)


def generate_level():
    new_player, x, y = None, None, None
    for y in range(len(level_map)):
        for x in range(len(level_map[y])):
            if level_map[y][x] == '#':
                Tile("wall", x, y)
            else:
                if level_map[y][x] == '@':
                    new_player = Player(x, y)

    return new_player, x, y


background = pygame.transform.scale(load_image("fon.jpg"), SIZE)
screen.blit(background, (0, 0))
p = generate_level()[0]

running = True
while running:
    p.update_movement()
    p.move()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            p.update(event)
    p.animation()
    print(f"is_sliding: {p.is_sliding}, in_air: {p.in_air}, cur_rotation: {p.cur_rotation}")
    screen.fill(pygame.Color("black"))
    delay = clock.tick(FPS)
    screen.blit(background, (0, 0))
    tile_sprites.draw(screen)
    pygame.draw.rect(screen, "red", p.rect)
    player_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()
