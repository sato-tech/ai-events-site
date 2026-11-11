"""ai-events の出力(out/index.html)をこのリポジトリへ写し、変わっていれば commit + push する。

標準ライブラリのみ・LLM なし・$0。毎朝の取得(ai-events fetch)の後に launchd から呼ぶ。
  python3 publish.py            # 変更があれば公開
  python3 publish.py --dry-run  # 何をするかだけ表示
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("AI_EVENTS_SRC") or os.path.expanduser("~/Desktop/tekuo/git/ai-events/out/index.html")
DST = os.path.join(HERE, "index.html")
GIT = "/usr/bin/git"
MIN_BYTES = 20_000  # これより小さいのは取得失敗や空ファイルの疑い


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


def git(*args):
    return subprocess.run([GIT, "-C", HERE, *args], capture_output=True, text=True, timeout=120)


def main(argv):
    dry = "--dry-run" in argv
    try:
        data = open(SRC, "rb").read()
    except OSError as e:
        log(f"中止: 元ファイルを読めない ({e})")
        return 1
    if len(data) < MIN_BYTES or b"<title>" not in data:
        log(f"中止: 元ファイルが不正の疑い ({len(data)} bytes)。公開しない")
        return 1
    old = open(DST, "rb").read() if os.path.exists(DST) else b""
    if data == old:
        log("変更なし")
        return 0
    if dry:
        log(f"dry-run: 更新あり ({len(old)} → {len(data)} bytes)。書き込まない")
        return 0
    with open(DST, "wb") as f:
        f.write(data)
    for step in (
        ("add", "index.html"),
        ("commit", "-q", "-m", f"chore: 一覧を自動更新 {time.strftime('%Y-%m-%d')}"),
        ("push", "-q", "origin", "main"),
    ):
        r = git(*step)
        if r.returncode != 0:
            log(f"失敗: git {step[0]}: {r.stderr.strip()[:300]}")
            return 1
    log(f"公開: {len(data)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
