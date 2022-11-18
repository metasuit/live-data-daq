# ---
# Game Template
# ---
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"  # Disable Welcome Message
import pygame, sys, random, math
import pandas as pd
import matplotlib.pyplot as plt


def print_volts(v, font):
    voltage_text = font.render("Peak Voltage: " + str(v), True, BLACK)
    screen.blit(voltage_text, (20, 50))


def transform_volt_to_angle(v):
    angle = (v - volt_streched) / (volt_contracted - volt_streched) * (
                angle_contracted - angle_stretched) + angle_stretched
    return angle


def rotate(surface, angle, pivot, offset):
    """Rotate the surface around the pivot point.

    Args:
        surface (pygame.Surface): The surface that is to be rotated.
        angle (float): Rotate by this angle.
        pivot (tuple, list, pygame.math.Vector2): The pivot point.
        offset (pygame.math.Vector2): This vector is added to the pivot.
    """
    rotated_image = pygame.transform.rotozoom(surface, -angle, 1)  # Rotate the image.
    rotated_offset = offset.rotate(angle)  # Rotate the offset vector.
    # Add the offset vector to the center/pivot point to shift the rect.
    rect = rotated_image.get_rect(center=pivot + rotated_offset)
    return rotated_image, rect  # Return the rotated image and shifted rect.


class Arm(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, width, height):
        super().__init__()

        self.angle = 20
        self.pivot = [pos_x, pos_y]
        self.offset = pygame.math.Vector2(0, 0)
        self.pos_x = pos_x
        self.pos_y = pos_y

        self.image, self.rect = rotate(pygame.image.load('img/arm_100x300.png'), self.angle, self.pivot, self.offset)


class ForeArm(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, width, height):
        super().__init__()

        self.angle = 85
        self.angle_inc = False
        self.angle_dec = False
        self.pivot = [pos_x, pos_y]
        self.offset = pygame.math.Vector2(0, height / 2 + 53)
        self.pos_x = pos_x
        self.pos_y = pos_y

        self.image = pygame.image.load('img/forearm.png')
        self.rect = self.image.get_rect()
        self.rect.center = [self.pos_x, self.pos_y]

    def update(self):

        self.point = pygame.mouse.get_pos()

        if self.angle_inc:
            self.angle += 2
        if self.angle_dec:
            self.angle -= 2

        self.angle = transform_volt_to_angle(volt_curr)

        self.image, self.rect = rotate(pygame.image.load('img/forearm.png'), self.angle, self.pivot, self.offset)


class Joint(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, width, height):
        super().__init__()

        self.angle = 0
        self.pivot = [pos_x, pos_y]
        self.offset = pygame.math.Vector2(0, 0)
        self.pos_x = pos_x
        self.pos_y = pos_y

        self.image = pygame.image.load('img/forearm.png')
        self.rect = self.image.get_rect()
        self.rect.center = [self.pos_x, self.pos_y]

    def update(self):
        self.angle += 1
        self.point = pygame.mouse.get_pos()

        self.image, self.rect = rotate(pygame.image.load('img/joint_85.png'), self.angle, self.pivot, self.offset)


# General Variables (Can be changed anytime)
screen_width = 900
screen_height = 900
joint_height = 85
joint_width = 85
white = (0, 0, 0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
lst = []
average = 0

# General Setup
pygame.init()
text_surface = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()  # Limit fps
font = pygame.font.SysFont('chalkduster.ttf', 52)

# Read out calibration data and adapt scale accordingly
volt_curr = 0
volt_streched = 0
volt_contracted = 0
angle_stretched = 20
angle_contracted = -60
with open("calibration.txt", "r") as f:
    volt_streched = float(f.readline())
    volt_contracted = float(f.readline())

# Game variables
game_active = True

data = []
fonts = pygame.font.get_fonts()

# Sprite Setup
moving_sprites = pygame.sprite.Group()
static_sprites = pygame.sprite.Group()

# Game Screen
pygame.display.set_caption("Biceps Animation 1")
screen = pygame.display.set_mode((screen_width, screen_height))  # Image canvas
bg_img = pygame.image.load('img/background.png')
bg_img = pygame.transform.scale(bg_img, (screen_width, screen_height))

# Generate Objects
Arm = Arm(screen_height / 2 + 63, screen_width / 3 - 30, 70, 270)
static_sprites.add(Arm)
ForeArm = ForeArm(screen_height / 2, screen_width / 2, 70, 270)
Joint = Joint(screen_height / 2, screen_width / 2, joint_width, joint_height)
moving_sprites.add(ForeArm)
moving_sprites.add(Joint)
# moving_sprites.add(Joint)
# static_sprites.add(Arm)


while True:  # Game loop

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and game_active:
                ForeArm.angle_inc = True
            if event.key == pygame.K_DOWN and game_active:
                ForeArm.angle_dec = True
            if event.key == pygame.K_SPACE and not game_active:
                game_active == True

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP and game_active:
                ForeArm.angle_inc = False
            if event.key == pygame.K_DOWN and game_active:
                ForeArm.angle_dec = False

    screen.blit(bg_img, (0, 0))

    static_sprites.draw(screen)
    moving_sprites.draw(screen)
    moving_sprites.update()

    # Read Data
    # data = pd.read_csv('data.csv')
    # y1 = data['total_1'].tolist()
    # total_1 = y1[-1]

    with open('analog-data.txt') as f:
        first_line = f.readline()

        first_line = first_line.replace('[', '')
        first_line = first_line.replace(']', '')
        first_line = first_line.replace("'", '')
        first_line = first_line.replace(' ', '')

        x = first_line.split(",")

        if len(x) > 4:
            for i in range(0, int(len(x))):
                lst.append(float(x[i]))
            average = sum(lst) / len(lst)
            lst.clear()
            if (volt_curr < average - 0.02) or (volt_curr > average + 0.02):
                volt_curr = average
            print_volts(average, font)
        else:
            print_volts(average, font)

    pygame.display.update()  # Draws everything on the screen, what has been drawn before
    clock.tick(60)  # Can't run faster than 60 fps
