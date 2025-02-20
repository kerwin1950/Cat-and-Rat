import os
import pygame

# 初始化 pygame 和字体模块
pygame.init()
pygame.font.init()

# 窗口尺寸和步长
HORIZONTAL_LENGTH = 800
VERTICAL_WIDTH = 800
STEP_SIZE = 20

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREEN = (0, 100, 0)
BRIGHT_GREEN = (0, 155, 0)
GREY = (128, 128, 128)
YELLOW = (255, 255, 0)

# 资源路径设置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "resources")

# 资源文件路径
ICON_PATH = os.path.join(RESOURCE_DIR, "logo.png")
BG_MUSIC_PATH = os.path.join(RESOURCE_DIR, "bg.mp3")
EAT_SOUND_PATH = os.path.join(RESOURCE_DIR, "eat.mp3")
HIT_SOUND_PATH = os.path.join(RESOURCE_DIR, "hit.mp3")
LOSER_SOUND_PATH = os.path.join(RESOURCE_DIR, "loser.mp3")
WINNER_SOUND_PATH = os.path.join(RESOURCE_DIR, "winer.mp3")

# 初始化字体
FONT_LARGE = pygame.font.SysFont('SimHei', 50)
FONT_MIDDLE = pygame.font.SysFont('SimHei', 30)
FONT_SMALL = pygame.font.SysFont('SimHei', 20)
