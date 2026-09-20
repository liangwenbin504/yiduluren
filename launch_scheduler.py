# -*- coding: utf-8 -*-
"""
调度器自启动器（由 Windows 任务计划程序调用，pythonw 无窗口运行）。

使用持久端口绑定作为互斥锁，确保只有一个实例运行。
"""
import os
import sys

# ── 确保 venv 包可访问（支持系统 Python 直接调用，跳过 venv launcher）──
_HERE = os.path.dirname(os.path.abspath(__file__))
_VENV_SITE = os.path.join(_HERE, '.venv', 'Lib', 'site-packages')
if _VENV_SITE not in sys.path:
    sys.path.insert(0, _VENV_SITE)

import socket

MUTEX_PORT = 15556
ROOT = os.path.dirname(os.path.abspath(__file__))

# ── 模块级互斥锁 ──
try:
    _mutex_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _mutex_sock.bind(('127.0.0.1', MUTEX_PORT))
    _mutex_sock.listen(1)
except OSError:
    sys.exit(0)  # 已有实例运行，静默退出


def main():
    os.chdir(ROOT)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import auto_scheduler
    auto_scheduler.run_scheduler()


if __name__ == '__main__':
    main()
