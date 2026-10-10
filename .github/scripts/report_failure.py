"""
构建失败时，把 buildozer 日志的关键部分发成一条 GitHub Issue。

为什么发 Issue 而不是提交回仓库：
    公开仓库的构建日志只有管理员能通过 API 读到（匿名访问返回 403），
    而 Issue 是公开可读的。发成 Issue 之后，任何人都能拿 API 看到失败原因。
    （原来试过"提交回仓库"，但容器里 git 拿不到推送权限。）

环境变量：
    GH_TOKEN  GitHub 自动注入的 token（需要 issues: write 权限）
    REPO      owner/repo
    RUN_URL  这次构建的页面地址（放进正文方便点回去）
"""

import json
import os
import urllib.request

LOG = "/tmp/bz.log"
MAX_BODY = 60000        # GitHub 单条正文上限约 65536，留点余量


def read_tail(path: str, lines: int = 400) -> str:
    """取日志最后 N 行。文件不存在说明失败得很早，如实说明。"""
    if not os.path.exists(path):
        return "(没生成日志文件 —— 说明失败在 buildozer 真正开始之前)"
    with open(path, encoding="utf-8", errors="replace") as f:
        return "".join(f.readlines()[-lines:])


def main() -> int:
    body = (
        f"构建失败：{os.environ.get('RUN_URL', '(无地址)')}\n\n"
        f"## 最后的 400 行（能看出在编译哪个库）\n"
        f"```\n{read_tail(LOG)}\n```\n"
    )
    if len(body) > MAX_BODY:
        body = body[:MAX_BODY] + "\n...(太长，已截断)"

    payload = json.dumps({"title": "构建失败日志", "body": body}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{os.environ['REPO']}/issues",
        data=payload,
        headers={
            "Authorization": "token " + os.environ["GH_TOKEN"],
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "buildozer-ci",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("Issue 已创建，状态码:", r.status)
    except Exception as exc:
        # 发不出去也不要让这一步再挂一次，至少把日志打到 stdout
        print("创建 Issue 失败:", exc)
        print(body[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
