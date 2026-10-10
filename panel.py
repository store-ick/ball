"""
一个面板 = 一条赛道（球 + 一串横杠）。

物理模型：
    球有 (x, y, vx, vy) 四个量。
    每一帧先受重力：vy += g * dt
    再位移，然后处理三种碰撞：
        1. 左右两侧屏幕壁 —— 水平反弹（vx 取反）
        2. 顶部 —— 不反弹，把球按在顶上（vy 归零），让它自然再落下来
        3. 横杠 —— 只处理"从上往下砸"的情况：结算伤害、给一个固定的向上初速度
    横杠血量 <= 0 就消失，球自然落到下一根。
    球掉出面板底部 = 这一屏通关。
"""

from __future__ import annotations

import pygame

import bignum
import effects
import render
import theme
from entities import Ball, Bar


class Panel:
    def __init__(self, cfg, rect, glob):
        self.cfg = cfg
        self.glob = glob
        self.x, self.y, self.w, self.h = rect

        radius = cfg.ball.radius or glob.ball_radius
        self.ball = Ball(cfg.ball, radius)
        self.bars = []

        self.finished = False
        self.finished_at = None
        self.hits = 0

        self.reset()

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    def reset(self):
        self.finished = False
        self.finished_at = None
        self.hits = 0

        self.bars = [
            Bar(hp, 0.0, self.glob.bar_height, row=i)
            for i, hp in enumerate(self.cfg.bars)
        ]
        self.layout_bars()
        self.apply_scale()

        # 出生点：顶部，横向位置由配置决定
        start_x = self.x + self.w * min(max(self.cfg.ball.start_x, 0.0), 1.0)
        start_y = self.y + self.ball.radius + 4
        self.ball.respawn(start_x, start_y)

    # ------------------------------------------------------------------
    # 布局 / 窗口缩放
    # ------------------------------------------------------------------
    def layout_bars(self):
        """按当前的矩形把横杠铺到各自的行上。

        行数由全局的 bar_count 决定，每屏都一样，所以第 i 行在每一屏
        都落在同一个高度，左右能对齐。按 bar.row 定位，不按列表下标。
        """
        g = self.glob
        top = self.y + self.header_height()
        bottom = self.y + self.h
        rows = g.bar_count or max(1, len(self.bars))
        gap = (bottom - top) / (rows + 1)
        for bar in self.bars:
            bar.y = top + gap * (bar.row + 1)

    def header_height(self) -> float:
        """顶部信息区留多高。窗口压得很扁时按比例收，免得横杠没地方放。"""
        return min(self.glob.header_height, self.h * self.glob.header_ratio)

    # ------------------------------------------------------------------
    # 随窗口缩放物理
    # ------------------------------------------------------------------
    def apply_scale(self):
        """把"当前尺寸 / 配置里的初始尺寸"算成缩放系数挂到球上。

        纵向量（重力、反弹力度）乘 scale_y，横向速度乘 scale_x。
        这样横杠间距变大时球也弹得同样高，下落耗时在任何窗口下都一样
        （落体 t = √(2d/g)，d 和 g 同比例放缩会抵消）。

        球的半径、横杠厚度、字体不缩放。
        """
        if not self.glob.scale_physics:
            sx = sy = 1.0
        else:
            ref_w = self.glob.panel_width or self.w
            ref_h = self.glob.panel_height or self.h
            sx = self.w / ref_w
            sy = self.h / ref_h
        self.ball.scale_x = sx
        self.ball.scale_y = sy

    def relayout(self, rect):
        """窗口大小变了：换新矩形，横杠重新铺，球按比例挪过去。

        位置按比例缩放；速度也按新老系数换算一下，动作才是连着的。
        球的半径、重力、反弹力度的"配置值"都不动 —— 它们只在用的时候乘缩放系数。
        """
        ox, oy, ow, oh = self.x, self.y, self.w, self.h
        old_sx, old_sy = self.ball.scale_x, self.ball.scale_y
        self.x, self.y, self.w, self.h = rect
        if ow <= 0 or oh <= 0:
            return

        kx, ky = self.w / ow, self.h / oh
        self.ball.x = self.x + (self.ball.x - ox) * kx
        self.ball.y = self.y + (self.ball.y - oy) * ky

        self.layout_bars()
        self.apply_scale()

        if old_sx > 0 and old_sy > 0:
            self.ball.vx *= self.ball.scale_x / old_sx
            self.ball.vy *= self.ball.scale_y / old_sy

        self._clamp_ball()

    def _clamp_ball(self):
        """把球按回面板里，免得缩小时卡在墙外。"""
        r = self.ball.radius
        ball = self.ball
        ball.x = min(max(ball.x, self.x + r), self.x + self.w - r)
        ball.y = min(max(ball.y, self.y + r), self.y + self.h - r)

    # ------------------------------------------------------------------
    # 物理
    # ------------------------------------------------------------------
    def update(self, dt: float, elapsed: float):
        if self.finished:
            return

        ball = self.ball
        # 重力也带上窗口缩放系数：窗口变高，重力跟着变强，弹跳高度占比才不变
        gravity = self.glob.gravity * ball.gravity_mult * ball.scale_y

        # 分小步推进，避免球从高处落下时穿过横杠
        speed = max(abs(ball.vx), abs(ball.vy))
        step_len = max(ball.radius * 0.4, 1.0)
        steps = int(speed * dt / step_len) + 1
        steps = max(1, min(steps, 96))
        sub = dt / steps

        for _ in range(steps):
            self._step(ball, gravity, sub)
            if self.finished:
                break

        if self.finished and self.finished_at is None:
            self.finished_at = elapsed

    def _step(self, ball: Ball, gravity: float, dt: float):
        r = ball.radius
        left = self.x
        right = self.x + self.w
        top = self.y
        bottom = self.y + self.h

        ball.vy += gravity * dt
        ball.x += ball.vx * dt
        ball.y += ball.vy * dt

        # 1. 左右屏幕壁
        if ball.x - r < left:
            ball.x = left + r
            ball.vx = abs(ball.vx)
        elif ball.x + r > right:
            ball.x = right - r
            ball.vx = -abs(ball.vx)

        # 2. 顶部（不反弹，压在顶上）
        if ball.y - r < top:
            ball.y = top + r
            if ball.vy < 0:
                ball.vy = 0.0

        # 3. 横杠（只在往下落的时候判定，避免刚弹起来又连撞）
        if ball.vy > 0:
            for bar in list(self.bars):
                if not bar.alive:
                    continue
                if (ball.y + r > bar.y
                        and ball.y - r < bar.bottom
                        and ball.x + r > left
                        and ball.x - r < right):
                    ball.y = bar.y - r
                    ball.bounce_off()       # 弹起来；第一次弹跳时顺手决定横向往哪走
                    self._hit(bar, ball)
                    break

        # 4. 掉出底部 = 通关
        if ball.y - r > bottom:
            self.finished = True

    def _hit(self, bar: Bar, ball: Ball):
        """球砸到横杠：先结算本次伤害，再触发球的能力。"""
        self.hits += 1
        # 数字只精确到整数，但两边方向不同：
        #   伤害是增益 -> 向上取整，免得 ×0.5 把球归零
        #   横杠血量是目标 -> 向下取整，免得出现"显示 0 却还活着"
        ball.damage = bignum.ceil_int(ball.damage)
        bar.hp -= ball.damage

        ctx = effects.EffectContext(ball=ball, bar=bar, panel=self)
        effects.apply_all(ball.ops, ctx)

        bar.hp = bignum.floor_int(bar.hp)
        ball.damage = bignum.ceil_int(ball.damage)

        if not bar.alive:
            bar.hp = bignum.ZERO
            try:
                self.bars.remove(bar)
            except ValueError:
                pass

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def draw(self, surface):
        g = self.glob

        # 横杠
        for bar in self.bars:
            self._draw_bar(surface, bar)

        # 球
        ball = self.ball
        if not self.finished:
            cx, cy, r = int(ball.x), int(ball.y), int(ball.radius)
            pygame.draw.circle(surface, ball.color, (cx, cy), r)
            pygame.draw.circle(surface, theme.INK, (cx, cy), r, 2)
            label = bignum.fmt(ball.damage)
            if len(label) <= 4:
                render.draw_text(surface, label, size=int(r * 1.1),
                                 color=theme.PAPER, center=(cx, cy))

        # 顶部信息：左边球名 + 描述，右边当前伤害
        self._draw_header(surface)

    def _draw_bar(self, surface, bar: Bar):
        rect = (int(self.x), int(bar.y), int(self.w), int(bar.height))
        pygame.draw.rect(surface, theme.INK, rect)

        label = bignum.fmt(bar.hp)
        size = render.fit_size(label, int(self.w * 0.86), int(self.glob.bar_height * 1.15))
        render.draw_text(surface, label, size=size, color=theme.PAPER,
                         center=(int(self.x + self.w / 2), int(bar.y + bar.height / 2)))

    def _draw_header(self, surface):
        pad = 16
        name_size = 34
        desc_size = 18
        dmg_size = 34

        inner_w = max(40, self.w - pad * 2)
        left = self.x + pad
        right = self.x + self.w - pad

        # 先量出伤害占多宽，剩下的才留给球名 —— 免得窗口拖窄时两个撞在一起
        dmg = bignum.fmt(self.ball.damage)
        dmg_s = render.fit_size(dmg, int(inner_w * 0.55), dmg_size, minimum=15)
        dmg = render.clip_text(dmg, dmg_s, inner_w)
        dmg_w = render.text_size(dmg, dmg_s)[0]
        render.draw_text(surface, dmg, size=dmg_s, color=theme.INK, topright=(right, 14))

        name = self.cfg.ball.name
        name_room = max(40, inner_w - dmg_w - 16)
        ns = render.fit_size(name, name_room, name_size, minimum=14)
        name = render.clip_text(name, ns, name_room)
        render.draw_text(surface, name, size=ns, color=theme.INK, topleft=(left, 14))

        name_h = render.text_size(name, ns)[1]
        if self.cfg.ball.desc:
            desc_s = render.fit_size(self.cfg.ball.desc, inner_w, desc_size, minimum=12)
            desc = render.clip_text(self.cfg.ball.desc, desc_s, inner_w)
            render.draw_text(surface, desc, size=desc_s, color=theme.INK_2,
                             topleft=(left, 14 + name_h + 8))
