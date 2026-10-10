# 构建失败日志（自动生成，排查用）

运行: https://github.com/store-ick/ball/actions/runs/38047137868

```
configure.ac:418: the top level
configure.ac:215: error: possibly undefined macro: LT_SYS_SYMBOL_USCORE
      If this token and others are legitimate, please use m4_pattern_allow.
      See the Autoconf documentation.
autoreconf: error: /usr/bin/autoconf failed with exit status: 1


  STDERR:

[0m[1;34m# Android packages installation done.[0m
[0m[1;30m# Run '/opt/hostedtoolcache/Python/3.10.22/x64/bin/python -m pythonforandroid.toolchain aab -h --color=always --storage-dir=/home/runner/work/ball/ball/.buildozer/android/platform/build-arm64-v8a --ndk-api=24 --ignore-setup-py --debug' ...[0m
[0m[1;30m# Cwd /home/runner/work/ball/ball/.buildozer/android/platform/python-for-android[0m
[0m[1;34m# Check application requirements[0m
[0m[1;34m# Compile platform[0m
[0m[1;30m# Run '/opt/hostedtoolcache/Python/3.10.22/x64/bin/python -m pythonforandroid.toolchain create --dist_name=ballgame --bootstrap=sdl2 --requirements=python3==3.10.12,kivy==2.3.0,hostpython3==3.10.12,pyjnius==1.5.0,pygame --arch=arm64-v8a --copy-libs --color=always --storage-dir=/home/runner/work/ball/ball/.buildozer/android/platform/build-arm64-v8a --ndk-api=24 --ignore-setup-py --debug' ...[0m
[0m[1;30m# Cwd /home/runner/work/ball/ball/.buildozer/android/platform/python-for-android[0m
[0m[1;31m# Command failed: ('/opt/hostedtoolcache/Python/3.10.22/x64/bin/python', '-m', 'pythonforandroid.toolchain', 'create', '--dist_name=ballgame', '--bootstrap=sdl2', '--requirements=python3==3.10.12,kivy==2.3.0,hostpython3==3.10.12,pyjnius==1.5.0,pygame', '--arch=arm64-v8a', '--copy-libs', '--color=always', '--storage-dir=/home/runner/work/ball/ball/.buildozer/android/platform/build-arm64-v8a', '--ndk-api=24', '--ignore-setup-py', '--debug')[0m
[0m[1;31m# Error code: 1[0m
[0m[1;31m# ENVIRONMENT:[0m
[0m[1;31m#     SHELL = '/bin/bash'[0m
[0m[1;31m#     SELENIUM_JAR_PATH = '/usr/share/java/selenium-server.jar'[0m
[0m[1;31m#     CONDA = '/usr/share/miniconda'[0m
[0m[1;31m#     GITHUB_WORKSPACE = '/home/runner/work/ball/ball'[0m
[0m[1;31m#     JAVA_HOME_11_X64 = '/usr/lib/jvm/temurin-11-jdk-amd64'[0m
[0m[1;31m#     JAVA_HOME_25_X64 = '/usr/lib/jvm/temurin-25-jdk-amd64'[0m
[0m[1;31m#     PKG_CONFIG_PATH = '/opt/hostedtoolcache/Python/3.10.22/x64/lib/pkgconfig'[0m
[0m[1;31m#     GITHUB_PATH = '/home/runner/work/_temp/_runner_file_commands/add_path_3360162f-8f36-499b-8831-bb32292f0172'[0m
[0m[1;31m#     GITHUB_ACTION = 'build'[0m
[0m[1;31m#     JAVA_HOME = '/opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.20-1/x64'[0m
[0m[1;31m#     GITHUB_RUN_NUMBER = '2'[0m
[0m[1;31m#     RUNNER_NAME = 'GitHub Actions 1000000001'[0m
[0m[1;31m#     GRADLE_HOME = '/usr/share/gradle-9.8.0'[0m
[0m[1;31m#     GITHUB_REPOSITORY_OWNER_ID = '209243694'[0m
[0m[1;31m#     ACTIONS_RUNNER_ACTION_ARCHIVE_CACHE = '/opt/actionarchivecache'[0m
[0m[1;31m#     XDG_CONFIG_HOME = '/home/runner/.config'[0m
[0m[1;31m#     Python_ROOT_DIR = '/opt/hostedtoolcache/Python/3.10.22/x64'[0m
[0m[1;31m#     MEMORY_PRESSURE_WRITE = 'c29tZSAyMDAwMDAgMjAwMDAwMAA='[0m
[0m[1;31m#     DOTNET_SKIP_FIRST_TIME_EXPERIENCE = '1'[0m
[0m[1;31m#     ANT_HOME = '/usr/share/ant'[0m
[0m[1;31m#     JAVA_HOME_8_X64 = '/usr/lib/jvm/temurin-8-jdk-amd64'[0m
[0m[1;31m#     GITHUB_TRIGGERING_ACTOR = 'store-ick'[0m
[0m[1;31m#     pythonLocation = '/opt/hostedtoolcache/Python/3.10.22/x64'[0m
[0m[1;31m#     GITHUB_REF_TYPE = 'branch'[0m
[0m[1;31m#     HOMEBREW_CLEANUP_PERIODIC_FULL_DAYS = '3650'[0m
[0m[1;31m#     ACTIONS_RUNNER_RETURN_JOB_RESULT_FOR_HOSTED = '1'[0m
[0m[1;31m#     ANDROID_NDK = '/usr/local/lib/android/sdk/ndk/27.3.13750724'[0m
[0m[1;31m#     BOOTSTRAP_HASKELL_NONINTERACTIVE = '1'[0m
[0m[1;31m#     PWD = '/home/runner/work/ball/ball'[0m
[0m[1;31m#     PIPX_BIN_DIR = '/opt/pipx_bin'[0m
[0m[1;31m#     LOGNAME = 'runner'[0m
[0m[1;31m#     GITHUB_ARTIFACTS_LIST = '/home/runner/work/_temp/_runner_file_commands/artifacts_list_3360162f-8f36-499b-8831-bb32292f0172'[0m
[0m[1;31m#     GITHUB_REPOSITORY_ID = '1413072173'[0m
[0m[1;31m#     GITHUB_ACTIONS = 'true'[0m
[0m[1;31m#     USE_BAZEL_FALLBACK_VERSION = 'silent:'[0m
[0m[1;31m#     ANDROID_NDK_LATEST_HOME = '/usr/local/lib/android/sdk/ndk/30.0.16248370'[0m
[0m[1;31m#     SYSTEMD_EXEC_PID = '2082'[0m
[0m[1;31m#     GITHUB_SHA = '052d6287960fb1b2c77698916899473c412d0bb6'[0m
[0m[1;31m#     GITHUB_WORKFLOW_REF = 'store-ick/ball/.github/workflows/build_apk.yml@refs/heads/master'[0m
[0m[1;31m#     POWERSHELL_DISTRIBUTION_CHANNEL = 'GitHub-Actions-Linux'[0m
[0m[1;31m#     RUNNER_ENVIRONMENT = 'github-hosted'[0m
[0m[1;31m#     DOTNET_MULTILEVEL_LOOKUP = '0'[0m
[0m[1;31m#     GITHUB_REF = 'refs/heads/master'[0m
[0m[1;31m#     RUNNER_OS = 'Linux'[0m
[0m[1;31m#     GITHUB_REF_PROTECTED = 'false'[0m
[0m[1;31m#     HOME = '/home/runner'[0m
[0m[1;31m#     GITHUB_API_URL = 'https://api.github.com'[0m
[0m[1;31m#     LANG = 'C.UTF-8'[0m
[0m[1;31m#     GOROOT_1_25_X64 = '/opt/hostedtoolcache/go/1.25.14/x64'[0m
[0m[1;31m#     RUNNER_TRACKING_ID = 'github_abbdb708-aac3-4a65-be88-42b9e733e176'[0m
[0m[1;31m#     RUNNER_ARCH = 'X64'[0m
[0m[1;31m#     MEMORY_PRESSURE_WATCH = '/sys/fs/cgroup/system.slice/hosted-compute-agent.service/memory.pressure'[0m
[0m[1;31m#     RUNNER_TEMP = '/home/runner/work/_temp'[0m
[0m[1;31m#     GITHUB_STATE = '/home/runner/work/_temp/_runner_file_commands/save_state_3360162f-8f36-499b-8831-bb32292f0172'[0m
[0m[1;31m#     EDGEWEBDRIVER = '/usr/local/share/edge_driver'[0m
[0m[1;31m#     JAVA_HOME_21_X64 = '/usr/lib/jvm/temurin-21-jdk-amd64'[0m
[0m[1;31m#     GITHUB_ENV = '/home/runner/work/_temp/_runner_file_commands/set_env_3360162f-8f36-499b-8831-bb32292f0172'[0m
[0m[1;31m#     GITHUB_EVENT_PATH = '/home/runner/work/_temp/_github_workflow/event.json'[0m
[0m[1;31m#     INVOCATION_ID = 'cb79dabebc634791931c8b2eb6ca6b8d'[0m
[0m[1;31m#     GITHUB_EVENT_NAME = 'push'[0m
[0m[1;31m#     GITHUB_RUN_ID = '38047137868'[0m
[0m[1;31m#     JAVA_HOME_17_X64 = '/opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.20-1/x64'[0m
[0m[1;31m#     ANDROID_NDK_HOME = '/usr/local/lib/android/sdk/ndk/27.3.13750724'[0m
[0m[1;31m#     GITHUB_STEP_SUMMARY = '/home/runner/work/_temp/_runner_file_commands/step_summary_3360162f-8f36-499b-8831-bb32292f0172'[0m
[0m[1;31m#     HOMEBREW_NO_AUTO_UPDATE = '1'[0m
[0m[1;31m#     GITHUB_ACTOR = 'store-ick'[0m
[0m[1;31m#     NVM_DIR = '/home/runner/.nvm'[0m
[0m[1;31m#     SGX_AESM_ADDR = '1'[0m
[0m[1;31m#     GITHUB_RUN_ATTEMPT = '1'[0m
[0m[1;31m#     ANDROID_HOME = '/usr/local/lib/android/sdk'[0m
[0m[1;31m#     GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'[0m
[0m[1;31m#     ACCEPT_EULA = 'Y'[0m
[0m[1;31m#     USER = 'runner'[0m
[0m[1;31m#     PSModulePath = '/root/.local/share/powershell/Modules:/usr/local/share/powershell/Modules:/opt/microsoft/powershell/7/Modules:/usr/share/az_15.6.1'[0m
[0m[1;31m#     GITHUB_SERVER_URL = 'https://github.com'[0m
[0m[1;31m#     PIPX_HOME = '/opt/pipx'[0m
[0m[1;31m#     GECKOWEBDRIVER = '/usr/local/share/gecko_driver'[0m
[0m[1;31m#     CHROMEWEBDRIVER = '/usr/local/share/chromedriver-linux64'[0m
[0m[1;31m#     SHLVL = '1'[0m
[0m[1;31m#     ANDROID_SDK_ROOT = '/usr/local/lib/android/sdk'[0m
[0m[1;31m#     VCPKG_INSTALLATION_ROOT = '/usr/local/share/vcpkg'[0m
[0m[1;31m#     GITHUB_ACTOR_ID = '209243694'[0m
[0m[1;31m#     ACTIONS_ORCHESTRATION_ID = '063c0fb6-5351-85d8-9182-8f2c90a2b681.build.__default'[0m
[0m[1;31m#     RUNNER_TOOL_CACHE = '/opt/hostedtoolcache'[0m
[0m[1;31m#     ImageVersion = '20261004.327.1'[0m
[0m[1;31m#     Python3_ROOT_DIR = '/opt/hostedtoolcache/Python/3.10.22/x64'[0m
[0m[1;31m#     DOTNET_NOLOGO = '1'[0m
[0m[1;31m#     GITHUB_ARTIFACTS = '/home/runner/work/_temp/_runner_file_commands/artifacts_3360162f-8f36-499b-8831-bb32292f0172'[0m
[0m[1;31m#     GITHUB_WORKFLOW_SHA = '052d6287960fb1b2c77698916899473c412d0bb6'[0m
[0m[1;31m#     GOROOT_1_24_X64 = '/opt/hostedtoolcache/go/1.24.13/x64'[0m
[0m[1;31m#     GITHUB_REF_NAME = 'master'[0m
[0m[1;31m#     GITHUB_JOB = 'build'[0m
[0m[1;31m#     LD_LIBRARY_PATH = '/opt/hostedtoolcache/Python/3.10.22/x64/lib'[0m
[0m[1;31m#     XDG_RUNTIME_DIR = '/run/user/1001'[0m
[0m[1;31m#     AZURE_EXTENSION_DIR = '/opt/az/azcliextensions'[0m
[0m[1;31m#     GOROOT_1_26_X64 = '/opt/hostedtoolcache/go/1.26.8/x64'[0m
[0m[1;31m#     GITHUB_REPOSITORY = 'store-ick/ball'[0m
[0m[1;31m#     Python2_ROOT_DIR = '/opt/hostedtoolcache/Python/3.10.22/x64'[0m
[0m[1;31m#     ANDROID_NDK_ROOT = '/usr/local/lib/android/sdk/ndk/27.3.13750724'[0m
[0m[1;31m#     CHROME_BIN = '/usr/bin/google-chrome'[0m
[0m[1;31m#     GITHUB_RETENTION_DAYS = '90'[0m
[0m[1;31m#     JOURNAL_STREAM = '9:15412'[0m
[0m[1;31m#     RUNNER_WORKSPACE = '/home/runner/work/ball'[0m
[0m[1;31m#     GITHUB_ACTION_REPOSITORY = ''[0m
[0m[1;31m#     HCA_CLOUD_PROVIDER = 'azure'[0m
[0m[1;31m#     PATH = '/home/runner/.buildozer/android/platform/apache-ant-1.9.4/bin:/opt/hostedtoolcache/Python/3.10.22/x64/bin:/opt/hostedtoolcache/Python/3.10.22/x64:/opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.20-1/x64/bin:/snap/bin:/home/runner/.local/bin:/opt/pipx_bin:/home/runner/.cargo/bin:/home/runner/.config/composer/vendor/bin:/usr/local/.ghcup/bin:/home/runner/.dotnet/tools:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin'[0m
[0m[1;31m#     GITHUB_BASE_REF = ''[0m
[0m[1;31m#     GHCUP_INSTALL_BASE_PREFIX = '/usr/local'[0m
[0m[1;31m#     CI = 'true'[0m
[0m[1;31m#     SWIFT_PATH = '/usr/share/swift/usr/bin'[0m
[0m[1;31m#     ImageOS = 'ubuntu24'[0m
[0m[1;31m#     GITHUB_REPOSITORY_OWNER = 'store-ick'[0m
[0m[1;31m#     GITHUB_HEAD_REF = ''[0m
[0m[1;31m#     GITHUB_ACTION_REF = ''[0m
[0m[1;31m#     ENABLE_RUNNER_TRACING = 'true'[0m
[0m[1;31m#     GITHUB_WORKFLOW = '构建 APK'[0m
[0m[1;31m#     DEBIAN_FRONTEND = 'noninteractive'[0m
[0m[1;31m#     GITHUB_OUTPUT = '/home/runner/work/_temp/_runner_file_commands/set_output_3360162f-8f36-499b-8831-bb32292f0172'[0m
[0m[1;31m#     AGENT_TOOLSDIRECTORY = '/opt/hostedtoolcache'[0m
[0m[1;31m#     _ = '/opt/hostedtoolcache/Python/3.10.22/x64/bin/buildozer'[0m
[0m[1;31m#     PACKAGES_PATH = '/home/runner/.buildozer/android/packages'[0m
[0m[1;31m#     ANDROIDSDK = '/home/runner/.buildozer/android/platform/android-sdk'[0m
[0m[1;31m#     ANDROIDNDK = '/home/runner/.buildozer/android/platform/android-ndk-r25b'[0m
[0m[1;31m#     ANDROIDAPI = '33'[0m
[0m[1;31m#     ANDROIDMINAPI = '24'[0m
[0m[1;31m# [0m
[0m[1;31m# Buildozer failed to execute the last command[0m
[0m[1;31m# The error might be hidden in the log above this error[0m
[0m[1;31m# Please read the full log, and search for it before[0m
[0m[1;31m# raising an issue with buildozer itself.[0m
[0m[1;31m# In case of a bug report, please add a full log with log_level = 2[0m
```
