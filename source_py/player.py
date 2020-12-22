import pygame, os, sys, time

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
             '#..........................#',
             '.###...................###.',
             '........###......###........',
             '..............@.............',
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
player_image = load_image("player.png")
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


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(player_sprites, all_sprites)
        self.image = player_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x * tile_width, y * tile_height
        self.setup_movement()

    def setup_movement(self):
        self.speed = [0, 0]
        self.velocity = [0, 0]
        self.gravity = 0.2
        self.base_speed = [2, 0]
        self.max_speed = [3, 3]
        self.moving_left, self.moving_right = False, False

    def update_movement(self):
        self.speed = [0, 0]
        if self.moving_right:
            self.speed[0] += self.base_speed[0]
        if self.moving_left:
            self.speed[0] -= self.base_speed[0]

        self.speed[1] += self.base_speed[1]
        self.base_speed[1] += self.gravity
        self.base_speed[1] = max(self.base_speed[1], self.max_speed[1])

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
                self.rect.top = obj.rect.top
                collision["top"] = True

        return collision


def generate_level():
    new_player, x, y = None, None, None
    for y in range(len(level_map)):
        for x in range(len(level_map[y])):
            print(level_map[y][x])
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
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                p.moving_right = True
            elif event.key == pygame.K_LEFT:
                p.moving_left = True
        elif event.type == pygame.K_UP:
            if event.key == pygame.K_RIGHT:
                p.moving_right = False
            elif event.key == pygame.K_LEFT:
                p.moving_left = False

    screen.fill(pygame.Color("black"))
    delay = clock.tick(FPS)
    screen.blit(background, (0, 0))
    tile_sprites.draw(screen)
    player_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()
