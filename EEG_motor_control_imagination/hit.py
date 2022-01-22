# 导入模块
import math
import sys
import time

import numpy as np
import pygame
from pygame.locals import *
from sklearn.svm import SVC
import scipy.io as sio

import MI_train
from util.glob import get_global_value


class GameWindow(object):
    '''创建游戏窗口类'''

    def __init__(self, *args, **kw):
        self.window_length = 600
        self.window_wide = 500
        # 绘制游戏窗口，设置窗口尺寸
        self.game_window = pygame.display.set_mode((self.window_length, self.window_wide))
        # 设置游戏窗口标题
        pygame.display.set_caption("脑控打砖块")
        # 定义游戏窗口背景颜色参数
        self.window_color = (135, 206, 250)

    def background(self):
        # 绘制游戏窗口背景颜色
        self.game_window.fill(self.window_color)


class Ball(object):
    '''创建球类'''

    def __init__(self, *args, **kw):
        # 设置球的半径、颜色、移动速度参数
        self.ball_color = (255, 215, 0)
        self.move_x = 5
        self.move_y = 5
        self.radius = 10

    def ballready(self):
        # 设置球的初始位置、
        self.ball_x = self.mouse_x
        self.ball_y = self.window_wide - self.rect_wide - self.radius
        # 绘制球，设置反弹触发条件
        pygame.draw.circle(self.game_window, self.ball_color, (self.ball_x, self.ball_y), self.radius)

    def ballmove(self):
        # 绘制球，设置反弹触发条件
        pygame.draw.circle(self.game_window, self.ball_color, (self.ball_x, self.ball_y), self.radius)
        self.ball_x += self.move_x
        self.ball_y -= self.move_y
        # 调用碰撞检测函数
        self.ball_window()
        self.ball_rect()
        if self.ball_y > 520:
            self.gameover = self.over_font.render("Game Over", False, (0, 0, 0))
            self.game_window.blit(self.gameover, (100, 130))
            self.over_sign = 1


class Rect(object):
    '''创建球拍类'''

    def __init__(self, *args, **kw):
        # 设置球拍颜色参数
        self.rect_color = (255, 0, 0)
        self.rect_length = 100
        self.rect_wide = 10
        self.mouse_x = self.window_length / 2

    def rectmove(self, mov_code):
        # predict left
        if mov_code == 0:
            self.mouse_x -= 5
        # predict right
        elif mov_code == 1:
            self.mouse_x += 5
            # 绘制球拍，限定横向边界
        if self.mouse_x >= self.window_length - self.rect_length // 2:
            self.mouse_x = self.window_length - self.rect_length // 2
        if self.mouse_x <= self.rect_length // 2:
            self.mouse_x = self.rect_length // 2
        pygame.draw.rect(self.game_window, self.rect_color, (
            (self.mouse_x - self.rect_length // 2), (self.window_wide - self.rect_wide), self.rect_length,
            self.rect_wide))


class Brick(object):
    def __init__(self, *args, **kw):
        # 设置砖块颜色参数
        self.brick_color = (84, 255, 159)
        self.brick_list = [[1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1],
                           [1, 1, 1, 1, 1, 1]]
        self.brick_length = 80
        self.brick_wide = 20

    def brickarrange(self):
        for i in range(5):
            for j in range(6):
                self.brick_x = j * (self.brick_length + 24)
                self.brick_y = i * (self.brick_wide + 20) + 40
                if self.brick_list[i][j] == 1:
                    # 绘制砖块
                    pygame.draw.rect(self.game_window, self.brick_color,
                                     (self.brick_x, self.brick_y, self.brick_length, self.brick_wide))
                    # 调用碰撞检测函数
                    self.ball_brick()
                    if self.distanceb < self.radius:
                        self.brick_list[i][j] = 0
                        self.score += self.point
        # 设置游戏胜利条件
        if self.brick_list == [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0]]:
            self.win = self.win_font.render("You Win", False, (0, 0, 0))
            self.game_window.blit(self.win, (100, 130))
            self.win_sign = 1


class Score(object):
    '''创建分数类'''

    def __init__(self, *args, **kw):
        # 设置初始分数
        self.score = 0
        # 设置分数字体
        self.score_font = pygame.font.SysFont('arial', 20)
        # 设置初始加分点数
        self.point = 1
        # 设置初始接球次数
        self.frequency = 0

    def countscore(self):
        # 绘制玩家分数
        my_score = self.score_font.render(str(self.score), False, (255, 255, 255))
        self.game_window.blit(my_score, (555, 15))


class GameOver(object):
    '''创建游戏结束类'''

    def __init__(self, *args, **kw):
        # 设置Game Over字体
        self.over_font = pygame.font.SysFont('arial', 80)
        # 定义GameOver标识
        self.over_sign = 0


