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

import asyncio
import os
import sys

import pygame

import bar_editor
import bignum
import config as config_mod
import paths
import render
import select_screen
from panel import Panel


def _fatal(message: str) -> None:
    """出错了。

    控制台印一份；打包成 exe 后没控制台，再弹个系统对话框；
    最后**抛异常**，交给最外层的 main() 画到屏幕上 —— 不抛的话程序会
    "静静地退出"，网页版就只剩一片灰，什么线索都没有。
    """
    print(message, flush=True)
    if paths.is_frozen():
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "弹球 · 大数", 0x10)
        except Exception:
            pass
    raise RuntimeError(message)


def _exec_file_as_module(path: str, name: str) -> None:
    """把一个具体的 .py 文件当模块加载并执行。

    用来加载"程序旁边"的 custom_effects.py —— 打包之后 import 会找到
    打包进 exe 的那份，而我们要的是外面那份。
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"加载不了 {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module      # 先登记，模块内部互相引用时才找得到
    spec.loader.exec_module(module)


def _load_custom_effects() -> None:
    """载入用户自己写的算子。写挂了只警告，不影响游戏跑起来。

    打包发出去之后，别人也应该能自己加算子 —— 所以**优先加载程序旁边的
    custom_effects.py**，旁边没有才用打包进 exe 的那份默认示例。
    """
    beside = os.path.join(paths.program_dir(), "custom_effects.py")
    if paths.is_frozen() and os.path.exists(beside):
        try:
            _exec_file_as_module(beside, "custom_effects")
            print(f"[info] 已从 {beside} 载入自定义算子")
            return
        except Exception as exc:
            print(f"[warn] {beside} 载入失败，改用内置的那份：{exc}")

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
    for panel, rect in zip(panels, config_mod.panel_rects(game_cfg, size, count=len(panels))):
        panel.relayout(rect)
    return size


async def play_one_round(screen, game_cfg, clock, active) -> str:
    """跑一局。`active` 是要玩的屏在 cfg.panels 里的下标（可能只切了一屏）。

    返回 "restart"（按了 R）或 "quit"（关窗口 / Esc）。
    """
    size = screen.get_size()
    panels = [
        Panel(game_cfg.panels[i], rect, game_cfg.glob)
        for i, rect in zip(active, config_mod.panel_rects(game_cfg, size, count=len(active)))
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
        await asyncio.sleep(0)      # 让一帧给浏览器/事件循环，pygbag 必需


async def _show_crash(text: str) -> None:
    """把报错画在屏幕上，别让页面变成一片空白然后什么都不说。

    网页版出问题时看不到控制台（页面全灰），这个至少让人知道错在哪一行。
    显示完就一直停着，方便截图。
    """
    print(text, flush=True)
    # 桌面版：命令行里已经能看到，直接退出。
    # 网页版和安卓上没控制台可看，必须画在屏幕上 —— 尤其安卓，闪退时
    # 用户拿不到任何日志，这一屏是唯一的线索。
    on_web = sys.platform == "emscripten"
    on_android = "ANDROID_ARGUMENT" in os.environ
    if not (on_web or on_android):
        return
    try:
        if not pygame.get_init():
            pygame.init()
        screen = pygame.display.get_surface() or pygame.display.set_mode((1000, 640))
        font = pygame.font.Font(None, 22)
        lines = []
        for raw in text.splitlines()[-40:]:
            while raw:
                lines.append(raw[:95])
                raw = raw[95:]
        while True:
            for _ in pygame.event.get():
                pass
            screen.fill((255, 238, 238))
            for i, line in enumerate(lines[:28]):
                screen.blit(font.render(line, True, (170, 0, 0)), (14, 14 + i * 22))
            pygame.display.flip()
            await asyncio.sleep(0.05)
    except Exception:
        pass


async def main():
    """真正的入口。任何异常都画到屏幕上 —— 不然网页版就是一片灰，什么都不知道。"""
    try:
        return await _main()
    except Exception:
        import traceback
        await _show_crash(traceback.format_exc())
        return 1


async def _main():
    # 命令行给了配置路径就用它，但**必须先确认那个文件真的存在**。
    # 网页版（pygbag）里 sys.argv 装的是别的东西（包名之类），
    # 直接拿来当路径会去找一个不存在的文件，然后程序启动即退出、页面全灰。
    cfg_path = None
    if len(sys.argv) > 1:
        candidate = os.path.abspath(sys.argv[1])
        if os.path.exists(candidate):
            cfg_path = candidate
    if cfg_path is None:
        cfg_path = paths.find_file("game.toml")
    cfg_path = os.path.abspath(cfg_path)

    if not os.path.exists(cfg_path):
        _fatal(
            f"找不到配置文件：\n{cfg_path}\n\n"
            f"请把 game.toml 和 balls.toml 放在程序旁边（和 exe 同一个文件夹）。"
        )

    print(f"[info] 程序目录：{paths.program_dir()}", flush=True)
    print(f"[info] 配置文件：{cfg_path}", flush=True)

    try:
        game_cfg = config_mod.load(cfg_path)
    except Exception as exc:
        _fatal(f"配置读不了：\n{cfg_path}\n\n{type(exc).__name__}: {exc}")

    bignum.FULL_DIGIT_LIMIT = game_cfg.glob.full_digit_limit

    _load_custom_effects()

    pygame.init()
    pygame.display.set_caption("弹球 · 大数")

    # 网页版跑在 emscripten 上；安卓上 python-for-android 会设 ANDROID_ARGUMENT 这个环境变量
    on_web = sys.platform == "emscripten"
    on_android = "ANDROID_ARGUMENT" in os.environ
    on_mobile = on_web or on_android

    size = config_mod.window_size(game_cfg)
    if on_android:
        # 手机屏幕比例千差万别，直接用真实分辨率 ——
        # panel_rects() 会按这个尺寸重新分屏，横杠自己会适配
        pygame.display.init()
        info = pygame.display.Info()
        if info.current_w > 0 and info.current_h > 0:
            size = (info.current_w, info.current_h)

    # 手机上不存在"拖窗口"，别传 RESIZABLE
    flags = pygame.RESIZABLE if (game_cfg.glob.resizable and not on_mobile) else 0
    screen = pygame.display.set_mode(size, flags)
    clock = pygame.time.Clock()

    # 手机上闪退是看不到任何信息的，所以先画两个"路标"：
    #   屏幕变蓝   -> Python 起来了、显示也初始化了
    #   出现"启动中" -> 中文字体加载成功
    # 正常启动后会被游戏画面盖掉；要是停在这一屏，就知道后面哪一步崩了。
    if on_mobile:
        try:
            screen.fill((70, 130, 200))
            pygame.display.flip()
        except Exception:
            pass
        try:
            render.draw_text(screen, "启动中…", size=44, color=(255, 255, 255),
                             center=(size[0] // 2, size[1] // 2))
            pygame.display.flip()
        except Exception:
            pass

    picking = config_mod.needs_selection(game_cfg)
    # 要玩的屏的下标。选球界面里按 S 可以就地改成只留一屏。
    active = list(range(len(game_cfg.panels)))

    while True:
        # ── 开局准备：选球 + 编横杠，来回切直到按 Enter 开打 ──
        if picking:
            while True:
                if not active:
                    active = list(range(len(game_cfg.panels)))
                # 切单屏的时候窗口会改尺寸，所以把 surface 接回来
                screen, action = await select_screen.run(screen, game_cfg, active)
                if action is None:
                    pygame.quit()
                    return 0             # 按了 Esc
                kind, chosen = action
                if kind == "edit":
                    await bar_editor.run(screen, game_cfg, active)
                    continue
                for idx, ball in zip(active, chosen):
                    if ball is not None:
                        game_cfg.panels[idx].ball = ball
                break

        result = await play_one_round(screen, game_cfg, clock, active)
        if result == "quit":
            break
        # "restart"：回到循环开头，需要选球就再弹一次

    pygame.quit()
    return 0


# pygbag（网页版）要求这个形式：async 入口 + asyncio.run，后面不能再有别的代码。
# 桌面版走同一条路，行为完全一样。
asyncio.run(main())
