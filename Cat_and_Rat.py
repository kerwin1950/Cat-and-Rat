import pygame
import math
import sys
import random
import time
import heapq
import os
from pygame.locals import USEREVENT
# 初始化 pygame 模块
pygame.init()
pygame.mixer.init() 
# 游戏窗口尺寸和步长
HORIZONTAL_LENGTH = 800
VERTICAL_WIDTH = 800
STEP_SIZE = 20

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREEN =(0, 100, 0)
BRIGHT_GREEN = (0, 155, 0)
GREY = (128, 128, 128)
YELLOW=(255,255,0)
#资源路径设置
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR=os.path.join(BASE_DIR,"resource")
# 添加音效
EAT_SOUND =pygame.mixer.Sound(os.path.join(RESOURCE_DIR,"eat.mp3"))
HIT_SOUND =pygame.mixer.Sound(os.path.join(RESOURCE_DIR,"hit.mp3"))

LOSER_SOUND =pygame.mixer.Sound(os.path.join(RESOURCE_DIR,"loser.mp3"))
WINNER_SOUND = pygame.mixer.Sound(os.path.join(RESOURCE_DIR,"winer.mp3"))
# 添加背景音乐
pygame.mixer.music.load(os.path.join(RESOURCE_DIR,"bg.mp3"))
ICON = pygame.image.load(os.path.join(BASE_DIR,"logo.png")) 
# 字体设置
FONT_LARGE = pygame.font.SysFont('SimHei', 50)
FONT_MIDDLE = pygame.font.SysFont('SimHei', 30)
FONT_SMALL = pygame.font.SysFont('SimHei', 20)   

def clean_exit():
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    pygame.quit()
    sys.exit()
#PID控制器，用于动态调节速度   
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

#计算两个对象中心之间的欧式距离
def read_distance_sensor(a, b):
    error = math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
    return error

#老鼠对象，具有追踪目标和绘制自身的能力
class Rat:
    def __init__(self, speed, r, x, y, max_speed=400,min_speed=20):
        self.speed = speed
        self.initial_speed= speed 
        self.max_speed = max_speed 
        self.min_speed = min_speed 
        self.r = r
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, r*2, r*2) 
        self.color =(0,255,0) #( random.randint(0,255), random.randint(0,255), random.randint(0,255))
    
    def circle(self, screen):
        pygame.draw.circle(screen, self.color, [int(self.x), int(self.y)], self.r)

    def track(self, target_x, target_y, speed=None, obstacles=[]):
        if speed is None:
            speed = self.speed
        # 限制目标位置在屏幕范围内
        target_x = max(0, min(HORIZONTAL_LENGTH, target_x))
        target_y = max(0, min(VERTICAL_WIDTH, target_y))
        m_ab = max(math.sqrt((target_x - self.x) ** 2 + (target_y - self.y) ** 2), 0.001)
        if m_ab < 10:
             speed *= m_ab / 10  # 当接近目标时减速
        if m_ab < 1:  # 如果距离非常小，则直接停止
             return
        #计算移动方向
        sin_angle = (target_x - self.x) / m_ab
        cos_angle = (target_y - self.y) / m_ab
        new_x = self.x + speed / 60 * sin_angle
        new_y = self.y + speed / 60 * cos_angle
        new_rect = self.rect.copy()
        new_rect.center = (new_x, new_y) 
        # 检查是否与障碍物碰撞
        if not any(new_rect.colliderect(obs.rect) for obs in obstacles):     
           self.x = new_x
           self.y = new_y
           self.rect = new_rect

