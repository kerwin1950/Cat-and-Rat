import pygame
import math
import random
from config import HORIZONTAL_LENGTH, VERTICAL_WIDTH, WHITE, YELLOW, DARK_GREEN, BRIGHT_GREEN, GREY

class Rat:
    def __init__(self, speed, r, x, y, max_speed=400, min_speed=20):
        self.speed = speed
        self.initial_speed = speed 
        self.max_speed = max_speed 
        self.min_speed = min_speed 
        self.r = r
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, r*2, r*2)
        self.color = (0, 255, 0)
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, [int(self.x), int(self.y)], self.r)
    
    def track(self, target_x, target_y, speed=None, obstacles=[]):
        if speed is None:
            speed = self.speed
        target_x = max(0, min(HORIZONTAL_LENGTH, target_x))
        target_y = max(0, min(VERTICAL_WIDTH, target_y))
        m_ab = max(math.sqrt((target_x - self.x) ** 2 + (target_y - self.y) ** 2), 0.001)
        if m_ab < 10:
            speed *= m_ab / 10
        if m_ab < 1:
            return
        sin_angle = (target_x - self.x) / m_ab
        cos_angle = (target_y - self.y) / m_ab
        new_x = self.x + speed / 60 * sin_angle
        new_y = self.y + speed / 60 * cos_angle
        new_rect = self.rect.copy()
        new_rect.center = (new_x, new_y)
        if not any(new_rect.colliderect(obs.rect) for obs in obstacles):
            self.x = new_x
            self.y = new_y
            self.rect = new_rect

class Cat:
    def __init__(self, speed, r, x, y, max_speed=500, decay_rate=0.6, min_speed=10):
        self.speed = speed
        self.max_speed = max_speed
        self.min_speed = min_speed
        self.decay_rate = decay_rate
        self.r = r
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, r*2, r*2)
        self.color = (255, 0, 0)
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, [int(self.x), int(self.y)], self.r)
    
    def update_speed(self, pid_speed):
        self.speed = min(self.max_speed, max(self.min_speed, pid_speed))
        self.speed *= self.decay_rate
    
    def adjust_direction(self, current_direction, obstacle_rect, force_random=False):
        slide_directions = [
            pygame.math.Vector2(1, 0), pygame.math.Vector2(-1, 0),
            pygame.math.Vector2(0, 1), pygame.math.Vector2(0, -1),
            pygame.math.Vector2(1, 1), pygame.math.Vector2(-1, 1),
            pygame.math.Vector2(1, -1), pygame.math.Vector2(-1, -1),
            pygame.math.Vector2(2, 0), pygame.math.Vector2(0, 2),
            pygame.math.Vector2(-2, 0), pygame.math.Vector2(0, -2)
        ]
        if force_random:
            random.shuffle(slide_directions)
        speed_boost = 1.3
        for slide_dir in slide_directions:
            test_rect = self.rect.copy()
            test_rect.center = (self.x + slide_dir.x * self.speed * speed_boost / 60,
                                self.y + slide_dir.y * self.speed * speed_boost / 60)
            if not test_rect.colliderect(obstacle_rect):
                return slide_dir
        return None

    def track(self, target_x, target_y, speed=None, obstacles=[]):
        if speed is None:
            speed = self.speed
        direction = pygame.math.Vector2(target_x - self.x, target_y - self.y)
        if direction.length() == 0:
            return
        direction = direction.normalize()
        new_x = self.x + speed / 60 * direction.x
        new_y = self.y + speed / 60 * direction.y
        new_rect = self.rect.copy()
        new_rect.center = (new_x, new_y)
        while speed > 0:
            for obstacle in obstacles:
                if new_rect.colliderect(obstacle.rect):
                    adjusted_direction = self.adjust_direction(direction, obstacle.rect)
                    if adjusted_direction is not None:
                        new_x = self.x + speed / 60 * adjusted_direction.x
                        new_y = self.y + speed / 60 * adjusted_direction.y
                        new_rect.center = (new_x, new_y)
                        if not new_rect.colliderect(obstacle.rect):
                            break
            self.x = new_x
            self.y = new_y
            self.rect = new_rect
            speed -= 1
class CheesePool:
    def __init__(self):
        self.pool=[]
    def get_cheese(self, x, y):
        if self.pool:
            cheese = self.pool.pop()
            cheese.reset(x, y)
            return cheese
        else:
            return Cheese(x, y)
    def return_cheese(self,cheese):
        self.pool.append(cheese)
class Cheese:
    def __init__(self, x, y, size=20):
        self.x = x
        self.y = y
        self.size = size
        self.rect = pygame.Rect(x - size // 2, y, size, size)
    
    def draw(self, screen):
        pygame.draw.polygon(screen, YELLOW, [
            (self.x, self.y),
            (self.x + self.size / 2, self.y + self.size),
            (self.x - self.size / 2, self.y + self.size)
        ])


class Obstacle:
    def __init__(self, screen, x, y):
        self.screen = screen
        self.x = x
        self.y = y
        self.length = random.randint(10, 100)
        self.width = random.randint(10, 100)
        self.color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        self.rect = pygame.Rect(self.x, self.y, self.length, self.width)
    
    def draw(self):
        pygame.draw.rect(self.screen, self.color, self.rect)

class Button:
    def __init__(self, color, x, y, width, height, text=''):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self, screen, font, outline=None):
        if outline:
            pygame.draw.rect(screen, outline, (self.x-5, self.y-5, self.width+10, self.height+10), 0)
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), 0)
        if self.text:
            text_surface = font.render(self.text, True, WHITE)
            screen.blit(text_surface, (self.x + (self.width - text_surface.get_width()) // 2,
                                       self.y + (self.height - text_surface.get_height()) // 2))
    
    def is_over(self, pos):
        return self.x < pos[0] < self.x + self.width and self.y < pos[1] < self.y + self.height
