"""
开局选球界面。

左右两屏各一列，同屏一起选。鼠标和键盘都能用：

    鼠标   悬停高亮，点一下选中，点左下角「编辑横杠」进编辑器
    键盘   ↑ / ↓ 在当前列里上下移
           Tab / ← / → 在左右两列之间切换
           Enter / 空格 开始游戏
           E 进横杠编辑器
           Esc 退出

每一行都做成一根"横杠"：选中的那根"上墨"变成实心黑，没选中的是空槽。
当前操作的那一列标题用强调色，另一列里的选中项画成空心 —— 一眼看出焦点在哪。

哪一屏在关卡配置里写死了球，那一列就锁住、不参与选择。
"""

from __future__ import annotations

from typing import List, Optional

import pygame

import config as config_mod
import render
import theme as T
from config import BallCfg, GameConfig

ROW_H = 44          # 每一行（一根横杠）的高度
ROW_GAP = 8
ROW_STEP = ROW_H + ROW_GAP
DESC_RESERVE = 132  # 列表下面留给描述的高度
BTN_H = 36
LOCK_NAME_SIZE = 34

# 这些标点不允许出现在行首，宁可让这一行稍微超一点点
_NO_LINE_START = "。，、！？：；）】》」』…—·%,.!?:;)]}"


class _Column:
    def __init__(self, rect, title: str, roster: List[BallCfg],
                 pinned_ball: Optional[BallCfg] = None, is_pinned: bool = False):
        self.rect = tuple(rect)
        self.title = title
        self.roster = roster
        self.pinned = pinned_ball
        self.locked = is_pinned       # 配置里写死了球 -> 这一列不让选
        self.offset = 0
        self.row_rects: List[tuple] = []   # 每帧算出来的行矩形，给鼠标命中用

        # 初始高亮：如果这一屏上次选过球，就停在那一颗上，省得每次重挑
        self.index = 0
        if not self.locked and roster:
            names = [b.name for b in roster]
            if pinned_ball is not None and pinned_ball.name in names:
                self.index = names.index(pinned_ball.name)

    @property
    def selectable(self) -> bool:
        return not self.locked and bool(self.roster)

    @property
    def current(self) -> Optional[BallCfg]:
        if self.locked:
            return self.pinned
        if not self.roster:
            return None
        return self.roster[self.index]

    def move(self, delta: int) -> None:
        if self.selectable:
            self.index = (self.index + delta) % len(self.roster)

    def row_at(self, pos) -> Optional[int]:
        """鼠标落在第几行上（返回 roster 里的下标）。"""
        for i, rect in enumerate(self.row_rects):
            if T.in_rect(pos, rect):
                return self.offset + i
        return None