#猫对象，包含速度调节和碰撞规避等功能
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
        self.is_colliding = False
        self.collision_start_time = None
        self.color = (255,0,0) #( random.randint(0,255), random.randint(0,255), random.randint(0,255))
    
    def circle(self, screen):
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
            pygame.math.Vector2(2, 0), pygame.math.Vector2(0, 2),  # 更大的步长尝试
            pygame.math.Vector2(-2, 0), pygame.math.Vector2(0, -2)
        ]
        if force_random:
            random.shuffle(slide_directions)

        speed_boost = 1.3
        for slide_dir in slide_directions:
            #临时加速
            test_rect = self.rect.copy()
            test_rect.center = (self.x + slide_dir.x * self.speed * speed_boost / 60, self.y + slide_dir.y * self.speed * speed_boost / 60)
            if not test_rect.colliderect(obstacle_rect):
                return slide_dir
        return None # 如果没有找到有效方向，返回原地

    def track(self, target_x, target_y, speed=None, obstacles=[]):
        if speed is None:
            speed = self.speed
        direction = pygame.math.Vector2(target_x - self.x, target_y - self.y).normalize()
        new_x = self.x + speed / 60 * direction.x
        new_y = self.y + speed / 60 * direction.y
        new_rect = self.rect.copy()
        new_rect.center = (new_x, new_y)
        while speed > 0:
            for obstacle in obstacles:
                if new_rect.colliderect(obstacle.rect): 
                    adjusted_direction = self.adjust_direction(direction, obstacle.rect)  # 尝试找到一个没有障碍的方向
                    if adjusted_direction != pygame.math.Vector2(0, 0):  # 检查方向是否有效
                        new_x = self.x + speed / 60 * adjusted_direction.x
                        new_y = self.y + speed / 60 * adjusted_direction.y
                        new_rect.center = (new_x, new_y)
                        if not new_rect.colliderect(obstacle.rect):
                            break  # 如果新方向没有障碍，则使用新方向

            self.x = new_x
            self.y = new_y
            self.rect = new_rect
            speed -= 1 
#奶酪对象
class Cheese:
    def __init__(self, x, y, size=20):
        self.x = x
        self.y = y
        self.size = size
        self.rect = pygame.Rect(x - size / 2, y, size, size)

    def draw(self, screen):
        pygame.draw.polygon(screen, YELLOW, [
            (self.x, self.y),
            (self.x + self.size / 2, self.y + self.size),
            (self.x - self.size / 2, self.y + self.size)
        ])
#在不与障碍物碰撞的位置生成奶酪
def generate_cheese_position(obstacles, step_size, screen_width, screen_height):
    while True:
        x = random.randint(1, (screen_width - 20) // step_size - 1) * step_size
        y = random.randint(1, (screen_height - 20) // step_size - 1) * step_size
        cheese = Cheese(x, y)
        if not any(cheese.rect.colliderect(ob.rect) for ob in obstacles):
            return cheese

#障碍物对象，随机生成位置和尺寸
class Obstacle:
    def __init__(self, screen, x, y):
        self.screen = screen
        self.x = x
        self.y = y
        self.length = random.randint(10,100)
        self.width = random.randint(10,100)
        self.color = ( random.randint(0,255), random.randint(0,255), random.randint(0,255))
        self.area_list = [[self.x, self.y, self.length, self.width]]
        self.rect = pygame.Rect(self.x, self.y, self.length, self.width)
        self.refresh()

    def refresh(self):
         pygame.draw.rect(self.screen, self.color, self.rect)  
#判断给定坐标是否与障碍物发生碰撞
def is_colliding(x, y, obstacles, radius):
    temp_rect = pygame.Rect(x - radius, y - radius, 2 * radius, 2 * radius)
    return any(temp_rect.colliderect(obstacle.rect) for obstacle in obstacles)

def generate_safe_position(radius, obstacles):
    while True:
        x = random.randint(radius, HORIZONTAL_LENGTH - radius)
        y = random.randint(radius, VERTICAL_WIDTH - radius)
        if not is_colliding(x, y, obstacles, radius):
            return x, y
#初始化一定数量的障碍物
def initialize_obstacles(screen, num_obstacles):
    return [Obstacle(screen, random.randint(0, HORIZONTAL_LENGTH - 80), random.randint(0, VERTICAL_WIDTH - 80)) for _ in range(num_obstacles)]

#按钮
class Button:
    def __init__(self, color, x, y, width, height, text=''):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self, screen, outline=None):
        # 绘制按钮以及边框
        if outline:
            pygame.draw.rect(screen, outline, (self.x-5, self.y-5, self.width+10, self.height+10), 0)
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), 0)

        if self.text != '':
            text = FONT_SMALL.render(self.text, 1, WHITE)
            screen.blit(text, (self.x + (self.width/2 - text.get_width()/2), self.y + (self.height/2 - text.get_height()/2)))

    def is_over(self, pos):
        # 检查鼠标是否在按钮上
        if self.x < pos[0] < self.x + self.width:
            if self.y < pos[1] < self.y + self.height:
                return True
        return False
