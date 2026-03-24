#!/bin/bash
#
# 停止 OpenClaw Workspace 文件同步守护进程

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/sync.pid"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# --- 检查 PID 文件 ---
if [ ! -f "$PID_FILE" ]; then
    warn "PID 文件不存在，守护进程可能未在运行"
    exit 0
fi

PID=$(cat "$PID_FILE")

if [ -z "$PID" ]; then
    warn "PID 文件为空，清理中..."
    rm -f "$PID_FILE"
    exit 0
fi

# --- 检查进程是否存活 ---
if ! kill -0 "$PID" 2>/dev/null; then
    warn "进程 $PID 已不存在，清理 PID 文件..."
    rm -f "$PID_FILE"
    exit 0
fi

# --- 发送 SIGTERM 优雅停止 ---
info "正在停止守护进程 (PID: $PID)..."
kill -TERM "$PID"

WAIT_SECONDS=10
for i in $(seq 1 $WAIT_SECONDS); do
    if ! kill -0 "$PID" 2>/dev/null; then
        info "守护进程已停止 (等待了 ${i} 秒)"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# --- 超时强杀 ---
warn "进程未在 ${WAIT_SECONDS} 秒内退出，强制终止..."
kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
info "守护进程已强制终止"
