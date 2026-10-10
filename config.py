"""
读取 TOML 配置。

一份"关卡配置"（比如 game.toml）结构：

    [global]
    gravity = 1800.0
    balls_file = "balls.toml"     # 球库文件，相对本文件的位置

    [[panel]]
    bars = [45, 1000000, "1E10"]
    # 不写 ball = 开局弹界面让你从球库里挑

    [[panel]]
    bars = [2, 10, 10]
    ball = "1球"                   # 写死用球库里的哪颗

"球库"是另一个文件（比如 balls.toml），里面全是可选的球：

    [[ball]]
    name = "加一球"
    desc = "每次撞击，攻击力+1"
    base_damage = 1
    on_hit = [{ op = "add_damage", value = 1 }]

也允许像以前那样直接内联写死在 panel 里（[panel.ball]），那样这一屏就不参与选球。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    import tomllib                      # Python 3.11+ 自带
except ModuleNotFoundError:
    # Python 3.10 及以下没有 tomllib —— 安卓那边被 pygame 的 recipe 钉在 3.10，
    # 少了这个包游戏会启动即崩（ModuleNotFoundError: No module named 'tomllib'）。
    # tomli 是它的官方"前身"，Python 3.11 的 tomllib 就是照它做的，API 完全一样。
    import tomli as tomllib

import paths

DEFAULT_COLOR = (222, 58, 58)
DEFAULT_BALLS_FILE = "balls.toml"


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------
@dataclass
class BallCfg:
    name: str = "球"
    desc: str = ""
    base_damage: Any = 1            # 初始伤害（int / float / str）
    bounce_speed: float = 620.0     # 反弹力度（像素/秒）
    speed_x: float = 220.0          # 横向速度（正数往右，负数往左）
    radius: Optional[float] = None  # None 表示用全局值
    start_x: float = 0.5            # 出生点横向位置，0=最左 1=最右
    color: Tuple[int, int, int] = DEFAULT_COLOR
    ops: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PanelCfg:
    bars: List[Any] = field(default_factory=list)
    ball: Optional[BallCfg] = None  # 这一屏当前用的球（没选之前是 None）
    pinned: bool = False            # True = 配置里写死了球，不参与开局选择
    title: str = ""                 # 面板角标，留空就用"第 n 屏"


@dataclass
class GlobalCfg:
    gravity: float = 2000.0
    panel_width: int = 470
    panel_height: int = 900
    divider_width: int = 6
    header_height: int = 150        # 顶部留给"球名/描述/伤害"的高度
    bar_height: int = 20
    ball_radius: int = 18
    fps: int = 60
    full_digit_limit: int = 10      # 显示阈值，见 bignum
    bar_count: int = 0              # 每一屏的横杠数量，左右共用（0 = 自动取最长的那个列表）
    default_bar_hp: Any = 1         # 某屏横杠给少了，在底部补的默认血量
    balls_file: str = DEFAULT_BALLS_FILE
    resizable: bool = True          # 窗口能不能拖大小
    header_ratio: float = 0.35      # 顶部信息区最多占屏高多少（窗口压很扁时兜底）
    scale_physics: bool = True      # 物理效果随窗口缩放（球半径 / 字体不缩放）


@dataclass
class GameConfig:
    glob: GlobalCfg
    panels: List[PanelCfg]
    roster: List[BallCfg] = field(default_factory=list)   # 球库


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------
def _color(value, default=DEFAULT_COLOR) -> Tuple[int, int, int]:
    if not value:
        return default
    try:
        r, g, b = (int(c) for c in value[:3])
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    except Exception:
        return default


def _bar_hp(entry):
    """横杠可以写成数字，也可以写成 { hp = ... }，后者方便以后加字段。"""
    if isinstance(entry, dict):
        return entry.get("hp", 1)
    return entry


def _parse_ball(bd: Optional[dict]) -> BallCfg:
    """把一段球的配置（不管是球库里的还是内联的）转成 BallCfg。"""
    bd = bd or {}
    radius = bd.get("radius")
    return BallCfg(
        name=str(bd.get("name", "球")),
        desc=str(bd.get("desc", "")),
        base_damage=bd.get("base_damage", 1),
        bounce_speed=float(bd.get("bounce_speed", BallCfg.bounce_speed)),
        speed_x=float(bd.get("speed_x", BallCfg.speed_x)),
        radius=(None if radius is None else float(radius)),
        start_x=float(bd.get("start_x", BallCfg.start_x)),
        color=_color(bd.get("color")),
        ops=list(bd.get("on_hit", []) or []),
    )


def _load_roster(path: str, balls_file: str) -> List[BallCfg]:
    """读球库文件。文件不存在就返回空球库（不报错，方便单屏写死球的配置）。

    找的位置：关卡配置旁边 -> 程序旁边（exe 旁边）-> 打包进 exe 的那份。
    """
    full = paths.find_file(balls_file, os.path.dirname(os.path.abspath(path)))
    if not os.path.exists(full):
        return []
    with open(full, "rb") as fh:
        root = tomllib.load(fh)
    return [_parse_ball(b) for b in (root.get("ball") or [])]


def ball_display_name(panel: PanelCfg, index: int) -> str:
    """给控制台提示用的屏名。"""
    if panel.title:
        return panel.title
    return f"第 {index + 1} 屏"


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def load(path: str) -> GameConfig:
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)

    g = raw.get("global", {}) or {}
    glob = GlobalCfg(
        gravity=float(g.get("gravity", GlobalCfg.gravity)),
        panel_width=int(g.get("panel_width", GlobalCfg.panel_width)),
        panel_height=int(g.get("panel_height", GlobalCfg.panel_height)),
        divider_width=int(g.get("divider_width", GlobalCfg.divider_width)),
        header_height=int(g.get("header_height", GlobalCfg.header_height)),
        bar_height=int(g.get("bar_height", GlobalCfg.bar_height)),
        ball_radius=int(g.get("ball_radius", GlobalCfg.ball_radius)),
        fps=int(g.get("fps", GlobalCfg.fps)),
        full_digit_limit=int(g.get("full_digit_limit", GlobalCfg.full_digit_limit)),
        bar_count=int(g.get("bar_count", GlobalCfg.bar_count) or 0),
        default_bar_hp=g.get("default_bar_hp", GlobalCfg.default_bar_hp),
        balls_file=str(g.get("balls_file", GlobalCfg.balls_file)),
        resizable=bool(g.get("resizable", GlobalCfg.resizable)),
        header_ratio=float(g.get("header_ratio", GlobalCfg.header_ratio)),
        scale_physics=bool(g.get("scale_physics", GlobalCfg.scale_physics)),
    )

    roster = _load_roster(path, glob.balls_file)

    panels_raw = raw.get("panel") or []
    if not panels_raw:
        raise ValueError("配置里至少要有 1 个 [[panel]]")

    panels: List[PanelCfg] = []
    for i, pd in enumerate(panels_raw):
        if pd.get("enabled", True) is False:
            continue                        # enabled = false 就跳过这一屏

        spec = pd.get("ball")
        pinned = False
        if isinstance(spec, dict):
            ball: Optional[BallCfg] = _parse_ball(spec)      # 内联写死
            pinned = True
        elif isinstance(spec, str):
            ball = next((b for b in roster if b.name == spec), None)
            if ball is None:
                hint = "球库是空的" if not roster else \
                    "球库里只有：" + "、".join(b.name for b in roster)
                raise ValueError(f"[[panel]] 的 ball = \"{spec}\" 在球库里找不到（{hint}）")
            pinned = True
        else:
            ball = None                     # 开局弹界面选

        panels.append(
            PanelCfg(
                bars=[_bar_hp(b) for b in (pd.get("bars") or [])],
                ball=ball,
                pinned=pinned,
                title=str(pd.get("title", "")),
            )
        )

    if not panels:
        raise ValueError("所有 [[panel]] 都被 enabled = false 关掉了，至少要留一个")

    # 需要选球，但球库是空的 -> 早点报错，别等进游戏
    if any(p.ball is None for p in panels) and not roster:
        raise ValueError(
            f"有屏要用球库选球，但球库是空的。"
            f"请在 {glob.balls_file}（或 [global] balls_file 指定的文件）里写几个 [[ball]]。"
        )

    # 每一屏的横杠数量是共用的：所有屏都排同样的行，第 i 根就落在同一个高度，
    # 左右保证对得齐。没写 bar_count 就用最长的那个列表。
    longest = max(len(p.bars) for p in panels)
    bar_count = glob.bar_count or longest
    if bar_count < longest:
        raise ValueError(
            f"bar_count = {bar_count} 比最长的那个 bars 列表（{longest} 根）还短，放不下，把它调大"
        )

    for i, p in enumerate(panels):
        missing = bar_count - len(p.bars)
        if missing > 0:
            name = p.ball.name if p.ball else ball_display_name(p, i)
            print(
                f"[config] 「{name}」只写了 {len(p.bars)} 根横杠，"
                f"按 bar_count = {bar_count} 在底部补 {missing} 根"
                f"（血量 {glob.default_bar_hp}）。不想补就在它的 bars 里写满 {bar_count} 个。"
            )
            p.bars.extend([glob.default_bar_hp] * missing)

    glob.bar_count = bar_count

    return GameConfig(glob=glob, panels=panels, roster=roster)


def needs_selection(cfg: GameConfig) -> bool:
    """只要有一屏在配置里没写死球，就需要开局选球界面。

    注意看的是 pinned 而不是 ball —— 选完球之后 ball 会被填上，
    但那不代表这一屏就变成"写死"了。
    """
    return any(not p.pinned for p in cfg.panels)


# ---------------------------------------------------------------------------
# 几何
# ---------------------------------------------------------------------------
def window_size(cfg: GameConfig) -> Tuple[int, int]:
    n = len(cfg.panels)
    g = cfg.glob
    width = g.panel_width * n + g.divider_width * max(0, n - 1)
    return width, g.panel_height


def panel_rects(cfg: GameConfig, size=None, count: int = None) -> List[Tuple[int, int, int, int]]:
    """算出每个面板在窗口里的像素矩形 (x, y, w, h)。

    传 size 就按那个尺寸算（窗口拖大拖小之后要重算），不传就用配置里的初始尺寸。
    传 count 就按那么多屏来分（切单屏的时候用），不传就是全部屏。
    各屏宽度平均分，中间的竖线占掉固定宽度。
    """
    n = len(cfg.panels) if count is None else count
    n = max(1, n)
    g = cfg.glob
    if size is None:
        width, height = window_size(cfg)
    else:
        width, height = size

    divider = g.divider_width if n > 1 else 0
    avail = max(1, width - divider * max(0, n - 1))
    pw = avail / n

    rects = []
    for i in range(n):
        x0 = round(i * (pw + divider))
        x1 = round(i * (pw + divider) + pw)
        rects.append((x0, 0, max(1, x1 - x0), height))
    return rects