#显示游戏说明界面
def show_instructions(screen):
    button_color = DARK_GREEN  # 按钮颜色
    hover_color = BRIGHT_GREEN  # 鼠标悬停时按钮的颜色
    return_button = Button(button_color, 300, 350, 200, 50, 'Return')
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # 按下ESC返回
                    running = False
            pos = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN:
               if return_button.is_over(pos):  # 检查鼠标点击是否在按钮上
                    running = False
            if event.type == pygame.MOUSEMOTION:
               if return_button.is_over(pos):
                  return_button.color = hover_color
               else:
                 return_button.color = button_color
        screen.fill(BLACK)
        return_button.draw(screen,GREY)
        titile_text = FONT_MIDDLE.render("游戏规则介绍", True, WHITE)
        line_1_text= FONT_SMALL.render("绿色小球代表老鼠，由鼠标位置控制，单击左键可以给其加速。", True, WHITE)
        line_2_text= FONT_SMALL.render("红色大球代表猫，会追逐绿色小球，被红色大球追到损失一条命。", True, WHITE)
        line_3_text= FONT_SMALL.render("黄色三角代表奶酪，老鼠吃到可以加分。", True, WHITE)
        line_4_text= FONT_SMALL.render("老鼠一共有三条命，要求老鼠在一分钟尽量不被猫抓到且多吃奶酪。", True, WHITE)
        text_x=100
        text_y=120
        example_rat = Rat(0, 5,text_x, 160)
        example_rat.circle(screen)
        example_cat= Cat(0,15,text_x,190)
        example_cat.circle(screen)
        example_cheese=Cheese(text_x,220)
        example_cheese.draw(screen)
        screen.blit(titile_text, (text_x, 80))
        screen.blit(line_1_text, (text_x+20, text_y + 30 * 1))
        screen.blit(line_2_text, (text_x+20, text_y + 30 * 2))
        screen.blit(line_3_text, (text_x+20, text_y + 30 * 3))

        pygame.display.flip()
def show_start_screen(screen):
    # 定义按钮属性
    button_color = DARK_GREEN  # 按钮颜色
    hover_color = BRIGHT_GREEN  # 鼠标悬停时按钮的颜色
    start_button = Button(button_color, 300, 250, 200, 50, 'Start Game')
    help_button = Button(button_color, 300, 350, 200, 50, 'Help')
    exit_button = Button(button_color, 300, 450, 200, 50, 'Exit')
    WINNER_SOUND.play()
    WINNER_SOUND.set_volume(0.5)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            pos = pygame.mouse.get_pos()
            if event.type == pygame.QUIT:
                pygame.quit()  # 关闭pygame
                exit()  # 完全退出程序
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.is_over(pos):  # 检查鼠标点击是否在按钮上
                   WINNER_SOUND.stop()
                   pygame.time.delay(300)  # 延迟200毫秒
                   pygame.mixer.music.play()
                   pygame.mixer.music.set_volume(0.2)
                   return True
                if help_button.is_over(pos):
                   show_instructions(screen)
                if exit_button.is_over(pos):
                   return False
        # 检查鼠标悬停状态以改变按钮颜色
        if event.type == pygame.MOUSEMOTION:
            if start_button.is_over(pos):
                start_button.color = hover_color
            else:
                start_button.color = button_color
            if exit_button.is_over(pos):
                exit_button.color = hover_color
            else:
                exit_button.color = button_color
            if help_button.is_over(pos):
                help_button.color = hover_color
            else:
                help_button.color = button_color

        screen.fill(BLACK)  # 清屏
        text = FONT_LARGE.render('Welcome', True, WHITE)
        screen.blit(text, (320, 150))  # 将第一行文本放置在屏幕上
        start_button.draw(screen,GREY) # 绘制按钮
        exit_button.draw(screen,GREY)
        help_button.draw(screen,GREY)
        pygame.display.flip()
    return False
