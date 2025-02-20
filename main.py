import pygame
import sys
import random
import time
from config import *
from entities import Rat, Cat, Cheese, Obstacle, Button
from utils import PID, read_distance_sensor, generate_safe_position, generate_cheese_position, initialize_obstacles, update_timer

# 初始化 pygame
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((HORIZONTAL_LENGTH, VERTICAL_WIDTH), pygame.RESIZABLE)
pygame.display.set_caption("猫捉老鼠")
icon = pygame.image.load(ICON_PATH)
pygame.display.set_icon(icon)

# 加载音效与背景音乐
EAT_SOUND = pygame.mixer.Sound(EAT_SOUND_PATH)
HIT_SOUND = pygame.mixer.Sound(HIT_SOUND_PATH)
LOSER_SOUND = pygame.mixer.Sound(LOSER_SOUND_PATH)
WINNER_SOUND = pygame.mixer.Sound(WINNER_SOUND_PATH)
pygame.mixer.music.load(BG_MUSIC_PATH)

def clean_exit():
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    pygame.quit()
    sys.exit()

def show_instructions():
    button_color = DARK_GREEN
    hover_color = BRIGHT_GREEN
    return_button = Button(button_color, 300, 350, 200, 50, 'Return')
    running = True                  
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                clean_exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            pos = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if return_button.is_over(pos):
                    running = False
            if event.type == pygame.MOUSEMOTION:
                return_button.color = hover_color if return_button.is_over(pos) else button_color
        screen.fill(BLACK)
        return_button.draw(screen, FONT_SMALL, GREY)
        title_text = FONT_MIDDLE.render("游戏规则介绍", True, WHITE)
        line1_text = FONT_SMALL.render("绿色小球代表老鼠，由鼠标控制。", True, WHITE)
        line2_text = FONT_SMALL.render("红色大球代表猫，会追逐老鼠。", True, WHITE)
        line3_text = FONT_SMALL.render("黄色三角代表奶酪，老鼠吃到可以加分。", True, WHITE)
        line4_text = FONT_SMALL.render("老鼠有三条命，在一分钟内尽量存活。", True, WHITE)
        screen.blit(title_text, (100, 80))
        screen.blit(line1_text, (120, 150))
        screen.blit(line2_text, (120, 180))
        screen.blit(line3_text, (120, 210))
        screen.blit(line4_text, (120, 240))
        pygame.display.flip()

def show_start_screen():
    button_color = DARK_GREEN
    hover_color = BRIGHT_GREEN
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
                clean_exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.is_over(pos):
                    WINNER_SOUND.stop()
                    pygame.time.delay(300)
                    pygame.mixer.music.play()
                    pygame.mixer.music.set_volume(0.2)
                    return True
                if help_button.is_over(pos):
                    show_instructions()
                if exit_button.is_over(pos):
                    return False
            if event.type == pygame.MOUSEMOTION:
                start_button.color = hover_color if start_button.is_over(pos) else button_color
                help_button.color = hover_color if help_button.is_over(pos) else button_color
                exit_button.color = hover_color if exit_button.is_over(pos) else button_color
        screen.fill(BLACK)
        text = FONT_LARGE.render('Welcome', True, WHITE)
        screen.blit(text, (320, 150))
        start_button.draw(screen, FONT_SMALL, GREY)
        help_button.draw(screen, FONT_SMALL, GREY)
        exit_button.draw(screen, FONT_SMALL, GREY)
        pygame.display.flip()
    return False

def show_exit_screen(scores, lives_count):
    screen.fill(BLACK)
    button_color = DARK_GREEN
    hover_color = BRIGHT_GREEN
    restart_button = Button(button_color, 300, 350, 200, 50, 'Restart Game')
    exit_button = Button(button_color, 300, 450, 200, 50, 'Exit')
    total_score = lives_count * scores if lives_count >= 1 else scores
    text = FONT_LARGE.render('Game Over!', True, WHITE)
    cheese_text = FONT_MIDDLE.render("奶酪数量： {}".format(scores), True, WHITE)
    lives_text = FONT_MIDDLE.render("剩余生命： {}".format(lives_count), True, WHITE)
    score_text = FONT_MIDDLE.render("最终得分：{}".format(total_score), True, WHITE)
    screen.blit(text, (300, 100))
    screen.blit(cheese_text, (300, 200))
    screen.blit(lives_text, (300, 240))
    screen.blit(score_text, (300, 280))
    pygame.mixer.music.stop()
    LOSER_SOUND.play()
    LOSER_SOUND.set_volume(0.5)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            pos = pygame.mouse.get_pos()
            if event.type == pygame.QUIT:
                clean_exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.is_over(pos):
                    LOSER_SOUND.stop()
                    pygame.time.delay(300)
                    pygame.mixer.music.play()
                    pygame.mixer.music.set_volume(0.2)
                    return True
                elif exit_button.is_over(pos):
                    clean_exit()
            if event.type == pygame.MOUSEMOTION:
                restart_button.color = hover_color if restart_button.is_over(pos) else button_color
                exit_button.color = hover_color if exit_button.is_over(pos) else button_color
        restart_button.draw(screen, FONT_SMALL, GREY)
        exit_button.draw(screen, FONT_SMALL, GREY)
        pygame.display.flip()
    return False

