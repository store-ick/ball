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

from typing import Callable, Dict

import bignum

# 名字 -> 函数
REGISTRY: Dict[str, Callable] = {}


class EffectContext:
    """传给算子的上下文。字段故意做得简单，方便用户自己加。"""

    __slots__ = ("ball", "bar", "panel")

    def __init__(self, ball, bar, panel):
        self.ball = ball
        self.bar = bar
        self.panel = panel


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