def show_exit_screen(screen,cheese,lives_count):
    screen.fill(BLACK)  # 清空屏幕，填充为黑色
    button_color = DARK_GREEN  # 按钮颜色
    hover_color = BRIGHT_GREEN  # 鼠标悬停时按钮的颜色
    restart_button = Button(button_color, 300, 350, 200, 50, 'Restart Game')
    exit_button = Button(button_color, 300, 450, 200, 50, 'Exit')
    scores=0
    if lives_count>=1:
        scores=lives_count*cheese
    else:
        scores=cheese

    # 创建文本对象
    text = FONT_LARGE.render('Game Over!', True, WHITE)
    cheese_text = FONT_MIDDLE.render("你获得的奶酪数量： {}".format(cheese), True, WHITE)
    lifes_text = FONT_MIDDLE.render("你最后还剩{}条命".format(lives_count),True,WHITE)
    scores_text=FONT_MIDDLE.render("最终得分：{}".format(scores),True,WHITE)
    # 定位文本
    screen.blit(text, (300, 100))
    screen.blit(cheese_text, (300, 200))
    screen.blit(lifes_text, (300, 240))
    screen.blit(scores_text, (300, 280))
    pygame.mixer.music.stop() 
    LOSER_SOUND.play()
    LOSER_SOUND.set_volume(0.5)

    # 等待用户按键以退出
    waiting = True
    while waiting:
       for event in pygame.event.get():
           pos = pygame.mouse.get_pos()
           if event.type == pygame.QUIT:  # 允许用户点击关闭窗口按钮退出
                clean_exit()
           if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.is_over(pos):  # 检查鼠标点击是否在按钮上
                    LOSER_SOUND.stop()
                    pygame.time.delay(300)  # 延迟200毫秒
                    pygame.mixer.music.play()
                    pygame.mixer.music.set_volume(0.2)
                    #main()
                    return True
                elif exit_button.is_over(pos):
                    clean_exit()
          # 检查鼠标悬停状态以改变按钮颜色
           if event.type == pygame.MOUSEMOTION:
                if restart_button.is_over(pos):
                    restart_button.color = hover_color
                else:
                    restart_button.color = button_color
                if exit_button.is_over(pos):
                    exit_button.color = hover_color
                else:
                    exit_button.color = button_color
       restart_button.draw(screen,GREY)
       exit_button.draw(screen,GREY)
       pygame.display.flip()  # 更新屏幕显示这些文本
    return False
def update_timer(start_ticks):
    seconds = (pygame.time.get_ticks() - start_ticks) // 1000  # convert milliseconds to seconds
    time_left = 60 - seconds  # 60 seconds countdown
    return max(time_left, 0)  # avoid negative countdown

