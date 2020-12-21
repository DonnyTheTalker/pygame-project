import pygame, os, sys, time

pygame.init()
SIZE = WIDTH, HEIGHT = 800, 600
FPS = 50

screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()


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


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    delay = clock.tick(FPS)

    screen.fill(pygame.Color("black"))
    pygame.display.flip()
