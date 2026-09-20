#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测调度守护进程 v2.0
=========================
解决三大瓶颈：
  1. 调度器从不自动启动 → 本守护进程保证 24x7 运行
  2. 崩溃/重启后停止 → 自动重启 + 心跳监控
  3. 无启动入口 → 一键启动

功能：
  - 启动 auto_scheduler.py 并持续监控
  - 崩溃自动重启（最多3次/小时）
  - 每30秒写心跳文件
  - 支持 Windows 开机自启动（注册为计划任务）

用法：
  python stock_guardian.py              # 前台运行（可查看日志）
  python stock_guardian.py --daemon     # 后台运行
  python stock_guardian.py --install    # 注册 Windows 开机启动
  python stock_guardian.py --status     # 查看当前状态
"""

import os, sys, time, json, signal, subprocess, threading
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
HEARTBEAT_FILE = MEMORY / "guardian_heartbeat.json"
GUARDIAN_PID_FILE = MEMORY / "guardian.pid"
SCHEDULER_SCRIPT = BASE / "auto_scheduler.py"
MAX_RESTARTS_PER_HOUR = 3
CHECK_INTERVAL = 5  # 每5秒检查一次
HEARTBEAT_INTERVAL = 30  # 每30秒写心跳


class StockGuardian:
    """股票预测调度守护进程"""

    def __init__(self):
        self.process = None
        self.restart_count = 0
        self.restart_window_start = None
        self.running = True
        self.start_time = datetime.now()

    def log(self, msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {msg}", flush=True)

    def write_heartbeat(self):
        """写心跳文件"""
        MEMORY.mkdir(parents=True, exist_ok=True)
        heartbeat = {
            "timestamp": datetime.now().isoformat(),
            "scheduler_running": self.process is not None and self.process.poll() is None,
            "guardian_pid": os.getpid(),
            "restart_count": self.restart_count,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
        }
        with open(HEARTBEAT_FILE, 'w') as f:
            json.dump(heartbeat, f, indent=2)

    def start_scheduler(self):
        """启动调度器进程"""
        if self.process and self.process.poll() is None:
            self.log("调度器已在运行中，跳过启动")
            return True

        self.log("正在启动股票预测调度器...")
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(SCHEDULER_SCRIPT), "--foreground"],
                cwd=str(BASE),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
            )
            time.sleep(2)
            if self.process.poll() is None:
                self.log(f"✅ 调度器已启动 (PID: {self.process.pid})")
                return True
            else:
                self.log(f"❌ 调度器启动失败 (exit code: {self.process.poll()})")
                return False
        except Exception as e:
            self.log(f"❌ 启动异常: {e}")
            return False

    def restart_scheduler(self):
        """重启调度器（带限流）"""
        now = datetime.now()

        # 重置计数窗口（每小时）
        if self.restart_window_start is None or \
           (now - self.restart_window_start).total_seconds() > 3600:
            self.restart_window_start = now
            self.restart_count = 0

        if self.restart_count >= MAX_RESTARTS_PER_HOUR:
            self.log(f"⚠️ 每小时重启超过{MAX_RESTARTS_PER_HOUR}次，暂停60秒...")
            time.sleep(60)
            self.restart_window_start = datetime.now()
            self.restart_count = 0

        self.restart_count += 1
        self.log(f"🔄 重启调度器 (第{self.restart_count}次)")

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except:
                try:
                    self.process.kill()
                except:
                    pass

        time.sleep(3)
        return self.start_scheduler()

    def run(self):
        """主循环"""
        self.log("=" * 60)
        self.log("  股票预测调度守护进程 v2.0")
        self.log(f"  启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"  调度器脚本: {SCHEDULER_SCRIPT}")
        self.log(f"  心跳文件: {HEARTBEAT_FILE}")
        self.log("=" * 60)

        # 注册信号处理
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())

        # 启动调度器
        if not self.start_scheduler():
            self.log("❌ 首次启动失败，5秒后重试...")
            time.sleep(5)
            self.start_scheduler()

        last_heartbeat = 0

        while self.running:
            try:
                now = time.time()

                # 写心跳
                if now - last_heartbeat > HEARTBEAT_INTERVAL:
                    self.write_heartbeat()
                    last_heartbeat = now

                # 检查调度器是否存活
                if self.process:
                    rc = self.process.poll()
                    if rc is not None:
                        # 调度器退出了
                        self.log(f"⚠️ 调度器异常退出 (exit code: {rc})")
                        self.restart_scheduler()

                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                self.shutdown()
                break
            except Exception as e:
                self.log(f"⚠️ 异常: {e}")
                time.sleep(CHECK_INTERVAL)

    def shutdown(self):
        """优雅关闭"""
        self.log("正在关闭...")
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
        self.write_heartbeat()
        self.log("✅ 守护进程已停止")


def install_windows_startup():
    """注册 Windows 开机自启动（使用计划任务）"""
    import subprocess as sp

    script_path = Path(__file__).resolve()
    python_path = sys.executable

    # 创建 VBS 启动脚本（隐藏窗口）
    vbs_path = BASE / "_autostart_guardian.vbs"
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """{python_path}"" ""{script_path}"" --daemon", 0, False
'''
    with open(vbs_path, 'w') as f:
        f.write(vbs_content)

    # 删除旧任务
    sp.run(['schtasks', '/delete', '/tn', 'YiduLiuren_StockGuardian', '/f'],
           capture_output=True, shell=True)

    # 创建新任务
    result = sp.run([
        'schtasks', '/create', '/tn', 'YiduLiuren_StockGuardian',
        '/tr', f'wscript.exe "{vbs_path}"',
        '/sc', 'onlogon',
        '/rl', 'highest',
        '/f',
    ], capture_output=True, text=True, shell=True)

    if result.returncode == 0:
        print("✅ Windows 开机自启动已注册成功！")
        print(f"   任务名称: YiduLiuren_StockGuardian")
        print(f"   启动脚本: {vbs_path}")
    else:
        print(f"❌ 注册失败: {result.stderr}")
        print("   请以管理员身份运行此脚本")


def show_status():
    """显示当前状态"""
    print("=" * 50)
    print("  股票预测调度系统状态")
    print("=" * 50)

    # 心跳文件
    if HEARTBEAT_FILE.exists():
        with open(HEARTBEAT_FILE) as f:
            hb = json.load(f)
        last_ts = datetime.fromisoformat(hb["timestamp"])
        ago = (datetime.now() - last_ts).total_seconds()
        print(f"  守护进程: {'✅ 运行中' if ago < 120 else '❌ 已停止'}")
        print(f"  最后心跳: {last_ts.strftime('%H:%M:%S')} ({ago:.0f}秒前)")
        print(f"  调度器状态: {'✅ 运行中' if hb.get('scheduler_running') else '❌ 已停止'}")
        print(f"  运行时长: {hb.get('uptime_seconds', 0)/3600:.1f}小时")
    else:
        print(f"  守护进程: ❌ 未启动")

    # 预测记录
    pred_file = MEMORY / "stock_predictions.json"
    if pred_file.exists():
        with open(pred_file) as f:
            data = json.load(f)
        preds = data if isinstance(data, list) else data.get('predictions', [])
        today = datetime.now().strftime("%Y-%m-%d")
        today_preds = [p for p in preds if p.get('date') == today]
        completed = [p for p in preds if p.get('status') == 'completed']
        print(f"\n  总预测记录: {len(preds)}")
        print(f"  已完成对照: {len(completed)}")
        print(f"  今日预测: {len(today_preds)} 条")

    # 调度器日志
    log_file = MEMORY / "scheduler_log.json"
    if log_file.exists():
        with open(log_file) as f:
            logs = json.load(f)
        if logs:
            last = logs[-1]
            print(f"\n  最后调度事件: {last.get('time','?')[:19]}")
            print(f"  事件: {last.get('action','?')} {'✅' if last.get('success') else '❌'}")


def main():
    if "--install" in sys.argv:
        install_windows_startup()
    elif "--status" in sys.argv:
        show_status()
    elif "--daemon" in sys.argv:
        # 后台模式
        print("后台模式启动中...")
        guardian = StockGuardian()
        # 分离进程
        if os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.FreeConsole()
        guardian.run()
    else:
        # 前台模式
        guardian = StockGuardian()
        guardian.run()


if __name__ == "__main__":
    main()
