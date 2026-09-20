#!/usr/bin/env bash
# PATH 修复脚本（2026-09-11）
# 背景：WorkBuddy 启动 bash 子进程时 PATH 丢失 → shim(shell-runtime-bash-env.sh) 里
#       dirname/cd 找不到 → 所有 Unix 工具不可用（报 "command not found"）。
# 用法：在命令开头 source 本文件即可恢复全部基础工具。
#   source /e/仪度六壬择日/yiduluren/_fix_path.sh && <你的命令>
#
# 注：shim 仍会往 stderr 打两行 "dirname: command not found" 告警 —— **无害**
#     （它在 PATH 设置前先执行）。彻底修复需重启 WorkBuddy 应用/会话。

export PATH="/usr/bin:/bin:/c/Program Files/Git/usr/bin:/c/Users/Administrator/.workbuddy/binaries/PortableGit/versions/1.2.0/usr/bin:/c/Users/Administrator/.workbuddy/binaries/PortableGit/versions/1.2.0/bin:${PATH}"

# 便捷别名（仅当未定义时）
command -v ll >/dev/null 2>&1 || alias ll='ls -la'