def main():
    clock = pygame.time.Clock()
    running = show_start_screen()
    initial_cheese_count=3
    lives_count = 3
    scores = 0

    obstacles = initialize_obstacles(screen, 20)
    cat_x, cat_y = generate_safe_position(15, obstacles)
    rat_x, rat_y = generate_safe_position(5, obstacles)
    
    cheeses =[generate_cheese_position(obstacles)for _ in range(initial_cheese_count)]
    cat = Cat(random.randint(60, 300), 15, cat_x, cat_y)
    rat = Rat(random.randint(60, 300), 5, rat_x, rat_y)
    pid_controller = PID(0.9, 0.1, 0.01)
    
    last_catch_time = pygame.time.get_ticks()
    catch_cooldown = 2000
    start_ticks = pygame.time.get_ticks()
    
    while running:
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                clean_exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if 0 <= mouse_x <= HORIZONTAL_LENGTH and 0 <= mouse_y <= VERTICAL_WIDTH:
                    rat.speed = min(rat.speed + 50, rat.max_speed)
        target_x, target_y = pygame.mouse.get_pos()
        screen.fill(BLACK)
        for obs in obstacles:
            obs.draw()
        error = read_distance_sensor(rat, cat)
        pid_speed = max(pid_controller.control(error), 0)
        rat.speed = max(rat.min_speed, rat.speed - 1)
        cat.update_speed(pid_speed)
        rat.track(target_x, target_y, obstacles=obstacles)
        rat.draw(screen)
        cat.track(rat.x, rat.y, cat.speed, obstacles=obstacles)
        cat.draw(screen)
        for cheese in cheeses:
            cheese.draw(screen)
        for cheese in cheeses:
            if rat.rect.colliderect(cheese.rect):
                scores += 1
                EAT_SOUND.play()
                EAT_SOUND.set_volume(0.5)
                cheeses.remove(cheese)
                new_cheese_count=random.choice([1,2,3])
                for _ in range(new_cheese_count):
                    new_cheese = generate_cheese_position(obstacles)
                    cheeses.append(new_cheese)
                pygame.time.delay(50)
                break # 一次只处理一个奶酪碰撞，防止重复触发
        
        if abs(cat.x - rat.x) < 10 and abs(cat.y - rat.y) < 10:
            if current_time > last_catch_time + catch_cooldown:
                last_catch_time = current_time
                HIT_SOUND.play()
                HIT_SOUND.set_volume(0.3)
                lives_count -= 1
                if lives_count == 0:
                    if show_exit_screen(scores, lives_count):
                        start_ticks = pygame.time.get_ticks()
                        lives_count = 3
                        scores = 0
                        obstacles = initialize_obstacles(screen, 20)
                        cat_x, cat_y = generate_safe_position(15, obstacles)
                        rat_x, rat_y = generate_safe_position(5, obstacles)
                        pid_controller = PID(0.9, 0.1, 0.01)
                        cat = Cat(random.randint(60, 300), 15, cat_x, cat_y)
                        rat = Rat(random.randint(60, 300), 5, rat_x, rat_y)
                        cheese = generate_cheese_position(obstacles)
                        running = True
        time_left = update_timer(start_ticks)
        timer_text = FONT_MIDDLE.render("Time: {}".format(time_left), True, WHITE)
        screen.blit(timer_text, (600, 10))
        if time_left <= 0:
            if show_exit_screen(scores, lives_count):
                start_ticks = pygame.time.get_ticks()
                lives_count = 3
                scores = 0
                obstacles = initialize_obstacles(screen, 20)
                cat_x, cat_y = generate_safe_position(15, obstacles)
                rat_x, rat_y = generate_safe_position(5, obstacles)
                pid_controller = PID(0.9, 0.1, 0.01)
                cat = Cat(random.randint(60, 300), 15, cat_x, cat_y)
                rat = Rat(random.randint(60, 300), 5, rat_x, rat_y)
                cheese = generate_cheese_position(obstacles)
        lives_text = FONT_MIDDLE.render("生命: {}".format(lives_count), True, WHITE)
        screen.blit(lives_text, (10, 60))
        scores_text = FONT_MIDDLE.render("奶酪: {}".format(scores), True, WHITE)
        screen.blit(scores_text, (10, 10))
        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        pass
