import pygame
import math

from utils import (
    BLOCK_SIZE_X,
    BLOCK_SIZE_Y,
    SPEED,
    BULLET_SPEED,
    PLAYER_COLOR,
    HEALTH_LIMIT,
    get_time_ms,
)
from globals import (
    all_group,
    hearts_group,
    player_bullet_group,
    walls_group,
    entropy,
    entropy_step,
)
from images import HEART_IMAGE, BAD_HEART_IMAGE

from bullet import Bullet


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(all_group)
        global entropy

        # Basic stuff
        self.x = x
        self.y = y
        self.w = 0.6
        self.h = 0.6
        self.rect = pygame.Rect(
            entropy, entropy, self.w * BLOCK_SIZE_X, self.h * BLOCK_SIZE_Y
        )
        entropy += entropy_step

        # Camera
        self.last_camera_dx = 0
        self.last_camera_dy = 0

        self.health = 3

        self.shooting_delay = 210  # in ms
        self.last_shooting_time = 0

    def draw(self, surface, dx, dy):
        self.last_camera_dx = dx
        self.last_camera_dy = dy
        self.rect.x = self.x * BLOCK_SIZE_X + dx
        self.rect.y = self.y * BLOCK_SIZE_Y + dy
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect, 0)
        self.draw_health_bar(surface)

    def draw_health_bar(self, surface):
        for i in range(1, HEALTH_LIMIT + 1):
            sprite = pygame.sprite.Sprite()
            sprite.image = self.image = pygame.transform.scale(
                HEART_IMAGE if i <= self.health else BAD_HEART_IMAGE,
                (1.2 * BLOCK_SIZE_X, 1.2 * BLOCK_SIZE_Y),
            )
            surface.blit(self.image, ((i * 1.2 - 1) * BLOCK_SIZE_X, 0.2 * BLOCK_SIZE_Y))

    def event_handler(self, _, events_types, time):
        keys = pygame.key.get_pressed()
        dx = (
            (
                max(keys[pygame.K_RIGHT], keys[pygame.K_d])
                - max(keys[pygame.K_LEFT], keys[pygame.K_a])
            )
            * SPEED
            * time
        )
        dy = (
            (
                max(keys[pygame.K_DOWN], keys[pygame.K_s])
                - max(keys[pygame.K_UP], keys[pygame.K_w])
            )
            * SPEED
            * time
        )

        if dx != 0:
            self.move_single_axis(dx, 0)
        if dy != 0:
            self.move_single_axis(0, dy)

        # Hearts
        heart_hits = pygame.sprite.spritecollide(self, hearts_group, False)
        for heart in heart_hits:
            self.pickup_heart(heart)

        # Shooting
        if (
            pygame.mouse.get_pressed()[0]
            and get_time_ms() >= self.last_shooting_time + self.shooting_delay
        ):
            self.last_shooting_time = get_time_ms()

            mouse_x, mouse_y = pygame.mouse.get_pos()

            # 0.2 - bullet size
            player_center_x = self.x + (self.w - 0.2) / 2
            player_center_y = self.y + (self.h - 0.2) / 2

            # 0.1 - half of the bullet size
            distance_x = (
                (mouse_x - self.last_camera_dx) / BLOCK_SIZE_X - player_center_x - 0.1
            )
            distance_y = (
                (mouse_y - self.last_camera_dy) / BLOCK_SIZE_Y - player_center_y - 0.1
            )
            angle = math.atan2(distance_y, distance_x)

            speed_x = math.cos(angle) * BULLET_SPEED
            speed_y = math.sin(angle) * BULLET_SPEED

            Bullet(
                player_bullet_group, player_center_x, player_center_y, speed_x, speed_y
            )

    def move_single_axis(self, dx, dy):
        last_rect_x = self.rect.x
        last_rect_y = self.rect.y

        self.x += dx
        self.rect.x = int(self.x * BLOCK_SIZE_X + self.last_camera_dx)
        if self.rect.x == last_rect_x and dx != 0:
            self.x -= dx
            self.rect.x = last_rect_x
            return None

        self.y += dy
        self.rect.y = int(self.y * BLOCK_SIZE_Y + self.last_camera_dy)
        if self.rect.y == last_rect_y and dy != 0:
            self.y -= dy
            self.rect.y = last_rect_y
            return None

        # logging.debug(self.x, self.y)

        walls_hits = pygame.sprite.spritecollide(self, walls_group, False)
        for wall in walls_hits:
            if dx > 0:  # Moving right; Hit the left side of the wall
                self.x = wall.x - self.w
                self.rect.x = last_rect_x
                break
            elif dx < 0:  # Moving left; Hit the right side of the wall
                self.x = wall.x + wall.w
                self.rect.x = last_rect_x
                break
            elif dy > 0:  # Moving down; Hit the top side of the wall
                self.y = wall.y - self.h
                self.rect.y = last_rect_y
                break
            elif dy < 0:  # Moving up; Hit the bottom side of the wall
                self.y = wall.y + wall.h
                self.rect.y = last_rect_y
                break

    def pickup_heart(self, heart):
        if self.health >= HEALTH_LIMIT:
            return None
        else:
            self.health += heart.heal_amount
            heart.kill()