def main():
    
    #游戏界面
    screen = pygame.display.set_mode((HORIZONTAL_LENGTH, VERTICAL_WIDTH), pygame.RESIZABLE)
    pygame.display.set_icon(ICON)
    pygame.display.set_caption("猫捉老鼠")
    clock = pygame.time.Clock()
    
    running = show_start_screen(screen)
    obstacles = initialize_obstacles(screen, 20)
    #grid = create_grid(obstacles)  
    # Generate safe positions for Cat and Animal
    cat_x, cat_y = generate_safe_position(15, obstacles)
    rat_x, rat_y = generate_safe_position(5, obstacles)
    cheese = generate_cheese_position(obstacles, STEP_SIZE, HORIZONTAL_LENGTH, VERTICAL_WIDTH)

    cat = Cat(random.randint(60, 300), 15, cat_x, cat_y)
    rat = Rat(random.randint(60, 300), 5, rat_x, rat_y)
    pid_controller = PID(kp=0.9, ki=0.1, kd=0.01)

    lives_count=3
    scores=0
    last_catch_time = pygame.time.get_ticks()  # 使用 pygame 的计时功能
    catch_cooldown = 2000  # 捕捉冷却时间，单位毫秒
    start_ticks = pygame.time.get_ticks()

    while running:
        current_time = pygame.time.get_ticks()  # 获取当前时间
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                mouse_x, mouse_y = pygame.mouse.get_pos()
                # 检查鼠标位置是否在有效范围内
                if 0 <= mouse_x <= HORIZONTAL_LENGTH and 0 <= mouse_y <= VERTICAL_WIDTH:
                    rat.speed = min(rat.speed + 50, rat.max_speed)
        
        target_x, target_y = pygame.mouse.get_pos()

        screen.fill(BLACK)
        for obstacle in obstacles:
            obstacle.refresh()
        
        error = read_distance_sensor(rat, cat)
        pid_speed = max(pid_controller.control(error),0)
        # Gradually reduce speed
        rat.speed = max(rat.min_speed, rat.speed - 1)
        cat.update_speed(pid_speed)  # 更新猫的速度，包括应用衰减
        
        rat.track(target_x, target_y, obstacles=obstacles)
        rat.circle(screen)
        cat.track(rat.x, rat.y, cat.speed, obstacles=obstacles)
        cat.circle(screen)
        cheese.draw(screen)

        if rat.rect.colliderect(pygame.Rect(cheese.x, cheese.y, cheese.size, cheese.size)):
            scores += 1  # 增加分数
            EAT_SOUND.play()  # 播放碰撞音效
            EAT_SOUND.set_volume(0.5)
            cheese = generate_cheese_position(obstacles, STEP_SIZE, HORIZONTAL_LENGTH, VERTICAL_WIDTH)  # 重新生成奶酪
            pygame.time.delay(50)
        # 检查猫是否捉到老鼠，且当前时间大于上次捕捉时间加上冷却时间
        if abs(cat.x - rat.x) < 10 and abs(cat.y - rat.y) < 10:
            if current_time > last_catch_time + catch_cooldown:
                last_catch_time = current_time  # 更新上次捕捉时间
                HIT_SOUND.play()  # 播放碰撞音效
                HIT_SOUND.set_volume(0.3)
                lives_count -= 1
                if lives_count == 0:
                    show_exit_screen(screen,scores,lives_count)
                    start_ticks = pygame.time.get_ticks()
                    lives_count =3
                    scores=0
                    obstacles = initialize_obstacles(screen, 20)
                    cat_x, cat_y = generate_safe_position(15, obstacles)
                    rat_x, rat_y = generate_safe_position(5, obstacles)
                    pid_controller = PID(kp=0.9, ki=0.1, kd=0.01)
                    cat = Cat(random.randint(60, 300), 15, cat_x, cat_y)
                    rat = Rat(random.randint(60, 300), 5, rat_x, rat_y)
                    cheese = generate_cheese_position(obstacles, STEP_SIZE, HORIZONTAL_LENGTH, VERTICAL_WIDTH)
            
                    running = True
        time_left = update_timer(start_ticks)
        timer_text = FONT_MIDDLE.render("Time: {}".format(time_left), True, WHITE)
        screen.blit(timer_text, (600, 10))  # Adjust position as needed
        if time_left <= 0:
            show_exit_screen(screen,scores,lives_count)
            start_ticks = pygame.time.get_ticks()
            lives_count =3
            scores=0
            obstacles = initialize_obstacles(screen, 20)
            cat_x, cat_y = generate_safe_position(15, obstacles)
            rat_x, rat_y = generate_safe_position(5, obstacles)
            pid_controller = PID(kp=0.9, ki=0.1, kd=0.01)
            cat = Cat(random.randint(60, 300), 15, cat_x, cat_y)
            rat = Rat(random.randint(60, 300), 5, rat_x, rat_y)
            cheese = generate_cheese_position(obstacles, STEP_SIZE, HORIZONTAL_LENGTH, VERTICAL_WIDTH)
            


        lives_text = FONT_MIDDLE.render("生命: {}".format(lives_count), True, WHITE)
        screen.blit(lives_text, (10, 60)) 
        scores_text = FONT_MIDDLE.render("奶酪: {}".format(scores), True, WHITE)
        screen.blit(scores_text, (10, 10)) 
        #cat_speed_text = FONT_SMALL.render("Cat Speed: {}".format(int(cat.speed)), True, WHITE)
        #screen.blit(cat_speed_text, (200, 40)) 
        #rat_speed_text = FONT_SMALL.render("Rat Speed: {}".format(int(rat.speed)), True, WHITE)
        #screen.blit(rat_speed_text, (200, 60)) 
                
        pygame.display.flip()
        clock.tick(60)              

if __name__ == '__main__':
    try:
        main()  # 运行你的主函数
    except SystemExit:
        pass  # 捕获 SystemExit 异常，防止打印异常堆栈
