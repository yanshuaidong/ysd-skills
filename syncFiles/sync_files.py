#!/usr/bin/env python3
"""OpenClaw Workspace 文件同步守护进程

将本地 ~/.openclaw/workspace 增量同步到远程服务器。
内置定时调度器，每天 14:30 自动执行 rsync 同步。
无第三方 Python 依赖，仅需系统自带的 sshpass + rsync。
"""

import os
import sys
import signal
import subprocess
import argparse
import logging
import time
import atexit
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PID_FILE = SCRIPT_DIR / "sync.pid"
LOG_DIR = SCRIPT_DIR / "logs"
ENV_FILE = SCRIPT_DIR / ".env"

SOURCE_DIR = os.path.expanduser("~/.openclaw/workspace/")
REMOTE_HOST = "82.157.138.214"
REMOTE_USER = "root"
REMOTE_DIR = "/root/openclaw-workspace/"
SYNC_HOUR = 14
SYNC_MINUTE = 30

EXCLUDE_PATTERNS = [".git/", ".DS_Store", "__pycache__/"]

logger = logging.getLogger("sync_files")
_shutdown = False


def load_password() -> str:
    if not ENV_FILE.exists():
        logger.error(".env 文件不存在: %s", ENV_FILE)
        sys.exit(1)
    for line in ENV_FILE.read_text().strip().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "SYNC_PASSWORD":
            return value.strip()
    logger.error(".env 中未找到 SYNC_PASSWORD")
    sys.exit(1)


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"sync_{datetime.now():%Y-%m-%d}.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def write_pid():
    PID_FILE.write_text(str(os.getpid()))
    logger.info("PID %d 已写入 %s", os.getpid(), PID_FILE)


def remove_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()
        logger.info("PID 文件已清理")


def signal_handler(signum, _frame):
    global _shutdown
    sig_name = signal.Signals(signum).name
    logger.info("收到信号 %s，准备退出...", sig_name)
    _shutdown = True


def run_sync(dry_run: bool = False):
    password = load_password()

    cmd = ["sshpass", "-p", password, "rsync", "-avz", "--delete"]
    for pattern in EXCLUDE_PATTERNS:
        cmd += ["--exclude", pattern]
    cmd += ["-e", "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 -p 22"]
    if dry_run:
        cmd.append("--dry-run")
    cmd += [SOURCE_DIR, f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}"]

    logger.info(
        "开始%s同步: %s -> %s:%s",
        "预览" if dry_run else "",
        SOURCE_DIR,
        REMOTE_HOST,
        REMOTE_DIR,
    )
    start_ts = time.time()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elapsed = time.time() - start_ts

        if result.stdout:
            for line in result.stdout.strip().splitlines():
                logger.info("  %s", line)

        if result.returncode == 0:
            logger.info("同步%s完成 (%.1f秒)", "预览" if dry_run else "", elapsed)
        else:
            logger.error("同步失败 (exit=%d, %.1f秒)", result.returncode, elapsed)
            if result.stderr:
                for line in result.stderr.strip().splitlines():
                    logger.error("  %s", line)
    except FileNotFoundError:
        logger.error("sshpass 未安装，请运行: brew install hudochenkov/sshpass/sshpass")
    except subprocess.TimeoutExpired:
        logger.error("同步超时 (>300秒)")
    except Exception as e:
        logger.error("同步异常: %s", e)


def seconds_until_next_run() -> float:
    """计算距离下一次 SYNC_HOUR:SYNC_MINUTE 的秒数"""
    now = datetime.now()
    target = now.replace(hour=SYNC_HOUR, minute=SYNC_MINUTE, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    delta = (target - now).total_seconds()
    return delta


def daemon_loop():
    wait = seconds_until_next_run()
    next_run = datetime.now() + timedelta(seconds=wait)
    logger.info(
        "定时任务已注册: 每天 %02d:%02d 执行同步",
        SYNC_HOUR,
        SYNC_MINUTE,
    )
    logger.info("下次同步时间: %s", next_run.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("守护进程运行中，等待调度... (Ctrl+C 退出)")

    while not _shutdown:
        now = datetime.now()
        if now.hour == SYNC_HOUR and now.minute == SYNC_MINUTE:
            logger.info("=== 定时任务触发 ===")
            run_sync()
            # 等 60 秒避免同一分钟内重复触发
            for _ in range(60):
                if _shutdown:
                    break
                time.sleep(1)
            # 计算并显示下次运行时间
            if not _shutdown:
                wait = seconds_until_next_run()
                next_run = datetime.now() + timedelta(seconds=wait)
                logger.info(
                    "下次同步时间: %s",
                    next_run.strftime("%Y-%m-%d %H:%M:%S"),
                )
        else:
            for _ in range(30):
                if _shutdown:
                    break
                time.sleep(1)

    logger.info("守护进程已退出")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Workspace 文件同步")
    parser.add_argument("--now", action="store_true", help="立即执行一次同步")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际传输文件")
    parser.add_argument("--once", action="store_true", help="只执行一次，不启动守护进程")
    args = parser.parse_args()

    setup_logging()

    if args.once:
        run_sync(dry_run=args.dry_run)
        return

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    write_pid()
    atexit.register(remove_pid)

    if args.now:
        run_sync(dry_run=args.dry_run)

    daemon_loop()


if __name__ == "__main__":
    main()
