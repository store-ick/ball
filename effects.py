"""
"球的撞击能力"算子表。

设计目标：配置文件里只写"名字 + 参数"的纯数据，
        想加真正奇怪的能力时再到 custom_effects.py 里注册一个 Python 函数。

配置文件里这样写：

    on_hit = [{ op = "add_damage", value = 1 }]

每一次球撞到横杠、结算完本次伤害之后，会按顺序调用这些算子。
算子拿到的 ctx 上有三样东西可以随便改：

    ctx.ball.damage        球的当前伤害（Decimal）
    ctx.ball.bounce        球的反弹力度（像素/秒，撞一下弹多高由它决定）
    ctx.ball.gravity_mult  球受到的"重力倍率"（1.0 = 全局重力，0.5 = 半个重力）
    ctx.bar.hp             当前被打的那根横杠的血量（Decimal）

想加新算子，在 custom_effects.py 里：

    from effects import register

    @register("反物质")
    def annihilate(ctx, **kw):
        ctx.bar.hp = 0
"""

from __future__ import annotations

import math
from typing import Callable, Dict

import bignum
import dots
from bignum import Decimal

# 名字 -> 函数
REGISTRY: Dict[str, Callable] = {}


class EffectContext:
    """传给算子的上下文。字段故意做得简单，方便用户自己加。"""

    __slots__ = ("ball", "bar", "panel", "dealt")

    def __init__(self, ball, bar, panel, dealt=0):
        self.ball = ball
        self.bar = bar
        self.panel = panel
        # 这一次撞击实际打掉了多少血（吸血类算子要用）
        self.dealt: Decimal = dealt


def register(name: str):
    """注册一个算子。重名会覆盖，方便用户在 custom_effects.py 里改写内置行为。"""
    def deco(fn: Callable) -> Callable:
        REGISTRY[name] = fn
        return fn
    return deco


def apply_all(ops, ctx: EffectContext) -> None:
    """按顺序执行一组算子。遇到没注册的名字只警告，不打断游戏。"""
    for spec in ops or ():
        if not isinstance(spec, dict):
            print(f"[effects] 忽略非法的能力项：{spec!r}")
            continue
        name = spec.get("op")
        kwargs = {k: v for k, v in spec.items() if k != "op"}
        fn = REGISTRY.get(name)
        if fn is None:
            print(f"[effects] 未注册的算子 '{name}'，已跳过")
            continue
        fn(ctx, **kwargs)


# ---------------------------------------------------------------------------
# ── 修改"球"的内置算子 ──
# ---------------------------------------------------------------------------

@register("add_damage")
def _add_damage(ctx, value=1, **kw):
    """每次撞击后攻击力 +value。"""
    ctx.ball.damage += bignum.parse(value)


@register("mul_damage")
def _mul_damage(ctx, value=2, **kw):
    """每次撞击后攻击力 ×value。"""
    ctx.ball.damage *= bignum.parse(value)


@register("set_damage")
def _set_damage(ctx, value=1, **kw):
    """每次撞击后把攻击力直接设成 value。"""
    ctx.ball.damage = bignum.parse(value)


@register("scale_bounce")
def _scale_bounce(ctx, value=1.0, **kw):
    """反弹力度乘以 value（>1 弹更高，<1 弹更低）。"""
    ctx.ball.bounce *= float(value)


@register("set_bounce")
def _set_bounce(ctx, value=0.0, **kw):
    """把反弹力度设成固定值（像素/秒）。"""
    ctx.ball.bounce = float(value)


@register("set_gravity_mult")
def _set_gravity_mult(ctx, value=1.0, **kw):
    """设球受到的重力倍率。0 就是失重（球会一直飘）。"""
    ctx.ball.gravity_mult = float(value)


@register("scale_gravity_mult")
def _scale_gravity_mult(ctx, value=1.0, **kw):
    """重力倍率乘以 value。"""
    ctx.ball.gravity_mult *= float(value)


# ---------------------------------------------------------------------------
# ── 修改"横杠"的内置算子 ──
# ---------------------------------------------------------------------------

@register("target_log")
def _target_log(ctx, **kw):
    """对数球：把横杠的数字取常用对数。1E10000 -> 10000。"""
    ctx.bar.hp = bignum.log10(ctx.bar.hp)


@register("target_scale")
def _target_scale(ctx, value=1.0, **kw):
    """把横杠血量乘以 value。"""
    ctx.bar.hp *= bignum.parse(value)


