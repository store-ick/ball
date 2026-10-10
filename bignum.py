"""
大数的表示与格式化。

横杠上的数字会大到 1E10000 这种程度，远远超出 float 的上限（约 1.8E308），
也超出 int 的合理使用范围，所以统一用 decimal.Decimal 来表示：

    * 精度 40 位有效数字（够用，且运算快）
    * 指数范围拉到 decimal 允许的最大值，1E10000 甚至 1E999999999 都不会溢出

对外的三个入口：
    parse(spec)  -> Decimal      把配置里的数字（int / float / str）转成大数
    fmt(d)       -> str          按游戏里的显示规则格式化（小数直接写，大数写科学计数法）
    log10(d)     -> Decimal      取常用对数（"对数球"要用）
"""

from __future__ import annotations

import decimal
from decimal import Decimal

# ---------------------------------------------------------------------------
# 全局精度 / 指数范围
# ---------------------------------------------------------------------------
CONTEXT = decimal.Context(
    prec=40,                       # 40 位有效数字
    Emax=decimal.MAX_EMAX,         # 指数上限拉到最大
    Emin=decimal.MIN_EMIN,
)

# 以下信号不希望它在正常游戏里抛异常（大数相减很容易不精确，这是预期内的）
for _sig in (
    decimal.Inexact,
    decimal.Rounded,
    decimal.Subnormal,
    decimal.Underflow,
    decimal.Clamped,
):
    CONTEXT.traps[_sig] = False

decimal.setcontext(CONTEXT)

ZERO = Decimal(0)
ONE = Decimal(1)


# ---------------------------------------------------------------------------
# 解析
# ---------------------------------------------------------------------------
def parse(spec) -> Decimal:
    """把配置里的数字转成 Decimal。

    支持：
        int            45
        float          1.6e9
        str            "1E10000"、"9.999E99"、"45"（超出 float 范围的必须写成字符串）
        已经是 Decimal 则原样返回
    """
    if isinstance(spec, Decimal):
        return spec
    if isinstance(spec, bool):
        raise TypeError("布尔值不能当数字用")
    if isinstance(spec, int):
        return Decimal(spec)
    if isinstance(spec, float):
        # 走 str 是为了避免二进制浮点误差被带进来
        return Decimal(repr(spec))
    if isinstance(spec, str):
        text = spec.strip().replace("^", "E")
        if not text:
            raise ValueError("空字符串不是合法数字")
        return Decimal(text)
    raise TypeError(f"无法识别的数字：{spec!r}")


# ---------------------------------------------------------------------------
# 格式化
# ---------------------------------------------------------------------------
# 十进制位数小于这个值就直接写完整数字，否则写科学计数法。
# 例如 1600000000（1.6E9）直接写，1E10 写成 "1E10"。
FULL_DIGIT_LIMIT = 10

# 科学计数法保留几位小数（4 位有效数字，对应截图里的 "9.999E99"）
SCI_FRACTION_DIGITS = 3


def fmt(value: Decimal) -> str:
    """按游戏里的习惯格式化一个数。

    这里**不做取整** —— 取整在数据产生的地方就做完了（横杠向下、伤害向上）。
    显示层再取一次的话，就会出现"屏幕显示 0 但其实还有 0.0413"这种对不上的情况。
    """
    if value == 0:
        return "0"

    negative = value < 0
    d = -value if negative else value
    sign = "-" if negative else ""

    exp10 = d.adjusted()          # floor(log10(d))

    if exp10 < FULL_DIGIT_LIMIT:
        # 小数字：完整写出来，去掉多余的 0
        text = format(d, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return sign + text

    # 大数字：写成 m.mmmE±n
    mantissa = d.scaleb(-exp10)   # 落到 [1, 10)
    quant = Decimal(1).scaleb(-SCI_FRACTION_DIGITS)
    m = mantissa.quantize(quant, rounding=decimal.ROUND_HALF_UP)
    if m >= 10:                   # 9.9996 -> 10.000，要进位
        m = m.scaleb(-1)
        exp10 += 1

    if m == 1:
        body = "1"
    else:
        body = format(m, "f").rstrip("0").rstrip(".")

    return f"{sign}{body}E{exp10}"


def log10(value: Decimal) -> Decimal:
    """常用对数。非正数直接返回 0（横杠血量打完就不该再取对数了）。"""
    if value <= 0:
        return ZERO
    return value.log10()


def floor_int(value: Decimal) -> Decimal:
    """向下取整到整数。给"横杠血量"这类要被打掉的目标数字用。

    指数 >= 0 的数（1E10000 这种）本来就是整数，原样返回，不会展开成超大整数。
    """
    if value.as_tuple().exponent >= 0:
        return value
    return value.to_integral_value(rounding=decimal.ROUND_FLOOR)


def ceil_int(value: Decimal) -> Decimal:
    """向上取整到整数。给"球的伤害"这类增益数字用。

    伤害要是向下取整，`×0.5` 这种就会把球归零、直接废掉；
    向上取整最多是"不亏"，不会把一颗球算死。
    """
    if value.as_tuple().exponent >= 0:
        return value
    return value.to_integral_value(rounding=decimal.ROUND_CEILING)


def is_zero(value: Decimal) -> bool:
    return value <= 0
