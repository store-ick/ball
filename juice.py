"""
受击反馈（打击感）。

全是**纯视觉**的东西，不改任何游戏逻辑 —— 所以单独放一个文件，
panel.py 那边只负责"什么时候触发"。

四样：

    横杠震颤    被撞时整条抖一下，0.12 秒衰减回位
    球压扁      撞上那一刻竖着压扁、横向拉宽，0.1 秒弹回
    冻结       打空一根的瞬间全场停顿 60ms —— "这一下很重"的全部来源
    碎块飞散    打空时横杠裂成几块，带着初速度飞出去、受重力、淡出

参数都在下面这几个常量里，觉得过了/不够就调它们。
"""

from __future__ import annotations

import math
import random

import pygame

import theme

# ── 参数 ──────────────────────────────────────────────────────────────────
FREEZE_ON_BREAK = 0.06     # 击破时冻结多久（秒）
SHAKE_TIME = 0.12          # 震颤持续多久
SHAKE_PX = 3.0             # 震颤幅度（像素）
SQUASH_TIME = 0.10         # 压扁持续多久
SQUASH_RATIO = 0.25        # 0.25 = 竖着缩 25%、横着涨 25%

SHARD_COUNT = 5            # 一根横杠裂成几块
SHARD_LIFE = 0.65          # 碎块活多久（秒）
SHARD_SPEED = 260.0        # 碎块飞出去的初速度（像素/秒）
SHARD_GRAVITY = 2200.0


# ── 全局冻结 ──────────────────────────────────────────────────────────────
# 故意做成模块级的：左边打空一根时，右边也一起顿一下 —— 整块屏幕一起"受力"
_freeze_left = 0.0


def freeze(seconds: float = FREEZE_ON_BREAK) -> None:
    global _freeze_left
    _freeze_left = max(_freeze_left, seconds)


def frozen() -> bool:
    return _freeze_left > 0.0


def advance(dt: float) -> None:
    """每帧调一次，推进冻结倒计时。"""
    global _freeze_left
    if _freeze_left > 0.0:
        _freeze_left = max(0.0, _freeze_left - dt)


# ── 横杠震颤 ──────────────────────────────────────────────────────────────
def shake_offset(left: float) -> float:
    """left = 还剩多少震颤时间，返回这一帧横向该偏多少像素。"""
    if left <= 0.0:
        return 0.0
    k = left / SHAKE_TIME                 # 1 → 0
    return math.sin(left * 90.0) * SHAKE_PX * k


# ── 球压扁 ────────────────────────────────────────────────────────────────
def squash_scale(left: float) -> tuple:
    """按剩余时间返回球该有的 (横向倍率, 竖向倍率)。"""
    if left <= 0.0:
        return 1.0, 1.0
    k = left / SQUASH_TIME
    return 1.0 + SQUASH_RATIO * k, 1.0 - SQUASH_RATIO * k


# ── 碎块 ──────────────────────────────────────────────────────────────────
class Shard:
    """横杠被打空时裂出来的一块碎片。"""

    __slots__ = ("x", "y", "vx", "vy", "w", "h", "life", "max_life")

    def __init__(self, x, y, vx, vy, w, h, life):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.w = float(w)
        self.h = float(h)
        self.life = float(life)
        self.max_life = float(life)

    def update(self, dt: float) -> bool:
        """推进一帧。返回 False 表示该消失了。"""
        self.life -= dt
        if self.life <= 0:
            return False
        self.vy += SHARD_GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return True

    def draw(self, surface) -> None:
        # 越接近消失越淡（用一层带透明度的黑盖在原位上）
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        rect = (int(self.x), int(self.y), max(1, int(self.w)), max(1, int(self.h)))
        surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        surf.fill((*theme.INK, alpha))
        surface.blit(surf, rect[:2])


def make_shards(bar_x: float, bar_y: float, bar_w: float, bar_h: float) -> list:
    """把一根横杠裂成几块。参数是横杠的像素位置和尺寸。"""
    n = SHARD_COUNT
    piece_w = bar_w / n
    out = []
    for i in range(n):
        # 每一块往左或往右飞，角度随机一点，看着不像齐步走
        direction = -1.0 if i < n / 2 else 1.0
        vx = direction * SHARD_SPEED * random.uniform(0.5, 1.2)
        vy = -SHARD_SPEED * random.uniform(0.3, 0.9)
        out.append(Shard(
            x=bar_x + i * piece_w,
            y=bar_y,
            vx=vx,
            vy=vy,
            w=piece_w,
            h=bar_h,
            life=SHARD_LIFE * random.uniform(0.7, 1.0),
        ))
    return out
