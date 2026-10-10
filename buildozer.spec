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

# ★ 见文件头的说明：这组版本号是能编译通过的关键，别乱动
requirements = python3==3.10.12,kivy==2.3.0,hostpython3==3.10.12,pyjnius==1.5.0,pygame

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
warn_on_root = 1
