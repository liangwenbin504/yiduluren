#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调度器健康监控 + 自动重启
=======================
每分钟检查 auto_scheduler 进程是否存活，异常退出时自动重启并记录。

用法：
  python health_monitor.py
  python health_monitor.py --daemon   # 后台运行
"""

import os, sys, time, json, subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
HEALTH_LOG = MEMORY / "health_monitor.json"

os.makedirs(MEMORY, exist_ok=True)


def get_beijing_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)


def log_event(event_type, detail=""):
    """记录健康事件"""
    events = []
    if HEALTH_LOG.exists():
        with open(HEALTH_LOG, 'r') as f:
            events = json.load(f)
    events.append({
        "time": get_beijing_now().isoformat(),
        "type": event_type,
        "detail": detail,
    })
    # 只保留最近100条
    events = events[-100:]
    with open(HEALTH_LOG, 'w') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def check_scheduler_alive():
    """检查auto_scheduler进程是否存活"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=5
        )
        # 简单检查：看是否有python进程（无法精确判断哪个是scheduler）
        # 改用检查心跳文件
        heartbeat = MEMORY / "scheduler_heartbeat.txt"
        if heartbeat.exists():
            mtime = datetime.fromtimestamp(heartbeat.stat().st_mtime)
            age = (datetime.now() - mtime).total_seconds()
            if age < 300:  # 5分钟内有更新
                return True, f"心跳正常 ({(age//60):.0f}分钟前)"
            else:
                return False, f"心跳超时 ({age:.0f}秒前)"
        return False, "心跳文件不存在"
    except Exception as e:
        return False, f"检查异常: {e}"


def restart_scheduler():
    """重启调度器"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 重启调度器...")
    try:
        # 先杀掉可能的残留进程
        subprocess.run(['taskkill', '/F', '/FI', 'WINDOWTITLE eq *stock_guardian*'],
                       capture_output=True)
        time.sleep(2)

        # 启动
        proc = subprocess.Popen(
            [sys.executable, str(BASE / 'auto_scheduler.py')],
            cwd=str(BASE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log_event("restart", f"PID={proc.pid}")
        return True, f"PID={proc.pid}"
    except Exception as e:
        log_event("restart_failed", str(e))
        return False, str(e)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="持续守护模式")
    parser.add_argument("--once", action="store_true", help="检查一次")
    args = parser.parse_args()

    if args.once:
        alive, msg = check_scheduler_alive()
        print(f"[{'✅' if alive else '❌'}] 调度器状态: {msg}")
        return

    print("=" * 50)
    print("  🩺 调度器健康监控")
    print(f"  启动: {get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    restart_count = 0
    max_restarts_per_hour = 5

    while True:
        alive, msg = check_scheduler_alive()

        if not alive:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ❌ 调度器异常: {msg}")

            # 检查重启频率
            recent = []
            if HEALTH_LOG.exists():
                with open(HEALTH_LOG, 'r') as f:
                    recent = json.load(f)
            hour_ago = (get_beijing_now() - timedelta(hours=1)).isoformat()
            recent_restarts = sum(1 for e in recent if e['type'] == 'restart' and e['time'] > hour_ago)

            if recent_restarts >= max_restarts_per_hour:
                print(f"  ⚠️ 1小时内已重启{recent_restarts}次，暂停守护，等待手动排查")
                log_event("pause", f"1小时内重启{recent_restarts}次")
                time.sleep(1800)  # 等30分钟
                continue

            ok, detail = restart_scheduler()
            if ok:
                print(f"  ✅ 调度器已重启 ({detail})")
                restart_count += 1
            else:
                print(f"  ❌ 重启失败: {detail}")
        else:
            # 每10分钟输出一次心跳确认
            now = datetime.now()
            if now.minute % 10 == 0 and now.second < 60:
                print(f"[{now.strftime('%H:%M:%S')}] ✅ {msg}")

        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    main()
