"""游戏里的两个对象：横杠和球。"""

from __future__ import annotations

import random

import bignum
from bignum import Decimal


class Bar:
    """一条横杠。它身上显示的数字就是 hp，也就是"血量"。

    row 是它在整屏里的行号（从 0 开始，创建时就定死）。
    窗口缩放重排的时候按 row 定位 —— 这样上面几根已经被打掉了，
    下面的横杠也不会往上串位。
    """

    def __init__(self, hp, y: float, height: float, row: int = 0):
        self.hp: Decimal = bignum.floor_int(bignum.parse(hp))
        self.max_hp: Decimal = self.hp
        self.row = int(row)
        self.y = float(y)
        self.height = float(height)
        # 挂在这根横杠上的持续伤害（中毒、燃烧…），见 dots.py
        self.dots: list = []

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def alive(self) -> bool:
        return self.hp > 0


class Ball:
    """球。

    位置 / 速度用浮点像素，伤害用 Decimal 大数。
    球身上这几个字段是可以被算子改的，所以别把它们当成只读：

        damage         当前伤害
        bounce         反弹力度（撞横杠时给的向上初速度，像素/秒）
        gravity_mult   重力倍率（乘在全局重力上）
    """

    def __init__(self, cfg, radius: float, randomness: float = 0.0):
        self.cfg = cfg
        self.radius = float(radius)
        self.randomness = float(randomness)
        self.color = tuple(cfg.color)
        self.ops = list(cfg.ops)
        # 出生时掷的"性格"（见 respawn）
        self.speed_jitter = 1.0

        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.first_bounce = True        # 还没弹过 -> 开局竖直下落

        # 窗口缩放系数，由所属的 Panel 维护：
        #   scale_y 乘在重力和反弹力度上，scale_x 乘在横向速度上。
        #   配置里关掉"随窗口缩放物理"就恒为 1.0。
        self.scale_x = 1.0
        self.scale_y = 1.0

        self.damage: Decimal = bignum.ceil_int(bignum.parse(cfg.base_damage))
        self.bounce = float(cfg.bounce_speed)
        self.gravity_mult = 1.0

    def respawn(self, x: float, y: float) -> None:
        """回到出生点，并把被算子改过的属性全部复位。

        ★ 同时在这里掷一次这个球的"性格"：
          几个球的物理参数如果完全一样，哪怕方向随机，两边的**节奏**也是一样的
          （同时弹起、同时落杠），看着像镜像，很呆板。

          所以出生时给每个球随机扰动一下反弹力度和横向速度，之后**整局固定**：
            - 两个球各有各的规律，永远不同步 ✓ 看着就有"混乱感"
            - 但每个球内部还是干净的抛物线 ✓ 不会像卡顿

        randomness = 0 就退回完全确定的老行为。
        """
        r = self.randomness
        jitter = (lambda: random.uniform(1.0 - r, 1.0 + r)) if r > 0 else (lambda: 1.0)

        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0                   # 开局竖直下落，横向速度留到第一次弹跳才给
        self.vy = 0.0
        self.first_bounce = True
        self.damage = bignum.ceil_int(bignum.parse(self.cfg.base_damage))
        # 反弹力度 —— 决定弹多高。这条最管用：高度不同就不会同时落杠
        self.bounce = float(self.cfg.bounce_speed) * jitter()
        # 横向速度的倍率 —— 决定横着跑多快
        self.speed_jitter = jitter()
        self.gravity_mult = 1.0

    def bounce_off(self) -> None:
        """撞到横杠、被弹起来。

        开局那颗球是竖直落下来的，横向往哪边走留到**第一次弹跳**才决定 ——
        左右随机，两颗球各掷各的硬币，所以不会总是往同一边跑。
        之后横向速度就固定了，只有撞到左右屏幕壁才会换向。

        `speed_x = 0` 表示这颗球永远只上下弹，不横向走。
        """
        self.vy = -self.bounce * self.scale_y
        if self.first_bounce:
            self.first_bounce = False
            speed = float(self.cfg.speed_x)
            if speed:
                # 方向左右随机，速度大小带上出生时掷的那个倍率
                self.vx = (abs(speed) * self.speed_jitter * self.scale_x
                           * random.choice((-1, 1)))
