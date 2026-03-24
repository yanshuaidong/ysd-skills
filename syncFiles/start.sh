#!/bin/bash
#
# 启动 OpenClaw Workspace 文件同步守护进程
# 用法: bash start.sh [--now]
#   --now  启动后立即执行一次同步

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/sync.pid"
LOG_DIR="$SCRIPT_DIR/logs"
SYNC_SCRIPT="$SCRIPT_DIR/sync_files.py"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# --- 找到真实的 python3 路径（跳过 shell alias）---
PYTHON=""
for candidate in \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    /usr/bin/python3; do
    if [ -x "$candidate" ]; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    error "找不到 python3，请安装 Python 3"
    exit 1
fi

info "使用 Python: $PYTHON ($($PYTHON --version 2>&1))"

# --- 检查是否已在运行 ---
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        error "守护进程已在运行 (PID: $OLD_PID)"
        echo "  如需重启，请先运行: bash stop.sh"
        exit 1
    else
        warn "发现残留 PID 文件 (进程 $OLD_PID 已不存在)，清理中..."
        rm -f "$PID_FILE"
    fi
fi

# --- 检查 .env ---
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    error "缺少 .env 文件，请创建: $SCRIPT_DIR/.env"
    echo "  格式: SYNC_PASSWORD=your_password"
    exit 1
fi

# --- 检查 sshpass ---
if ! command -v sshpass &>/dev/null; then
    warn "sshpass 未安装，正在通过 Homebrew 安装..."
    if ! command -v brew &>/dev/null; then
        error "Homebrew 未安装，请先安装 Homebrew: https://brew.sh"
        exit 1
    fi
    brew install hudochenkov/sshpass/sshpass
    info "sshpass 安装完成"
fi

# --- 创建日志目录 ---
mkdir -p "$LOG_DIR"

# --- 启动守护进程 ---
EXTRA_ARGS=""
if [[ "$1" == "--now" ]]; then
    EXTRA_ARGS="--now"
    info "启动后将立即执行一次同步"
fi

TODAY=$(date +%Y-%m-%d)
nohup "$PYTHON" "$SYNC_SCRIPT" $EXTRA_ARGS >> "$LOG_DIR/sync_${TODAY}.log" 2>&1 &
DAEMON_PID=$!

sleep 1

if kill -0 "$DAEMON_PID" 2>/dev/null; then
    info "守护进程启动成功"
    echo ""
    echo "  PID:      $DAEMON_PID"
    echo "  PID 文件: $PID_FILE"
    echo "  日志目录: $LOG_DIR"
    echo "  同步时间: 每天 14:30"
    echo ""
    echo "  停止命令: bash $SCRIPT_DIR/stop.sh"
    echo "  查看日志: tail -f $LOG_DIR/sync_${TODAY}.log"
else
    error "守护进程启动失败，请查看日志: $LOG_DIR/sync_${TODAY}.log"
    exit 1
fi
