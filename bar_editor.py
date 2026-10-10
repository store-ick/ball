"""
横杠编辑器 —— 开局前可视化地安排左右两屏的横杠。

    鼠标   点一行选中它；点「加一根 / 删一根」调条数
    键盘   ↑ / ↓ 在当前列里换行
           Tab / ← / → 在左右两屏之间切换
           数字键 / . / E 输入数字（支持科学计数法，比如 1E10000）
           Backspace 删一个字符，Enter 确认这一行
           Esc 取消当前编辑，再按一次返回选球界面

条数是左右**共用**的（这样两边行位置才对得齐），所以"加一根"两边一起加。
数字则是左右**分别**定义的。

改完的内容只对本次运行有效，不会写回配置文件。
"""

from __future__ import annotations

import asyncio
from typing import List, Optional

import pygame

import bignum
import config as config_mod
import render
import theme as T
from config import GameConfig

ROW_H = 40
ROW_STEP = 48
IDX_W = 34          # 行号占的宽度
BTN_H = 36
ADD_DEFAULT = 10    # 新加一根的默认血量

_ALLOWED = set("0123456789.eE+-^")


class _Column:
    def __init__(self, rect, title: str, bars: List[str]):
        self.rect = tuple(rect)
        self.title = title
        self.bars = bars            # 直接引用 cfg.panels[i].bars（就地改，改完立刻生效）

        # 配置里可能是 int / 浮点 / 字符串，统一归一化成规范字符串，
        # 顺便让"9727 -> 9727"、"1.6e9 -> 1600000000"这种写法显示一致
        for i, raw in enumerate(bars):
            try:
                bars[i] = bignum.fmt(bignum.parse(raw))
            except Exception:
                bars[i] = str(raw)

        self.index = 0
        self.offset = 0
        self.buffer: Optional[str] = None    # 非 None = 正在编辑
        self.fresh = False                   # True = 还没动过，下一次按键替换整段
        self.row_rects: List[tuple] = []

    @property
    def editing(self) -> bool:
        return self.buffer is not None

    def begin_edit(self) -> None:
        if self.bars:
            self.buffer = str(self.bars[self.index])
            self.fresh = True

    def cancel_edit(self) -> None:
        self.buffer = None
        self.fresh = False

    def commit_edit(self) -> None:
        """把输入框里的东西写回去。解析不了（或者空了）就当作取消。"""
        if self.buffer is None or not self.bars:
            return
        text = self.buffer.strip()
        self.buffer = None
        self.fresh = False
        if not text:
            return
        try:
            value = bignum.parse(text)
        except Exception:
            return                    # 解析失败就保留原来的值
        if value < 0:
            value = bignum.ZERO
        self.bars[self.index] = bignum.fmt(value)

    def type_char(self, ch: str) -> None:
        """敲进一个字符。刚点开还没动过的话，第一个字符把旧值整个替换掉。"""
        if not self.editing:
            self.begin_edit()
        if self.fresh:
            self.buffer = ch
            self.fresh = False
        else:
            self.buffer = (self.buffer or "") + ch

    def backspace(self) -> None:
        if not self.editing:
            self.begin_edit()
        if self.fresh:
            self.buffer = ""
            self.fresh = False
        elif self.buffer:
            self.buffer = self.buffer[:-1]

    def move(self, delta: int) -> None:
        if self.bars:
            self.commit_edit()
            self.index = (self.index + delta) % len(self.bars)

    def row_at(self, pos) -> Optional[int]:
        for i, rect in enumerate(self.row_rects):
            if T.in_rect(pos, rect):
                return self.offset + i
        return None


def add_button_rect(width: int, height: int) -> tuple:
    y = height - T.HINT_H + (T.HINT_H - BTN_H) // 2
    return (T.PAD, y, 132, BTN_H)


def del_button_rect(width: int, height: int) -> tuple:
    x, y, w, h = add_button_rect(width, height)
    return (x + w + 10, y, 132, h)


