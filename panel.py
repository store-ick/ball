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

import random

import pygame

import bignum
import dots
import juice
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
        self.ball = Ball(cfg.ball, radius, glob.randomness)
        self.bars = []
        self.shards = []            # 被打空的横杠裂出来的碎块（纯视觉）

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
        self.shards = []

        self.bars = [
            Bar(hp, 0.0, self.glob.bar_height, row=i)
            for i, hp in enumerate(self.cfg.bars)
        ]
        self.layout_bars()
        self.apply_scale()

        # 出生点：顶部，横向位置由配置决定（randomness > 0 时再抖一点，
        # 免得每屏的球都从同一条竖线上掉下来）
        sx = min(max(self.cfg.ball.start_x, 0.0), 1.0)
        r = self.glob.randomness
        if r > 0:
            sx = min(max(sx + random.uniform(-r * 0.35, r * 0.35), 0.05), 0.95)
        start_x = self.x + self.w * sx
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

        # 受击反馈（震颤 / 压扁 / 碎块）—— 纯视觉，先推进
        self._tick_juice(dt)
        # 再结算持续伤害（中毒、燃烧…）—— 它们按"每秒"走，跟撞击无关
        self._tick_dots(dt)
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

    def _tick_juice(self, dt: float):
        """推进受击反馈：横杠震颤、球压扁、碎块。纯视觉，不碰物理。"""
        if self.ball.squash > 0:
            self.ball.squash = max(0.0, self.ball.squash - dt)
        for bar in self.bars:
            if bar.shake > 0:
                bar.shake = max(0.0, bar.shake - dt)
        if self.shards:
            self.shards = [s for s in self.shards if s.update(dt)]

    def _tick_dots(self, dt: float):
        """结算挂在横杠上的持续效果（中毒 / 燃烧…）。

        跟撞击无关，纯按时间走 —— 每攒够 1 秒扣一次血。
        被毒死的横杠在这里直接拿掉。
        """
        if not self.bars:
            return
        died = [bar for bar in self.bars if dots.tick_bar(bar, dt)]
        for bar in died:
            try:
                self.bars.remove(bar)
            except ValueError:
                pass

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
        # 受击反馈：横杠抖一下、球压扁一下
        bar.shake = juice.SHAKE_TIME
        ball.squash = juice.SQUASH_TIME
        # 数字只精确到整数，但两边方向不同：
        #   伤害是增益 -> 向上取整，免得 ×0.5 把球归零
        #   横杠血量是目标 -> 向下取整，免得出现"显示 0 却还活着"
        ball.damage = bignum.ceil_int(ball.damage)
        bar.hp -= ball.damage

        ctx = effects.EffectContext(ball=ball, bar=bar, panel=self,
                                    dealt=bignum.floor_int(ball.damage))
        effects.apply_all(ball.ops, ctx)

        bar.hp = bignum.floor_int(bar.hp)
        ball.damage = bignum.ceil_int(ball.damage)

        if not bar.alive:
            bar.hp = bignum.ZERO
            # 击破反馈：全场顿一下 + 横杠裂成几块飞出去
            juice.freeze()
            self.shards.extend(
                juice.make_shards(self.x, bar.y, self.w, bar.height)
            )
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
        # 碎块画在横杠之后，这样它们会盖在别的横杠上面飞
        for shard in self.shards:
            shard.draw(surface)

        # 球（撞到横杠那一刻会被压扁，见 juice.py）
        ball = self.ball
        if not self.finished:
            cx, cy, r = int(ball.x), int(ball.y), int(ball.radius)
            sx, sy = juice.squash_scale(ball.squash)
            rx = max(3, int(r * sx))
            ry = max(3, int(r * sy))
            box = (cx - rx, cy - ry, rx * 2, ry * 2)
            pygame.draw.ellipse(surface, ball.color, box)
            pygame.draw.ellipse(surface, theme.INK, box, 2)
            label = bignum.fmt(ball.damage)
            if len(label) <= 4:
                render.draw_text(surface, label, size=max(8, int(ry * 1.1)),
                                 color=theme.PAPER, center=(cx, cy))

        # 顶部信息：左边球名 + 描述，右边当前伤害
        self._draw_header(surface)

    def _draw_bar(self, surface, bar: Bar):
        """画一根横杠：黑条 = 血条，掉血时从右往左褪成浅灰。"""
        x, y, w, h = int(self.x), int(bar.y), int(self.w), int(bar.height)
        # 受击震颤：整条横杠连着上面的数字一起左右偏一点
        if bar.shake > 0:
            x += int(juice.shake_offset(bar.shake))

        # 黑色占多宽 = 当前血量 / 满格血量（满格就是这根横杠出生时的血量）
        frac = 0.0
        if bar.max_hp > 0:
            frac = float(bar.hp / bar.max_hp)
        frac = min(max(frac, 0.0), 1.0)
        fill_w = int(round(w * frac))

        # 先铺满浅灰（褪掉后的底色），再把左边那截盖成黑色 —— 所以是"从右往左褪"
        pygame.draw.rect(surface, theme.RULE, (x, y, w, h))
        if fill_w > 0:
            pygame.draw.rect(surface, theme.INK, (x, y, fill_w, h))

        # 数字固定画在整条横杠的正中间。颜色按"中间那块是黑是灰"来定，
        # 不然黑色太少的时候白字会糊在浅灰上看不见。
        label = bignum.fmt(bar.hp)
        size = render.fit_size(label, int(self.w * 0.86), int(self.glob.bar_height * 1.15))
        cx, cy = x + w // 2, y + h // 2
        main_color = theme.PAPER if fill_w >= w // 2 else theme.INK

        # 文字正好骑在黑白分界上的时候（比如血量刚好一半），一半会看不见。
        # 这种情况补一圈反色描边。只在骑线时做，平时不浪费渲染。
        text_w = render.text_size(label, size)[0] // 2
        if abs(fill_w - w // 2) < text_w:
            halo = theme.INK if main_color == theme.PAPER else theme.PAPER
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                render.draw_text(surface, label, size=size, color=halo,
                                 center=(cx + dx, cy + dy))

        render.draw_text(surface, label, size=size, color=main_color, center=(cx, cy))

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
