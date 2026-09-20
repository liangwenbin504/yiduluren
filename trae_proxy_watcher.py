"""
Trae 启动监控器 — 打开 Trae 时自动启动 DeepSeek 代理

========================================
  功能：
    开机后在后台静默运行，每5秒检测一次 Trae IDE 进程。
    一旦检测到 Trae 启动（或代理意外退出），自动拉起:
      deepseek_proxy.py (端口8765, image_url过滤代理)

  用法:
    python trae_proxy_watcher.py              # 前台运行
    python trae_proxy_watcher.py --test       # 自测模式(立即检测一次并退出)
========================================
"""
import os
import sys
import time
import subprocess
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

PROXY_SCRIPT = os.path.join(BASE, "deepseek_proxy.py")
PROXY_PORT = 8765
CHECK_INTERVAL = 5  # 秒

# Trae 进程名（多个变体）
TRAE_PROCESS_NAMES = [
    "TRAE SOLO CN",
    "TRAE SOLO",
    "Trae",
    "trae",
    "TRAE",
]


def beijing_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)


def log(msg):
    print(f"[监控] {beijing_now().strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


def is_trae_running():
    """检测 Trae IDE 是否在运行"""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info.get('name') or ""
                for t in TRAE_PROCESS_NAMES:
                    if t.lower() in name.lower():
                        return True
            except Exception:
                continue
        return False
    except ImportError:
        # psutil 不可用时回退到 tasklist
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq TRAE SOLO CN.exe'],
                capture_output=True, text=True, timeout=10,
            )
            return "TRAE SOLO CN.exe" in result.stdout
        except Exception:
            return True  # 检测失败时保守启动代理


def is_proxy_running():
    """检测代理端口是否已监听"""
    import socket
    try:
        with socket.create_connection(("127.0.0.1", PROXY_PORT), timeout=1):
            return True
    except Exception:
        return False


def start_proxy():
    """启动代理进程"""
    if is_proxy_running():
        log(f"✅ 代理已在运行 (端口 {PROXY_PORT})")
        return True

    try:
        # 隐藏窗口启动
        CREATE_NO_WINDOW = 0x08000000
        proc = subprocess.Popen(
            [sys.executable, PROXY_SCRIPT],
            cwd=BASE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
        # 等待2秒确认端口监听
        time.sleep(2)
        if is_proxy_running():
            log(f"✅ 代理已启动 (PID: {proc.pid}, 端口 {PROXY_PORT})")
            return True
        else:
            log(f"⚠️ 代理启动后端口未就绪 (PID: {proc.pid})")
            return False
    except Exception as e:
        log(f"❌ 启动代理失败: {e}")
        return False


def main():
    test_mode = "--test" in sys.argv

    log("=" * 50)
    log("Trae 启动监控器")
    log(f"监控间隔: {CHECK_INTERVAL}秒")
    log(f"代理脚本: {PROXY_SCRIPT}")
    log("=" * 50)

    # 自测模式
    if test_mode:
        t = is_trae_running()
        p = is_proxy_running()
        log(f"Trae 状态: {'运行中' if t else '未运行'}")
        log(f"代理状态: {'运行中' if p else '未运行'}")
        if t and not p:
            log("检测到 Trae 运行但代理未启动，拉起代理...")
            start_proxy()
        return

    # 常驻循环
    trae_was_running = is_trae_running()
    if trae_was_running:
        log("检测到 Trae 正在运行，确保代理已启动...")
        start_proxy()

    while True:
        trae_running = is_trae_running()
        proxy_running = is_proxy_running()

        if trae_running and not proxy_running:
            log("🚀 检测到 Trae 运行且代理未启动，自动拉起代理...")
            start_proxy()
        elif not trae_running and proxy_running:
            # Trae 未运行但代理在跑：保持运行（不关闭，避免反复启停）
            pass

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