class Win(object):
    '''创建游戏胜利类'''

    def __init__(self, *args, **kw):
        # 设置You Win字体
        self.win_font = pygame.font.SysFont('arial', 80)
        # 定义Win标识
        self.win_sign = 0


class Collision(object):
    '''碰撞检测类'''

    # 球与窗口边框的碰撞检测
    def ball_window(self):
        if self.ball_x <= self.radius or self.ball_x >= (self.window_length - self.radius):
            self.move_x = -self.move_x
        if self.ball_y <= self.radius:
            self.move_y = -self.move_y

    # 球与球拍的碰撞检测
    def ball_rect(self):
        # 定义碰撞标识
        self.collision_sign_x = 0
        self.collision_sign_y = 0

        if self.ball_x < (self.mouse_x - self.rect_length // 2):
            self.closestpoint_x = self.mouse_x - self.rect_length // 2
            self.collision_sign_x = 1
        elif self.ball_x > (self.mouse_x + self.rect_length // 2):
            self.closestpoint_x = self.mouse_x + self.rect_length // 2
            self.collision_sign_x = 2
        else:
            self.closestpoint_x = self.ball_x
            self.collision_sign_x = 3

        if self.ball_y < (self.window_wide - self.rect_wide):
            self.closestpoint_y = (self.window_wide - self.rect_wide)
            self.collision_sign_y = 1
        elif self.ball_y > self.window_wide:
            self.closestpoint_y = self.window_wide
            self.collision_sign_y = 2
        else:
            self.closestpoint_y = self.ball_y
            self.collision_sign_y = 3
        # 定义球拍到圆心最近点与圆心的距离
        self.distance = math.sqrt(
            math.pow(self.closestpoint_x - self.ball_x, 2) + math.pow(self.closestpoint_y - self.ball_y, 2))
        # 球在球拍上左、上中、上右3种情况的碰撞检测
        if self.distance < self.radius and self.collision_sign_y == 1 and (
                self.collision_sign_x == 1 or self.collision_sign_x == 2):
            if self.collision_sign_x == 1 and self.move_x > 0:
                self.move_x = - self.move_x
                self.move_y = - self.move_y
            if self.collision_sign_x == 1 and self.move_x < 0:
                self.move_y = - self.move_y
            if self.collision_sign_x == 2 and self.move_x < 0:
                self.move_x = - self.move_x
                self.move_y = - self.move_y
            if self.collision_sign_x == 2 and self.move_x > 0:
                self.move_y = - self.move_y
        if self.distance < self.radius and self.collision_sign_y == 1 and self.collision_sign_x == 3:
            self.move_y = - self.move_y
        # 球在球拍左、右两侧中间的碰撞检测
        if self.distance < self.radius and self.collision_sign_y == 3:
            self.move_x = - self.move_x

    # 球与砖块的碰撞检测
    def ball_brick(self):
        # 定义碰撞标识
        self.collision_sign_bx = 0
        self.collision_sign_by = 0

        if self.ball_x < self.brick_x:
            self.closestpoint_bx = self.brick_x
            self.collision_sign_bx = 1
        elif self.ball_x > self.brick_x + self.brick_length:
            self.closestpoint_bx = self.brick_x + self.brick_length
            self.collision_sign_bx = 2
        else:
            self.closestpoint_bx = self.ball_x
            self.collision_sign_bx = 3

        if self.ball_y < self.brick_y:
            self.closestpoint_by = self.brick_y
            self.collision_sign_by = 1
        elif self.ball_y > self.brick_y + self.brick_wide:
            self.closestpoint_by = self.brick_y + self.brick_wide
            self.collision_sign_by = 2
        else:
            self.closestpoint_by = self.ball_y
            self.collision_sign_by = 3
        # 定义砖块到圆心最近点与圆心的距离
        self.distanceb = math.sqrt(
            math.pow(self.closestpoint_bx - self.ball_x, 2) + math.pow(self.closestpoint_by - self.ball_y, 2))
        # 球在砖块上左、上中、上右3种情况的碰撞检测
        if self.distanceb < self.radius and self.collision_sign_by == 1 and (
                self.collision_sign_bx == 1 or self.collision_sign_bx == 2):
            if self.collision_sign_bx == 1 and self.move_x > 0:
                self.move_x = - self.move_x
                self.move_y = - self.move_y
            if self.collision_sign_bx == 1 and self.move_x < 0:
                self.move_y = - self.move_y
            if self.collision_sign_bx == 2 and self.move_x < 0:
                self.move_x = - self.move_x
                self.move_y = - self.move_y
            if self.collision_sign_bx == 2 and self.move_x > 0:
                self.move_y = - self.move_y
        if self.distanceb < self.radius and self.collision_sign_by == 1 and self.collision_sign_bx == 3:
            self.move_y = - self.move_y
        # 球在砖块下左、下中、下右3种情况的碰撞检测
        if self.distanceb < self.radius and self.collision_sign_by == 2 and (
                self.collision_sign_bx == 1 or self.collision_sign_bx == 2):
            if self.collision_sign_bx == 1 and self.move_x > 0:
                self.move_x = - self.move_x
                self.move_y = - self.move_y
            if self.collision_sign_bx == 1 and self.move_x < 0:
                self.move_y = - self.move_y
            if self.collision_sign_bx == 2 and self.move_x < 0:
                self.move_x = - self.move_x
                self.move_y = - self.move_y
            if self.collision_sign_bx == 2 and self.move_x > 0:
                self.move_y = - self.move_y
        if self.distanceb < self.radius and self.collision_sign_by == 2 and self.collision_sign_bx == 3:
            self.move_y = - self.move_y
        # 球在砖块左、右两侧中间的碰撞检测
        if self.distanceb < self.radius and self.collision_sign_by == 3:
            self.move_x = - self.move_x


class Main(GameWindow, Rect, Ball, Brick, Collision, Score, Win, GameOver):
    '''创建主程序类'''

    def __init__(self, *args, **kw):
        super(Main, self).__init__(*args, **kw)
        super(GameWindow, self).__init__(*args, **kw)
        super(Rect, self).__init__(*args, **kw)
        super(Ball, self).__init__(*args, **kw)
        super(Brick, self).__init__(*args, **kw)
        super(Collision, self).__init__(*args, **kw)
        super(Score, self).__init__(*args, **kw)
        super(Win, self).__init__(*args, **kw)

        s = 5       # start, 4<=s<=15
        e = 5       # end, 4<=e<=15
        data_path = 'C:/Users/Ziyi Yang/Desktop/FBCSP/data/data{}.mat'.format(s)
        all_data = sio.loadmat(data_path)['data_all']
        all_order = []
        for i in range(s, e+1):
            if i != s:
                data_path = 'C:/Users/Ziyi Yang/Desktop/FBCSP/data/data{}.mat'.format(i)
                all_data = np.hstack((all_data, sio.loadmat(data_path)['data_all']))
            order_path = []
            for j in range(1, 7):
                order_path.append('C:/Users/Ziyi Yang/Desktop/FBCSP/order/order_subject{}_{}.mat'.format(i, j))
            all_order.extend(order_path)

        X_train, y_train, self.data = MI_train.train(all_data, all_order, start=6, end=6.5, start2=6, end2=6.5)
        X_train2, y_train2, self.data2 = MI_train.train(all_data, all_order, lr=False, start=3, end=3.5, start2=7, end2=7.5)
        for k in np.arange(6.5, 12, 0.5):
            X, y, _ = MI_train.train(all_data, all_order, start=k, end=k+0.5, start2=k, end2=k+0.5)
            X_train = np.vstack((X_train, X))
            y_train = np.hstack((y_train, y))
        for k in np.arange(3.5, 6, 0.5):
            X2, y2, _ = MI_train.train(all_data, all_order, lr=False, start=k, end=k+0.5, start2=k+4, end2=k+4.5)
            X_train2 = np.vstack((X_train2, X2))
            y_train2 = np.hstack((y_train2, y2))

        self.model = SVC(C=0.2, gamma='scale')
        self.model.fit(X_train, y_train)
        self.model2 = SVC(C=0.2, gamma='scale')
        self.model2.fit(X_train2, y_train2)

    def start(self):
        # 定义游戏开始标识
        start_sign, i = 0, 0

        while True:
            self.background()
            self.countscore()

            tick = time.time()
            # get data from 全脑帽 and predict left, right, or steady
            eeg_data = get_global_value("eeg_data")
            if eeg_data is None:
                time.sleep(1)
                continue

            X_test2 = MI_train.test(self.data2, np.array([eeg_data]))
            tock = time.time()
            if self.model2.predict(X_test2)[0] == 0:
                y_pred = 2  # steady
            else:
                X_test = MI_train.test(self.data, np.array([eeg_data]))
                y_pred = self.model.predict(X_test)[0]
                # y_pred = model.predict(np.array([X_train[i%60]]))[0]
            print(tock - tick)
            self.rectmove(y_pred)

            if self.over_sign == 1 or self.win_sign == 1:
                break
            # 获取游戏窗口状态
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    pressed_array = pygame.mouse.get_pressed()
                    if pressed_array[0]:
                        start_sign = 1
            if start_sign == 0:
                self.ballready()
            else:
                self.ballmove()

            self.brickarrange()

            # 更新游戏窗口
            pygame.display.update()
            # 控制游戏窗口刷新频率
            time.sleep(0.010)
            i += 1
