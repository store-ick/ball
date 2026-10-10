"""
界面配色和共用的绘制件。

选球页和横杠编辑器共用这一套，视觉语言跟游戏本体是一致的：
纯白纸面、黑色横杠、白字，红色只用来表示"焦点"（当前操作的那一屏 / 正在编辑的那一行）。

核心想法很简单：这个游戏的样子就是"刻度板上的横杠"，
所以列表里的每一行也做成一根横杠 —— 选中就是把这一根"上墨"。
"""

from __future__ import annotations

import pygame

import render

# ── 配色 ──────────────────────────────────────────────────────────────────
PAPER = (255, 255, 255)     # 纸面
INK = (10, 10, 10)          # 墨：横杠、主文字
INK_2 = (110, 110, 110)     # 次级文字（描述）
INK_3 = (170, 170, 170)     # 弱化信息（序号、计数）
RULE = (233, 233, 233)      # 细分隔线
RULE_2 = (205, 205, 205)    # 稍重的分隔线
HOVER = (245, 245, 245)     # 鼠标悬停底
ACCENT = (222, 58, 58)      # 唯一的强调色（就是球的那个红）

# ── 字号阶 ────────────────────────────────────────────────────────────────
S_DISPLAY = 30              # 球名
S_TITLE = 24                # 列标题 / 按钮
S_BODY = 19                 # 描述
S_CAPTION = 16              # 提示、计数

# ── 量 ────────────────────────────────────────────────────────────────────
PAD = 24                    # 列内左右留白
HINT_H = 58                 # 底部操作条高度


# ── 绘制件 ────────────────────────────────────────────────────────────────
def heading(surface, x: int, y: int, w: int, text: str,
            *, active: bool = False, right: str = "") -> int:
    """列标题 + 一条横线。当前操作的那一列标题用强调色、横线也变粗变红。

    返回横线的 y，方便下面接着排版。
    """
    color = ACCENT if active else INK
    render.draw_text(surface, text, size=S_TITLE, color=color, topleft=(x, y))
    if right:
        render.draw_text(surface, right, size=S_CAPTION, color=INK_3,
                         topright=(x + w, y + 8))
    line_y = y + 40
    pygame.draw.line(surface, ACCENT if active else RULE_2,
                     (x, line_y), (x + w, line_y), 3 if active else 1)
    return line_y


def bar_row(surface, rect, label: str, *, mode: str = "idle",
            hovered: bool = False, size: int | None = None,
            caret: bool = False) -> None:
    """把一行画成一根"横杠"。

    mode:
        idle     空槽 —— 只有上下两条细线，像刻度尺上还没刻的格子
        filled   实心黑 + 白字，跟游戏里的横杠一模一样（选中的那一行）
        outline  空心 —— 黑框白底。非焦点屏里的选中项，跟 filled 区分开
        edit     正在编辑 —— 强调色描边
    """
    x, y, w, h = rect
    size = size or min(S_DISPLAY, max(16, h - 14))
    label = str(label)

    if mode == "filled":
        pygame.draw.rect(surface, INK, rect)
        if hovered:
            pygame.draw.rect(surface, ACCENT, rect, 2)
        color = PAPER
    elif mode == "outline":
        pygame.draw.rect(surface, PAPER, rect)
        pygame.draw.rect(surface, INK, rect, 2)
        color = INK
    else:
        if hovered or mode == "edit":
            pygame.draw.rect(surface, HOVER, rect)
        pygame.draw.line(surface, RULE, (x, y), (x + w, y), 1)
        pygame.draw.line(surface, RULE, (x, y + h - 1), (x + w, y + h - 1), 1)
        color = INK
        if mode == "edit":
            pygame.draw.rect(surface, ACCENT, rect, 2)

    if caret:
        # 正在输入的文本框：文字左对齐，后面跟一根光标
        tx = x + 14
        render.draw_text(surface, label, size=size, color=color, midleft=(tx, y + h // 2))
        tw = render.text_size(label, size)[0] if label else 0
        cx = tx + tw + 2
        pygame.draw.line(surface, ACCENT, (cx, y + 9), (cx, y + h - 9), 2)
    else:
        render.draw_text(surface, label, size=size, color=color,
                         center=(x + w // 2, y + h // 2))


def button(surface, rect, label: str, *, hovered: bool = False,
           primary: bool = False) -> None:
    """一个按钮。primary 用实心黑/强调色，其余用描边。"""
    x, y, w, h = rect
    if primary:
        pygame.draw.rect(surface, ACCENT if hovered else INK, rect)
        color = PAPER
    else:
        pygame.draw.rect(surface, HOVER if hovered else PAPER, rect)
        pygame.draw.rect(surface, INK if hovered else RULE_2, rect, 2)
        color = INK
    size = render.fit_size(label, w - 18, S_BODY, minimum=13)
    render.draw_text(surface, label, size=size, color=color,
                     center=(x + w // 2, y + h // 2))


def hint_bar(surface, width: int, height: int, text: str, *, align: str = "right",
             accent: bool = False) -> int:
    """底部那条操作提示的横线和文字。返回这条的顶部 y。

    默认右对齐 —— 左下角通常留给按钮，居中的话会被中间的竖线切断。
    """
    top = height - HINT_H
    pygame.draw.line(surface, RULE, (0, top), (width, top), 1)
    if not text:
        return top
    kwargs = {}
    if align == "right":
        kwargs["topright"] = (width - PAD, top + (HINT_H - S_CAPTION) // 2 - 4)
    else:
        kwargs["topleft"] = (PAD, top + (HINT_H - S_CAPTION) // 2 - 4)
    render.draw_text(surface, text, size=S_CAPTION,
                     color=ACCENT if accent else INK_3, **kwargs)
    return top


def in_rect(pos, rect) -> bool:
    x, y, w, h = rect
    return x <= pos[0] < x + w and y <= pos[1] < y + h
