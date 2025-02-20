import math
import random
import pygame
import time
from config import HORIZONTAL_LENGTH, VERTICAL_WIDTH, STEP_SIZE

class PID:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()

    def control(self, error):
        current_time = time.time()
        delta_time = max(current_time - self.last_time, 0.001)
        derivative = (error - self.previous_error) / delta_time
        self.integral += error * delta_time
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.previous_error = error
        self.last_time = current_time
        return output

def read_distance_sensor(a, b):
    """计算两个对象中心之间的欧式距离，a 和 b 均需具有 x 和 y 属性"""
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

def is_colliding(x, y, obstacles, radius):
    temp_rect = pygame.Rect(x - radius, y - radius, 2 * radius, 2 * radius)
    return any(temp_rect.colliderect(obstacle.rect) for obstacle in obstacles)

def generate_safe_position(radius, obstacles):
    while True:
        x = random.randint(radius, HORIZONTAL_LENGTH - radius)
        y = random.randint(radius, VERTICAL_WIDTH - radius)
        if not is_colliding(x, y, obstacles, radius):
            return x, y

def generate_cheese_position(obstacles):
    """在不与障碍物碰撞的位置生成奶酪"""
    while True:
        x = random.randint(1, (HORIZONTAL_LENGTH - 20) // STEP_SIZE - 1) * STEP_SIZE
        y = random.randint(1, (VERTICAL_WIDTH - 20) // STEP_SIZE - 1) * STEP_SIZE
        # 注意：这里需要从 entities 导入 Cheese 类
        from entities import Cheese
        cheese = Cheese(x, y)
        if not any(cheese.rect.colliderect(ob.rect) for ob in obstacles):
            return cheese

def initialize_obstacles(screen, num_obstacles):
    """生成一定数量的障碍物"""
    from entities import Obstacle
    obstacles = []
    for _ in range(num_obstacles):
        x = random.randint(0, HORIZONTAL_LENGTH - 80)
        y = random.randint(0, VERTICAL_WIDTH - 80)
        obstacles.append(Obstacle(screen, x, y))
    return obstacles

def update_timer(start_ticks):
    seconds = (pygame.time.get_ticks() - start_ticks) // 1000
    time_left = 60 - seconds
    return max(time_left, 0)
