"""
弹球大数游戏 —— 入口。

用法：
    python main.py [关卡配置路径]

默认读同目录下的 game.toml；球库默认读同目录下的 balls.toml。

    开局   可以从球库里选球（哪一屏写死了球就不参与选择）
    R      重开 —— 如果开了选球，会回到选球界面，可以换个球
    ESC    退出
"""

from __future__ import annotations

import os
import sys

import pygame

import bar_editor
import bignum
import config as config_mod
import render
import select_screen
from panel import Panel


def _load_custom_effects():
    """载入用户自己写的算子。写挂了只警告，不影响游戏跑起来。"""
    try:
        import custom_effects  # noqa: F401
    except Exception as exc:  # pragma: no cover - 给用户看的兜底
        print(f"[warn] custom_effects.py 载入失败：{exc}")


def _winner_text(panels) -> str:
    """只要有任意一屏打完，就宣布结果 —— 单屏提示通关，分屏宣布谁先到底。"""
    done = [p for p in panels if p.finished and p.finished_at is not None]
    if not done:
        return ""
    if len(panels) == 1:
        return "完成！按 R 重开"
    first = min(done, key=lambda p: p.finished_at)
    return f"{first.cfg.ball.name} 先到底 —— 获胜！    按 R 重开"


def render_frame(screen, panels, game_cfg):
    """把当前这一帧画出来：白底 -> 分屏竖线 -> 各面板 -> 胜负文字。"""
    width, height = screen.get_size()
    screen.fill((255, 255, 255))

    # 竖线画在相邻两屏之间那点空隙上（宽度跟着窗口走，不是写死的）
    divider = game_cfg.glob.divider_width
    for i in range(1, len(panels)):
        x = panels[i].x - divider
        pygame.draw.rect(screen, (0, 0, 0), (x, 0, divider, height))

    for panel in panels:
        panel.draw(screen)

    text = _winner_text(panels)
    if text:
        render.draw_text(screen, text, size=40, color=(200, 30, 30),
                         center=(width // 2, height // 2))


def relayout_panels(screen, game_cfg, panels) -> tuple:
    """窗口被拖动了 -> 按新尺寸重排横杠，球按比例挪过去。返回新的尺寸。"""
    size = screen.get_size()
    for panel, rect in zip(panels, config_mod.panel_rects(game_cfg, size)):
        panel.relayout(rect)
    return size


def play_one_round(screen, game_cfg, clock) -> str:
    """跑一局。返回 "restart"（按了 R）或 "quit"（关窗口 / Esc）。"""
    size = screen.get_size()
    panels = [
        Panel(pcfg, rect, game_cfg.glob)
        for pcfg, rect in zip(game_cfg.panels, config_mod.panel_rects(game_cfg, size))
    ]
    elapsed = 0.0

    while True:
        dt = min(clock.tick(game_cfg.glob.fps) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                if event.key == pygame.K_r:
                    return "restart"

        # 窗口大小变了就重排（用户拖窗口 / 双击标题栏最大化都走这里）
        if screen.get_size() != size:
            size = relayout_panels(screen, game_cfg, panels)

        # 只要有一屏打完就整个暂停，等按 R 重开
        if not any(p.finished for p in panels):
            elapsed += dt
            for panel in panels:
                panel.update(dt, elapsed)

        render_frame(screen, panels, game_cfg)
        pygame.display.flip()


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, "game.toml")
    cfg_path = os.path.abspath(cfg_path)

    if not os.path.exists(cfg_path):
        print(f"找不到配置文件：{cfg_path}")
        return 1

    try:
        game_cfg = config_mod.load(cfg_path)
    except Exception as exc:
        print(f"配置读不了：{cfg_path}\n  {type(exc).__name__}: {exc}")
        return 1

    bignum.FULL_DIGIT_LIMIT = game_cfg.glob.full_digit_limit

    _load_custom_effects()

    pygame.init()
    pygame.display.set_caption("弹球 · 大数")

    size = config_mod.window_size(game_cfg)
    flags = pygame.RESIZABLE if game_cfg.glob.resizable else 0
    screen = pygame.display.set_mode(size, flags)
    clock = pygame.time.Clock()

    picking = config_mod.needs_selection(game_cfg)

    while True:
        # ── 开局准备：选球 + 编横杠，来回切直到按 Enter 开打 ──
        if picking:
            while True:
                action = select_screen.run(screen, game_cfg)
                if action is None:
                    pygame.quit()
                    return 0             # 按了 Esc
                kind, chosen = action
                if kind == "edit":
                    bar_editor.run(screen, game_cfg)
                    continue
                for pcfg, ball in zip(game_cfg.panels, chosen):
                    if ball is not None:
                        pcfg.ball = ball
                break

        result = play_one_round(screen, game_cfg, clock)
        if result == "quit":
            break
        # "restart"：回到循环开头，需要选球就再弹一次

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