@register("target_add")
def _target_add(ctx, value=1, **kw):
    """给横杠回血 value。"""
    ctx.bar.hp += bignum.parse(value)


@register("target_set")
def _target_set(ctx, value=0, **kw):
    """把横杠血量直接设成 value。"""
    ctx.bar.hp = bignum.parse(value)


@register("annihilate")
def _annihilate(ctx, **kw):
    """反物质球：碰到的横杠直接湮灭。"""
    ctx.bar.hp = bignum.ZERO


# ---------------------------------------------------------------------------
# ── 持续伤害 ──
# ---------------------------------------------------------------------------

@register("dot")
def _dot(ctx, name="持续伤害", base=0, percent=0, stacks=1, life=0.0,
         color=None, **kw):
    """给横杠挂一层持续伤害，每秒结算一次。同名的叠层数。

    中毒球就是这个：
        on_hit = [{ op = "dot", name = "中毒", base = 1, percent = 1 }]
    撞一次挂一层，之后每秒扣「层数% × 当前血量 + 1」。

    percent 每层每秒扣当前血量的百分之几；base 是每秒的固定伤害。
    life = 持续几秒（0 = 永久，直到横杠被打死）。
    """
    dots.add_dot(ctx.bar, dots.Dot(
        name=name, base=base, percent=percent,
        stacks=stacks, life=life,
        color=color or (150, 60, 200),
    ))


# ---------------------------------------------------------------------------
# ── 大数算子（用对数空间，不然会爆炸）──
# ---------------------------------------------------------------------------

# log10(e)，斯特林公式要用
_LOG10_E = Decimal("0.4342944819032518276511289189166050822943970058036665661144")
# 十进制能表示的指数上限在 1e18 附近，留点余量
_MAX_LOG10 = Decimal(10) ** 17


def _log10_factorial(n: Decimal) -> Decimal:
    """log10(n!)，全程在对数空间算 —— 绝不真的去算那个天文长度的整数。"""
    f = float(n)
    if f < 1e300:
        # 小到能塞进 float：lgamma 直接给 ln(n!)，精确
        return Decimal(repr(math.lgamma(f + 1.0) / math.log(10.0)))
    # 大到 float 都装不下：斯特林级数
    #   log10(n!) ≈ n·log10(n) − n·log10(e) + 0.5·log10(n)
    lg = n.log10()
    return n * lg - n * _LOG10_E + lg / 2


def _from_log10(lg: Decimal) -> Decimal:
    """把 log10 还原成一个数。超出十进制能表示的范围就顶格。"""
    if lg <= 0:
        return bignum.ONE
    if lg > _MAX_LOG10:
        return Decimal(1).scaleb(int(_MAX_LOG10))
    return Decimal(10) ** lg


# 这个范围以内直接算精确的阶乘。20000! 大约 7 万位，算得动而且不慢。
_EXACT_FACTORIAL_LIMIT = 20000


@register("factorial")
def _factorial(ctx, **kw):
    """阶乘球：把当前攻击力换成它的阶乘。3 → 3! = 6 → 6! = 720 → 720! → …

    分两段：
      - 小数字（≤20000）直接算**精确值** —— 走对数空间会丢精度
        （3! 会变成 6.0000000000000009 那种）
      - 大数字只能在对数空间算：720! 已经是 1747 位数，
        再阶乘一次就是 10^(1.7×10^1749) 这个量级，真的算不出来
    超过十进制能表示的上限就顶格 —— 反正到那个量级没东西扛得住。
    """
    n = ctx.ball.damage
    if n <= 1:
        return

    if n <= _EXACT_FACTORIAL_LIMIT:
        ctx.ball.damage = Decimal(math.factorial(int(n)))
    else:
        ctx.ball.damage = _from_log10(_log10_factorial(n))


@register("square_damage")
def _square_damage(ctx, **kw):
    """平方球：攻击力自乘。3 → 9 → 81 → 6561 → …（涨得比阶乘慢得多）"""
    ctx.ball.damage = ctx.ball.damage * ctx.ball.damage


@register("drain")
def _drain(ctx, value=1.0, **kw):
    """吸血球：把这次从横杠身上打掉的血，按比例加到自己攻击力上。

    value = 1.0 就是"打多少吸多少"（守恒球）；0.5 是吸一半。
    """
    if ctx.dealt > 0:
        ctx.ball.damage += Decimal(str(float(value))) * ctx.dealt