def _wrap(text: str, size: int, max_width: int, max_lines: int = 3) -> List[str]:
    """按宽度折行。中文按字折就够了，顺带不让标点掉到行首。"""
    f = render.font(size)
    lines: List[str] = []
    cur = ""
    for ch in text:
        if cur and ch not in _NO_LINE_START and f.size(cur + ch)[0] > max_width:
            lines.append(cur)
            cur = ch
            if len(lines) == max_lines:
                return lines
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def _draw_column(screen, col: _Column, active: bool, height: int,
                 hover_index: Optional[int]) -> None:
    x, y, w, h = col.rect
    inner_x = x + T.PAD
    inner_w = w - T.PAD * 2

    counter = f"{col.index + 1}/{len(col.roster)}" if col.roster and col.selectable else ""
    T.heading(screen, inner_x, y + 26, inner_w, col.title, active=active, right=counter)

    if col.locked:
        render.draw_text(screen, col.pinned.name, size=LOCK_NAME_SIZE, color=T.INK,
                         topleft=(inner_x, y + 132))
        render.draw_text(screen, "这一屏在配置里写死了球", size=T.S_BODY,
                         color=T.INK_3, topleft=(inner_x, y + 184))
        return

    list_top = y + 96
    list_bottom = height - T.HINT_H - DESC_RESERVE
    visible = max(1, (list_bottom - list_top + ROW_GAP) // ROW_STEP)

    # 滚动：保证选中的那个永远看得见
    col.offset = max(0, min(col.offset, max(0, len(col.roster) - visible)))
    if col.index < col.offset:
        col.offset = col.index
    elif col.index >= col.offset + visible:
        col.offset = col.index - visible + 1

    col.row_rects = []
    for k in range(visible):
        idx = col.offset + k
        if idx >= len(col.roster):
            break
        ball = col.roster[idx]
        rect = (inner_x, list_top + k * ROW_STEP, inner_w, ROW_H)
        col.row_rects.append(rect)

        if idx == col.index:
            mode = "filled" if active else "outline"
        else:
            mode = "idle"
        size = render.fit_size(ball.name, inner_w - 32, T.S_DISPLAY, minimum=15)
        T.bar_row(screen, rect, ball.name, mode=mode, size=size,
                  hovered=(hover_index == idx and idx != col.index))

    # 选中球的描述：紧跟在列表下面
    cur = col.current
    if cur and cur.desc:
        desc_y = min(list_top + min(len(col.roster), visible) * ROW_STEP + 22,
                     height - T.HINT_H - 26)
        pygame.draw.line(screen, T.RULE, (inner_x, desc_y - 13),
                         (inner_x + inner_w, desc_y - 13), 1)
        ty = desc_y
        for line in _wrap(cur.desc, T.S_BODY, inner_w):
            render.draw_text(screen, line, size=T.S_BODY, color=T.INK_2,
                             topleft=(inner_x, ty))
            ty += 27


def edit_button_rect(width: int, height: int) -> tuple:
    return (T.PAD, height - T.HINT_H + (T.HINT_H - BTN_H) // 2, 176, BTN_H)


def draw_frame(screen, columns: List[_Column], active: int, g, width: int, height: int,
               mouse_pos=(0, 0), hover_rows=None, hover_btn: bool = False) -> None:
    """把选球界面整帧画出来（不处理输入，方便单测/复用）。"""
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

    T.hint_bar(screen, width, height, _hint_text(columns))

    if any(c.selectable for c in columns):
        T.button(screen, edit_button_rect(width, height), "编辑横杠  E", hovered=hover_btn)


def _hint_text(columns) -> str:
    n = sum(1 for c in columns if c.selectable)
    if n > 1:
        return "↑↓ 选择      Tab 换屏      Enter 开始      Esc 退出"
    return "↑↓ 选择      Enter 开始      Esc 退出"


def run(screen, cfg: GameConfig):
    """跑选球界面。

    返回 ("play", [每屏选中的球])，或 ("edit", None)（用户要去编横杠）；
    按 Esc / 关窗口返回 None。
    """
    g = cfg.glob
    size = screen.get_size()
    width, height = size

    columns: List[_Column] = []
    for i, (pcfg, rect) in enumerate(zip(cfg.panels, config_mod.panel_rects(cfg, size))):
        if pcfg.title:
            title = pcfg.title
        elif len(cfg.panels) == 1:
            title = "选择球"
        else:
            title = "左屏" if i == 0 else ("右屏" if i == 1 else f"第 {i + 1} 屏")
        columns.append(_Column(rect, title, cfg.roster, pcfg.ball, pcfg.pinned))

    selectable = [i for i, c in enumerate(columns) if c.selectable]
    active = selectable[0] if selectable else 0
    clock = pygame.time.Clock()

    mouse_pos = (0, 0)
    hover_rows: List[Optional[int]] = [None] * len(columns)
    hover_btn = False

    def refresh_hover() -> None:
        nonlocal hover_btn
        for i, col in enumerate(columns):
            hover_rows[i] = col.row_at(mouse_pos)
        hover_btn = T.in_rect(mouse_pos, edit_button_rect(width, height))

    while True:
        # 窗口被拖动了 -> 按新尺寸重算各列的位置
        new_size = screen.get_size()
        if new_size != size:
            size = new_size
            width, height = size
            for col, rect in zip(columns, config_mod.panel_rects(cfg, size)):
                col.rect = rect
            refresh_hover()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None

            if e.type == pygame.MOUSEMOTION:
                mouse_pos = e.pos
                refresh_hover()

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_pos = e.pos
                refresh_hover()
                if hover_btn:
                    return ("edit", None)
                for i, col in enumerate(columns):
                    idx = col.row_at(e.pos)
                    if idx is not None and col.selectable:
                        active = i
                        col.index = idx
                        refresh_hover()
                        break

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return ("play", [c.current for c in columns])
                if e.key == pygame.K_e:
                    return ("edit", None)
                if e.key in (pygame.K_UP, pygame.K_w):
                    columns[active].move(-1)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    columns[active].move(1)
                elif e.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT,
                               pygame.K_a, pygame.K_d):
                    if len(selectable) > 1:
                        step = -1 if e.key in (pygame.K_LEFT, pygame.K_a) else 1
                        k = selectable.index(active) if active in selectable else 0
                        active = selectable[(k + step) % len(selectable)]
                refresh_hover()

        draw_frame(screen, columns, active, g, width, height,
                   mouse_pos, hover_rows, hover_btn)
        pygame.display.flip()
        clock.tick(g.fps)
