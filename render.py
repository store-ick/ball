"""字体加载 + 文本绘制的小工具。"""

from __future__ import annotations

import os

import pygame

import paths

# ★ 优先用"跟程序放在一起"的字体。
#   网页版（pygbag）和打包成 exe 之后，系统字体路径是不存在的 ——
#   浏览器里没有 C:\Windows\Fonts，所以必须把字体文件打进包里一起发。
#   想换字体：把一个 .ttf/.ttc 放到程序旁边，改这里的文件名即可。
_BUNDLED_CANDIDATES = [
    "simhei.ttf",        # 黑体（9.3MB，覆盖全部常用汉字）
    "font.ttf",
    "msyh.ttc",
]

# 找不到打包字体时才退回系统字体（开发时用）
_SYSTEM_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",        # 微软雅黑
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",      # 黑体
    r"C:\Windows\Fonts\Deng.ttf",        # 等线
    r"C:\Windows\Fonts\simsun.ttc",      # 宋体
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]

_font_path = None
_font_path_ready = False
_cache: dict = {}


def _resolve_font_path():
    global _font_path, _font_path_ready
    if _font_path_ready:
        return _font_path

    for name in _BUNDLED_CANDIDATES:
        p = paths.find_file(name)
        if os.path.exists(p):
            _font_path = p
            break
    else:
        for path in _SYSTEM_CANDIDATES:
            if os.path.exists(path):
                _font_path = path
                break

    _font_path_ready = True
    return _font_path


def font(size: int, bold: bool = False) -> pygame.font.Font:
    size = max(8, int(size))
    key = (size, bold)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    path = _resolve_font_path()
    if path:
        f = pygame.font.Font(path, size)
    else:
        f = pygame.font.SysFont(None, size)
    f.set_bold(bold)
    _cache[key] = f
    return f


def text_size(text: str, size: int, bold: bool = False):
    return font(size, bold).size(text)


def fit_size(text: str, max_width: int, start: int, minimum: int = 10, bold: bool = False) -> int:
    """从 start 开始往下缩，直到文字宽度塞得进 max_width。"""
    size = start
    while size > minimum and font(size, bold).size(text)[0] > max_width:
        size -= 1
    return size


def clip_text(text: str, size: int, max_width: int, bold: bool = False) -> str:
    """缩到最小字号还是塞不下，就把尾巴截掉换成省略号。

    窗口被拖得很窄的时候用得上 —— 宁可显示"每次撞击，把横杠的数字取…"，
    也不要让文字越出面板边界。
    """
    f = font(size, bold)
    if max_width <= 0:
        return ""
    if f.size(text)[0] <= max_width:
        return text
    ell = "…"
    if f.size(ell)[0] > max_width:
        return ""
    out = text
    while out and f.size(out + ell)[0] > max_width:
        out = out[:-1]
    return out + ell


def draw_text(surface, text, *, size=22, color=(0, 0, 0), bold=False,
              center=None, topleft=None, topright=None, midleft=None):
    surf = font(size, bold).render(text, True, color)
    rect = surf.get_rect()
    if center is not None:
        rect.center = center
    elif topleft is not None:
        rect.topleft = topleft
    elif topright is not None:
        rect.topright = topright
    elif midleft is not None:
        rect.midleft = midleft
    surface.blit(surf, rect)
    return rect