def _apply_count(cfg: GameConfig, delta: int) -> None:
    """加减横杠条数。左右共用，所以两边一起变。"""
    panels = cfg.panels
    if delta > 0:
        for p in panels:
            p.bars.append(ADD_DEFAULT)
        cfg.glob.bar_count += 1
    elif delta < 0 and cfg.glob.bar_count > 1:
        for p in panels:
            if p.bars:
                p.bars.pop()
        cfg.glob.bar_count -= 1


def _draw_column(screen, col: _Column, active: bool, height: int,
                 hover_index: Optional[int]) -> None:
    x, y, w, h = col.rect
    inner_x = x + T.PAD
    inner_w = w - T.PAD * 2

    T.heading(screen, inner_x, y + 26, inner_w, col.title, active=active,
              right=f"{len(col.bars)} 根")

    list_top = y + 96
    list_bottom = height - T.HINT_H - 24
    visible = max(1, (list_bottom - list_top + (ROW_STEP - ROW_H)) // ROW_STEP)

    col.offset = max(0, min(col.offset, max(0, len(col.bars) - visible)))
    if col.index < col.offset:
        col.offset = col.index
    elif col.index >= col.offset + visible:
        col.offset = col.index - visible + 1

    col.row_rects = []
    for k in range(visible):
        idx = col.offset + k
        if idx >= len(col.bars):
            break
        ry = list_top + k * ROW_STEP
        full = (inner_x, ry, inner_w, ROW_H)
        col.row_rects.append(full)

        # 行号：左边一小列，弱化
        render.draw_text(screen, str(idx + 1), size=T.S_CAPTION, color=T.INK_3,
                         center=(inner_x + IDX_W // 2, ry + ROW_H // 2))

        bar_rect = (inner_x + IDX_W, ry, inner_w - IDX_W, ROW_H)
        selected = idx == col.index
        if selected and active:
            if col.editing:
                T.bar_row(screen, bar_rect, col.buffer, mode="edit",
                          caret=True, size=T.S_BODY)
            else:
                T.bar_row(screen, bar_rect, col.bars[idx], mode="edit", size=T.S_BODY)
        else:
            T.bar_row(screen, bar_rect, col.bars[idx], mode="filled", size=T.S_BODY,
                      hovered=(hover_index == idx))

    if not col.bars:
        render.draw_text(screen, "还没有横杠，点下面「加一根」", size=T.S_BODY,
                         color=T.INK_3, topleft=(inner_x, list_top + 8))


def draw_frame(screen, columns: List[_Column], active: int, width: int, height: int,
               mouse_pos=(0, 0), hover_rows=None, hover_add: bool = False,
               hover_del: bool = False) -> None:
    screen.fill(T.PAPER)

    # 竖线宽度 = 相邻两列之间实际留出的空隙（跟着窗口走）
    for i in range(1, len(columns)):
        left_col = columns[i - 1].rect
        divider = columns[i].rect[0] - (left_col[0] + left_col[2])
        if divider > 0:
            pygame.draw.rect(screen, T.INK, (columns[i].rect[0] - divider, 0, divider, height))

    for i, col in enumerate(columns):
        hover = hover_rows[i] if hover_rows else None
        _draw_column(screen, col, i == active, height, hover)

    editing = next((c for c in columns if c.editing), None)
    if editing is not None:
        hint = f"正在输入 {editing.buffer or '·'}    Enter 确认    Esc 取消"
        T.hint_bar(screen, width, height, hint, accent=True)
    else:
        T.hint_bar(screen, width, height,
                   "点一行改数字      Enter 确认      Tab 换屏      Esc 返回")

    T.button(screen, add_button_rect(width, height), "+ 加一根", hovered=hover_add)
    T.button(screen, del_button_rect(width, height), "− 删一根", hovered=hover_del)
    render.draw_text(screen, "左右共用", size=T.S_CAPTION, color=T.INK_3,
                     midleft=(del_button_rect(width, height)[0]
                              + del_button_rect(width, height)[2] + 14,
                              height - T.HINT_H + T.HINT_H // 2))


async def run(screen, cfg: GameConfig, active: Optional[List[int]] = None) -> None:
    """跑横杠编辑器。改的是 cfg.panels[i].bars 和 cfg.glob.bar_count，就地生效。

    `active` 是要显示哪几屏（切了单屏就只显示那一屏）。条数是全局共用的，
    所以增删行会影响所有屏，不只是显示出来的这些。
    """
    g = cfg.glob
    size = screen.get_size()
    width, height = size
    if active is None:
        active = list(range(len(cfg.panels)))

    def titles_and_rects(size_):
        rects = config_mod.panel_rects(cfg, size_, count=len(active))
        out = []
        for k, idx in enumerate(active):
            pcfg = cfg.panels[idx]
            title = pcfg.title or ("左屏" if idx == 0 else ("右屏" if idx == 1 else f"第 {idx + 1} 屏"))
            out.append((title, pcfg, rects[k]))
        return out

    columns: List[_Column] = [
        _Column(rect, title, pcfg.bars) for title, pcfg, rect in titles_and_rects(size)
    ]

    active = 0
    clock = pygame.time.Clock()
    mouse_pos = (0, 0)
    hover_rows: List[Optional[int]] = [None] * len(columns)
    hover_add = hover_del = False

    def refresh_hover() -> None:
        nonlocal hover_add, hover_del
        for i, col in enumerate(columns):
            hover_rows[i] = col.row_at(mouse_pos)
        hover_add = T.in_rect(mouse_pos, add_button_rect(width, height))
        hover_del = T.in_rect(mouse_pos, del_button_rect(width, height))

    while True:
        # 窗口被拖动了 -> 按新尺寸重算各列的位置
        new_size = screen.get_size()
        if new_size != size:
            size = new_size
            width, height = size
            for col, rect in zip(columns, config_mod.panel_rects(cfg, size, count=len(active))):
                col.rect = rect
            refresh_hover()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return

            if e.type == pygame.MOUSEMOTION:
                mouse_pos = e.pos
                refresh_hover()

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_pos = e.pos
                refresh_hover()
                if hover_add:
                    for col in columns:
                        col.commit_edit()
                    _apply_count(cfg, +1)
                elif hover_del:
                    for col in columns:
                        col.commit_edit()
                    _apply_count(cfg, -1)
                else:
                    for i, col in enumerate(columns):
                        idx = col.row_at(e.pos)
                        if idx is not None:
                            for c in columns:
                                if c is not col:
                                    c.commit_edit()
                            active = i
                            col.index = idx
                            col.begin_edit()
                            break
                refresh_hover()

            elif e.type == pygame.KEYDOWN:
                col = columns[active]
                if e.key == pygame.K_ESCAPE:
                    if col.editing:
                        col.cancel_edit()
                    else:
                        for c in columns:
                            c.commit_edit()
                        return
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    col.commit_edit()
                    col.move(1)
                elif e.key == pygame.K_BACKSPACE:
                    col.backspace()
                elif e.key in (pygame.K_UP, pygame.K_w):
                    col.move(-1)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    col.move(1)
                elif e.key == pygame.K_TAB:
                    col.commit_edit()
                    active = (active + 1) % len(columns)
                elif e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    col.commit_edit()
                    step = -1 if e.key == pygame.K_LEFT else 1
                    active = (active + step) % len(columns)
                else:
                    ch = getattr(e, "unicode", "")
                    if ch and ch in _ALLOWED:
                        col.type_char(ch)
                refresh_hover()

        draw_frame(screen, columns, active, width, height,
                   mouse_pos, hover_rows, hover_add, hover_del)
        pygame.display.flip()
        clock.tick(g.fps)
        await asyncio.sleep(0)      # pygbag 必需：每帧让出控制权
