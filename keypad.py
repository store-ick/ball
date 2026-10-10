"""
屏幕数字键盘 —— 给"要填数字"的地方用。

为什么需要它：
    手机上打不出 1E10000 这种数字（没有物理键盘），而横杠血量、球的伤害、
    反弹力度这些都要填数字。原来横杠编辑器靠键盘敲，手机上就废了。

设计成**两种输入都支持**：
    键盘   直接打字     （桌面快）
    触摸   点屏幕按键   （手机用）
同一份代码两端都能用，不用判断平台 —— 这比"手机上显示键盘、桌面上不显示"
更省事，而且桌面上鼠标点按键也能用。

用法（在 async 循环里）：
    text = await ask(screen, "横杠血量", initial="9727")
    if text is None:      # 用户取消了
        ...
"""

from __future__ import annotations

import asyncio

import pygame

import render
import theme as T

# 允许敲进去的字符。跟原来横杠编辑器那套一致
ALLOWED = set("0123456789.eE+-^")

# 键盘布局（4x4）。(按键文字, 动作)
#   动作以 ":" 开头的是命令，其余是往输入框里加字符
_LAYOUT = [
    [("1", "1"), ("2", "2"), ("3", "3"), ("退格", ":back")],
    [("4", "4"), ("5", "5"), ("6", "6"), ("清空", ":clear")],
    [("7", "7"), ("8", "8"), ("9", "9"), ("取消", ":cancel")],
    [(".", "."), ("0", "0"), ("E", "E"), ("确定", ":ok")],
]

# 这几个键用强调色，一眼能找到
_ACCENT_KEYS = {":ok", ":cancel"}


class NumericKeypad:
    def __init__(self, title: str, initial: str = "", max_len: int = 24):
        self.title = title
        self.text = initial
        self.max_len = max_len
        self.done = False
        self.cancelled = False
        # 刚打开还没动过 —— 第一次按键把旧值整段替换掉（跟原来横杠编辑器一致）
        self.fresh = bool(initial)
        self.buttons: list = []          # 每帧算出来，给点击命中用

    # ------------------------------------------------------------------
    def type_char(self, ch: str) -> None:
        if self.fresh:
            self.text = ch
            self.fresh = False
        elif len(self.text) < self.max_len:
            self.text += ch

    def backspace(self) -> None:
        if self.fresh:
            self.text = ""
            self.fresh = False
        else:
            self.text = self.text[:-1]

    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type == pygame.QUIT:
            self.cancelled, self.done = True, True
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.cancelled, self.done = True, True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.done = True
            elif event.key == pygame.K_BACKSPACE:
                self.backspace()
            else:
                ch = getattr(event, "unicode", "")
                if ch and ch in ALLOWED:
                    self.type_char(ch)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.buttons:
                if T.in_rect(event.pos, rect):
                    if action == ":ok":
                        self.done = True
                    elif action == ":cancel":
                        self.cancelled, self.done = True, True
                    elif action == ":clear":
                        self.text, self.fresh = "", False
                    elif action == ":back":
                        self.backspace()
                    else:
                        self.type_char(action)
                    return

    # ------------------------------------------------------------------
    def draw(self, screen) -> None:
        width, height = screen.get_size()

        # 半透明黑罩住整个屏幕，让键盘跳出来
        veil = pygame.Surface((width, height))
        veil.set_alpha(140)
        veil.fill((0, 0, 0))
        screen.blit(veil, (0, 0))

        # 键盘面板：跟着屏幕走，手机竖屏也不会溢出
        pw = min(width - 40, 660)
        ph = min(height - 60, 760)
        px = (width - pw) // 2
        py = (height - ph) // 2
        pygame.draw.rect(screen, (255, 255, 255), (px, py, pw, ph))
        pygame.draw.rect(screen, (10, 10, 10), (px, py, pw, ph), 3)

        pad = 24
        inner_x = px + pad
        inner_w = pw - pad * 2

        # 标题
        render.draw_text(screen, self.title, size=30, color=(10, 10, 10),
                         topleft=(inner_x, py + 20))

        # 输入框
        box_y = py + 72
        box_h = 74
        pygame.draw.rect(screen, (247, 247, 247), (inner_x, box_y, inner_w, box_h))
        pygame.draw.rect(screen, (10, 10, 10), (inner_x, box_y, inner_w, box_h), 2)
        shown = self.text or "（点下面的键输入）"
        color = (10, 10, 10) if self.text else (175, 175, 175)
        size = render.fit_size(shown, inner_w - 28, 36, minimum=18)
        render.draw_text(screen, shown, size=size, color=color,
                         midleft=(inner_x + 14, box_y + box_h // 2))

        # 键盘网格
        grid_y = box_y + box_h + 24
        grid_h = py + ph - pad - grid_y
        cols, rows = 4, 4
        gap = 10
        bw = (inner_w - gap * (cols - 1)) // cols
        bh = (grid_h - gap * (rows - 1)) // rows

        self.buttons = []
        for r, row in enumerate(_LAYOUT):
            for c, (label, action) in enumerate(row):
                rect = (inner_x + c * (bw + gap), grid_y + r * (bh + gap), bw, bh)
                self.buttons.append((rect, action))
                if action in _ACCENT_KEYS:
                    fill = (222, 58, 58) if action == ":ok" else (235, 235, 235)
                    color = (255, 255, 255) if action == ":ok" else (10, 10, 10)
                    pygame.draw.rect(screen, fill, rect)
                else:
                    pygame.draw.rect(screen, (255, 255, 255), rect)
                    pygame.draw.rect(screen, (10, 10, 10), rect, 2)
                    color = (10, 10, 10)
                fsize = render.fit_size(label, bw - 16, 34, minimum=16)
                render.draw_text(screen, label, size=fsize, color=color,
                                 center=(rect[0] + bw // 2, rect[1] + bh // 2))


async def ask(screen, title: str, initial: str = "") -> str | None:
    """弹出数字键盘，等用户输入完。

    返回：输入的内容；用户按取消 / Esc / 关窗口则返回 None。
    """
    kpd = NumericKeypad(title, str(initial))
    clock = pygame.time.Clock()
    while not kpd.done:
        for event in pygame.event.get():
            kpd.handle_event(event)
        kpd.draw(screen)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
    return None if kpd.cancelled else kpd.text
