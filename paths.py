"""
找文件的位置 —— 开发环境和 PyInstaller 打包后都能用。

为什么要这么绕：打包之后你的 .py 就不在你放 exe 的那个文件夹里了。

    --onefile   压成一个 exe，运行时先解压到一个临时目录再跑，
                __file__ 指向那个临时目录（每次运行都不一样，关掉就删）
    --onedir    生成一个文件夹，代码在 _internal 里（PyInstaller 6+）

所以"我旁边有什么文件"跟"我的代码在哪"是两件事，得分开问：

    program_dir()   程序"身边"是哪 —— 开发时是 .py 所在目录，打包后是 exe 所在目录
    bundled_dir()   打包进去的资源被解压到哪（就是 sys._MEIPASS，没打包时是 None）

找文件的顺序是「**配置旁边 → 程序旁边 → 打包进去的那份**」：
放在外面的优先，这样使用者改了才能生效；外面没有就退回打包的默认值，双击也能玩。
"""

from __future__ import annotations

import os
import sys


def is_frozen() -> bool:
    """是不是 PyInstaller 打出来的程序。"""
    return getattr(sys, "frozen", False)


def program_dir() -> str:
    """程序"身边"的目录。

    开发时 -> 这个 .py 文件所在的目录
    打包后 -> exe 所在的目录（**不是** PyInstaller 解压代码的临时目录）
    """
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def bundled_dir():
    """打包进 exe 的资源被解压到哪。没打包就是 None。"""
    return getattr(sys, "_MEIPASS", None)


def find_file(name: str, *prefer_dirs) -> str:
    """按顺序找文件，返回找到的第一个绝对路径。

    顺序：prefer_dirs（调用方指定的偏好目录）-> 程序旁边 -> 打包进去的那份。
    一个都没找到，就返回"程序旁边"那个路径 —— 报错信息里显示这个最直观。
    """
    dirs = [d for d in prefer_dirs if d]
    dirs.append(program_dir())
    bundled = bundled_dir()
    if bundled:
        dirs.append(bundled)

    for d in dirs:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return os.path.join(program_dir(), name)


def resource_path(name: str) -> str:
    """find_file 的简写：只在"程序旁边"和"打包进去"里找。"""
    return find_file(name)
