# =============================================================================
#  Buildozer 配置 —— 把游戏打成安卓 APK
# =============================================================================
#  本地用不上（Windows 跑不了 buildozer），是给 GitHub Actions 用的：
#  推代码 → 云端 Linux 跑 `buildozer android debug` → 产出 APK 挂到 Actions 里下载。
#
#  ⚠️ requirements 那行是被逼的：
#     python-for-android 里 pygame 的 recipe 早就没人维护了，
#     Python 3.11 删了 longintrepr.h、3.12 删了 distutils，都会让编译挂掉。
#     所以必须把 Python 钉回 3.10，Cython 钉在 3.0 以下。
#     别轻易改这几个版本号，改了大概率编译失败。
# =============================================================================

[app]

title = 弹球大数
package.name = ballgame
package.domain = com.stoneick

# 游戏源码就在仓库根目录
source.dir = .
source.include_exts = py,toml,ttf
# 这些是开发用的目录，打进包里只会让包变大、甚至打不进去
source.exclude_dirs = .git,.github,.idea,dist,build,__pycache__,.venv,venv,webapp,_runtime,_webtest,_cdn_cache

version = 1.0.0

# ★ 见文件头的说明：Python 和 Cython 的版本是能编译通过的关键，别乱动。
#
# 为什么没有 kivy / pyjnius：
#   这游戏是纯 pygame，压根不用它们。之前照着旧攻略抄进来，
#   结果 pyjnius==1.5.0（2022 年的版本）跟新版 Cython/setuptools 不兼容，
#   报 "NameError: name 'PYX_FILES' is not defined" 直接把构建卡死。
#   删掉之后少了两个又大又爱出毛病的依赖。
# tomli：Python 3.10 没有 tomllib（3.11 才进标准库），得靠这个背锅包读 toml。
#        它是纯 Python，p4a 直接从 PyPI 装，不需要 recipe。
requirements = python3==3.10.12,hostpython3==3.10.12,pygame,tomli

orientation = portrait
fullscreen = 1

# JDK 17 + NDK 25b 是社区验证过能过的组合
android.api = 33
android.minapi = 24
android.ndk = 25b

# 只打 64 位，构建时间砍一半（2016 年之后的手机基本都是 arm64）
android.archs = arm64-v8a

# 不自动接受 SDK 许可的话，CI 会卡在交互提示上
android.accept_sdk_license = True
android.allow_backup = True

p4a.bootstrap = sdl2


[buildozer]
log_level = 2
# ★ 必须写 0！
#   CI 的容器里是 root 用户，buildozer 会弹一句
#     "Buildozer is running as root! ... Are you sure you want to continue [y/n]?"
#   然后等键盘输入 —— CI 里没有键盘，于是 EOFError 直接崩，构建 0 秒结束。
#   写 0 就是关掉这个检查。
warn_on_root = 0
