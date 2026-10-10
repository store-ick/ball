"""
开局选球界面。

默认左右两屏各一列，同屏一起选。**按 S（或点左下角按钮）可以切成单屏**，
只看当前这一列的那颗球自己玩，再按一次恢复双屏。

    鼠标   悬停高亮，点一下选中；点左下角的按钮进编辑器 / 切单双屏
    键盘   ↑ / ↓ 在当前列里上下移
           Tab / ← / → 在左右两列之间切换
           Enter / 空格 开始游戏
           S 只看当前这一屏（再按一次恢复）
           E 进横杠编辑器
           Esc 退出

每一行都做成一根"横杠"：选中的那根"上墨"变成实心黑，没选中的是空槽。
当前操作的那一列标题用强调色，另一列里的选中项画成空心 —— 一眼看出焦点在哪。
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
BTN_GAP = 10
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


def _panel_title(cfg: GameConfig, index: int) -> str:
    """按它在配置里的原始位置起名，切单屏之后也知道自己看的是哪一屏。"""
    if cfg.panels[index].title:
        return cfg.panels[index].title
    if len(cfg.panels) == 1:
        return "选择球"
    if index == 0:
        return "左屏"
    if index == 1:
        return "右屏"
    return f"第 {index + 1} 屏"


def _window_size_for(cfg: GameConfig, n: int, height: int) -> tuple:
    """n 屏时窗口该多宽。切单/双屏的时候顺手把窗口调成对应比例。"""
    n = max(1, n)
    g = cfg.glob
    return (g.panel_width * n + g.divider_width * (n - 1), height)


def _build_columns(cfg: GameConfig, active: List[int], size) -> List[_Column]:
    rects = config_mod.panel_rects(cfg, size, count=len(active))
    columns = []
    for k, idx in enumerate(active):
        pcfg = cfg.panels[idx]
        columns.append(_Column(rects[k], _panel_title(cfg, idx),
                               cfg.roster, pcfg.ball, pcfg.pinned))
    return columns


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
    return _button_rect(width, height, 0, 176)


def solo_button_rect(width: int, height: int) -> tuple:
    return _button_rect(width, height, 1, 176)


def _button_rect(width: int, height: int, slot: int, w: int) -> tuple:
    y = height - T.HINT_H + (T.HINT_H - BTN_H) // 2
    return (T.PAD + slot * (w + BTN_GAP), y, w, BTN_H)


def draw_frame(screen, columns: List[_Column], active: int, width: int, height: int,
               mouse_pos=(0, 0), hover_rows=None, hover_btn=False,
               hover_solo=False, solo: bool = False) -> None:
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

    T.hint_bar(screen, width, height, _hint_text(columns, solo))

    if any(c.selectable for c in columns):
        T.button(screen, edit_button_rect(width, height), "编辑横杠  E", hovered=hover_btn)
    T.button(screen, solo_button_rect(width, height),
             "改回双屏  S" if solo else "只看这屏  S", hovered=hover_solo)


def _hint_text(columns, solo: bool) -> str:
    n = sum(1 for c in columns if c.selectable)
    if solo:
        return "↑↓ 选择      S 改回双屏      Enter 开始      Esc 退出"
    if n > 1:
        return "↑↓ 选择      Tab 换屏      Enter 开始      Esc 退出"
    return "↑↓ 选择      Enter 开始      Esc 退出"


def run(screen, cfg: GameConfig, active: List[int]):
    """跑选球界面。`active` 是要玩的屏在 cfg.panels 里的下标，可以被就地改动（切单屏）。

    返回 (screen, action)：切单屏时窗口会改尺寸，所以要把新的 surface 还回去。
    action 是 ("play", [每屏选中的球]) 或 ("edit", None)；按 Esc / 关窗口是 None。
    """
    size = screen.get_size()
    width, height = size
    columns = _build_columns(cfg, active, size)
    active_col = 0

    clock = pygame.time.Clock()
    mouse_pos = (0, 0)
    hover_rows: List[Optional[int]] = [None] * len(columns)
    hover_btn = hover_solo = False

    def refresh_hover() -> None:
        nonlocal hover_btn, hover_solo
        for i, col in enumerate(columns):
            hover_rows[i] = col.row_at(mouse_pos)
        hover_btn = T.in_rect(mouse_pos, edit_button_rect(width, height))
        hover_solo = T.in_rect(mouse_pos, solo_button_rect(width, height))

    def rebuild() -> None:
        """列数变了（切单/双屏）或者窗口尺寸变了，重算一遍。"""
        nonlocal columns, hover_rows, width, height, active_col
        width, height = screen.get_size()
        columns = _build_columns(cfg, active, (width, height))
        hover_rows = [None] * len(columns)
        active_col = min(active_col, len(columns) - 1)
        refresh_hover()

    def toggle_solo() -> None:
        nonlocal screen
        if len(active) > 1:
            active[:] = [active[active_col]]          # 只看当前这一列
        else:
            active[:] = list(range(len(cfg.panels)))  # 恢复全部
        # 顺手把窗口调成对应比例（高度保留），不然单屏会变成一个很扁的大方块
        if cfg.glob.resizable:
            new_w, cur_h = _window_size_for(cfg, len(active), height)
            screen = pygame.display.set_mode((new_w, cur_h), pygame.RESIZABLE)
        rebuild()

    while True:
        if screen.get_size() != size:
            size = screen.get_size()
            rebuild()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return screen, None

            if e.type == pygame.MOUSEMOTION:
                mouse_pos = e.pos
                refresh_hover()

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_pos = e.pos
                refresh_hover()
                if hover_btn:
                    return screen, ("edit", None)
                if hover_solo:
                    toggle_solo()
                    continue
                for i, col in enumerate(columns):
                    idx = col.row_at(e.pos)
                    if idx is not None and col.selectable:
                        active_col = i
                        col.index = idx
                        refresh_hover()
                        break

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return screen, None
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return screen, ("play", [c.current for c in columns])
                if e.key == pygame.K_e:
                    return screen, ("edit", None)
                if e.key == pygame.K_s:
                    toggle_solo()
                    continue
                if e.key in (pygame.K_UP, pygame.K_w):
                    columns[active_col].move(-1)
                elif e.key in (pygame.K_DOWN,):
                    columns[active_col].move(1)
                elif e.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT,
                               pygame.K_a, pygame.K_d):
                    if len(columns) > 1:
                        step = -1 if e.key in (pygame.K_LEFT, pygame.K_a) else 1
                        active_col = (active_col + step) % len(columns)
                refresh_hover()

        draw_frame(screen, columns, active_col, width, height,
                   mouse_pos, hover_rows, hover_btn, hover_solo, solo=len(active) == 1)
        pygame.display.flip()
        clock.tick(cfg.glob.fps)
