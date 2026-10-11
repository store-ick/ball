"""
用户自定义能力算子。

这个文件在游戏启动时会被自动 import。在下面用 @register("名字") 注册新算子，
然后就能在 game.toml 里用 `on_hit = [{ op = "名字", ... }]` 调用了。

算子函数的签名是 `fn(ctx, **kwargs)`，ctx 上可以改：

    ctx.ball.damage        当前伤害（Decimal，用 bignum.parse() 转）
    ctx.ball.bounce        反弹力度（像素/秒）
    ctx.ball.gravity_mult  重力倍率
    ctx.bar.hp             被打的那根横杠的血量（Decimal）
    ctx.panel              整个面板，想干嘛都行

下面是几个示例，全部已经注册好了，直接在 toml 里写 op 名字就能用。
不想要的话把函数删掉即可。
"""

from __future__ import annotations

import decimal

import bignum
from effects import register


# ---------------------------------------------------------------------------
# 示例 1：每次撞击把横杠血量砍半（配上向下取整，避免一直卡在 1）
# ---------------------------------------------------------------------------
@register("halve_target")
def halve_target(ctx, times=1, **kw):
    for _ in range(int(times)):
        if ctx.bar.hp <= 1:
            break
        ctx.bar.hp = (ctx.bar.hp / 2).to_integral_value(rounding=decimal.ROUND_CEILING)


# ---------------------------------------------------------------------------
# 示例 2：每次撞击让球的横向速度翻倍（越撞越疯的"狂暴球"）
# ---------------------------------------------------------------------------
@register("hasten")
def hasten(ctx, value=2.0, **kw):
    ctx.ball.vx *= float(value)


# ---------------------------------------------------------------------------
# 示例 3：横杠血量是奇数就加成，偶数就减半（"奇偶球"，纯属整活）
# ---------------------------------------------------------------------------
@register("parity_chaos")
def parity_chaos(ctx, **kw):
    hp = ctx.bar.hp
    if hp != hp.to_integral_value():
        return                      # 已经不是整数了（比如被取过对数），不动它
    ctx.bar.hp = hp * 2 if int(hp) % 2 else hp / 2

#------------------------------------------------------------------------------
#翻倍：每次撞击×2
#------------------------------------------------------------------------------
@register("翻倍")                     # ← 名字随你起，中文也行
def double(ctx, times=1, **kw):       # ← 想要参数就加在这
      for _ in range(int(times)):
          ctx.ball.damage *= 2

#-------------------------------------------------------------------------------
#二向箔球
#-------------------------------------------------------------------------------
@register("二向箔")
def flatten(ctx, **kw):
    hp = ctx.bar.hp
    if hp > 0:
        # adjusted() = floor(log10(hp))，所以位数 = adjusted + 1
        ctx.bar.hp = bignum.parse(hp.adjusted() + 1)