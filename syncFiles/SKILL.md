# syncFiles — OpenClaw Workspace 文件同步

将本地 `~/.openclaw/workspace` 目录自动同步到远程服务器，基于 rsync 增量同步，作为后台守护进程运行。

## 同步信息

| 项目 | 值 |
|------|-----|
| 源目录 | `/Users/yanshuaidong/.openclaw/workspace/` |
| 目标服务器 | `82.157.138.214` (root) |
| 目标目录 | `/root/openclaw-workspace/` |
| 同步频率 | 每天 14:30 |
| 同步方式 | rsync over SSH（增量同步） |

## 触发条件

- **自动触发：** 守护进程启动后，每天 14:30 (Asia/Shanghai) 自动执行
- **手动触发：** 可通过命令行随时手动同步

---

## 启动 / 停止

### 启动守护进程

```bash
cd syncFiles && bash start.sh
```

启动后立即同步一次：

```bash
cd syncFiles && bash start.sh --now
```

### 停止守护进程

```bash
cd syncFiles && bash stop.sh
```

### 查看运行状态

```bash
cat syncFiles/sync.pid && ps aux | grep sync_files
```

---

## 手动同步

不启动守护进程，只执行一次同步：

```bash
python syncFiles/sync_files.py --now --once
```

预览同步内容（不实际传输）：

```bash
python syncFiles/sync_files.py --dry-run --once
```

---

## 日志

日志按天存储在 `syncFiles/logs/` 目录：

```bash
# 查看今天的日志
cat syncFiles/logs/sync_$(date +%Y-%m-%d).log

# 实时跟踪日志
tail -f syncFiles/logs/sync_$(date +%Y-%m-%d).log
```

---

## 文件结构

```
syncFiles/
  sync_files.py    # 守护进程主程序
  start.sh         # 启动脚本
  stop.sh          # 停止脚本
  .env             # 密码配置（不进 git）
  SKILL.md         # 本文件
  sync.pid         # PID 文件（运行时生成）
  logs/            # 日志目录（运行时生成）
```

## 排除规则

以下文件/目录不会被同步到远程服务器：

- `.git/`
- `.DS_Store`
- `__pycache__/`

## 依赖

- `sshpass` — 通过 Homebrew 安装：`brew install hudochenkov/sshpass/sshpass`
- `schedule` — Python 定时调度库：`pip3 install schedule`

`start.sh` 会自动检查并安装以上依赖。
