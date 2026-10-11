"""
持续伤害（DoT）—— 挂在横杠上的"每秒掉血"效果。

为什么单独做一套：
    原来所有能力都是"撞击那一刻"触发的，没有时间维度。
    中毒、燃烧这类要"每秒结算一次、可以叠加"，得另立一套。

设计：
    效果挂在**横杠**上（不是球上），每条有自己的：
        base      每秒固定扣多少
        percent   每秒再扣"当前血量"的百分之几（每层）
        stacks    层数，同名的效果撞一次叠一层
        life      还能活几秒（0 = 永久，直到横杠被打死）
    面板每帧调 tick()，攒够 1 秒才真扣血 —— 所以是"每秒 1 次"。

想加新的持续效果，在 effects.py 里写个 { op = "dot", ... } 就够；
要更复杂的（比如伤害随层数平方增长），照 Dot 再写个子类即可。
"""

from __future__ import annotations

from typing import List

import bignum
from bignum import Decimal

# 每秒结算一次
TICK_SECONDS = 1.0


class Dot:
    def __init__(self, name: str = "持续伤害", base=0, percent=0.0,
                 stacks: int = 1, life: float = 0.0, color=(150, 60, 200)):
        self.name = name
        self.base: Decimal = bignum.parse(base)
        self.percent = float(percent)     # 每层每秒扣当前血量的百分之几
        self.stacks = max(1, int(stacks))
        self.life = float(life)           # 0 = 永久
        self.color = tuple(color)

        self.acc = 0.0                    # 攒了多久（够 1 秒就结算）
        self.age = 0.0                    # 活了多久

    # ------------------------------------------------------------------
    def merge(self, other: "Dot") -> None:
        """同名效果叠上来：层数相加；寿命取更长的那个（永久的压过限时的）。"""
        self.stacks += other.stacks
        if self.life <= 0 or other.life <= 0:
            self.life = 0.0
        else:
            self.life = max(self.life, other.life)

    def alive(self) -> bool:
        return self.life <= 0 or self.age < self.life

    def damage_now(self, bar) -> Decimal:
        """这一秒该扣多少血 = 固定值 + 层数% × 当前血量。"""
        part = bar.hp * Decimal(str(self.stacks * self.percent)) / Decimal(100)
        return self.base + part

    def tick(self, dt: float, bar) -> Decimal:
        """推进时间，返回这一帧要扣的总血量。

        不够 1 秒就返回 0 —— 这就是"每秒 1 次"。
        掉帧导致一帧跨过多秒时，就补算几次，不会漏。
        """
        self.age += dt
        self.acc += dt
        if self.acc < TICK_SECONDS:
            return bignum.ZERO

        times = int(self.acc / TICK_SECONDS)
        self.acc -= times * TICK_SECONDS
        return self.damage_now(bar) * times


def tick_bar(bar, dt: float) -> bool:
    """推进一条横杠上的所有持续效果。返回 True 表示它被毒死了。"""
    if not getattr(bar, "dots", None):
        return False

    total = bignum.ZERO
    for dot in bar.dots:
        total += dot.tick(dt, bar)

    if total > 0:
        bar.hp = bignum.floor_int(bar.hp - total)

    # 清掉过期的
    bar.dots = [d for d in bar.dots if d.alive()]
    return not bar.alive


def add_dot(bar, dot: Dot) -> None:
    """往横杠上挂一层。同名的叠层数，不新开一条。"""
    for existing in bar.dots:
        if existing.name == dot.name:
            existing.merge(dot)
            return
    bar.dots.append(dot)
