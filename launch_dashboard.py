# -*- coding: utf-8 -*-
"""
仪表盘自启动器（由 Windows 任务计划程序调用，pythonw 无窗口运行）。

使用持久端口绑定作为互斥锁，确保只有一个实例运行。
"""
import os
import sys

# ── 确保 venv 包可访问（支持系统 Python 直接调用，跳过 venv launcher）──
_HERE = os.path.dirname(os.path.abspath(__file__))
_VENV_SITE = os.path.join(_HERE, '.venv', 'Lib', 'site-packages')
if _VENV_SITE not in sys.path:
    sys.path.insert(0, _VENV_SITE)

import io
import socket
import traceback
import time

PORT = 5555
MUTEX_PORT = 15555
ROOT = os.path.dirname(os.path.abspath(__file__))
ERR_LOG = os.path.join(ROOT, '_memory', 'launch_dashboard.err')

# ── 模块级互斥锁：绑定端口确保单一实例 ──
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

    import stock_dashboard

    # ── pythonw 安全网：stock_dashboard 已处理模块级重定向，
    #     这里作为二次保险确保 Flask 日志不会因 None stdout 崩溃 ──
    class _FileBinary(io.RawIOBase):
        def __init__(self, f):
            self._f = f

        def writable(self):
            return True

        def readable(self):
            return False

        def seekable(self):
            return False

        def write(self, b):
            self._f.write(b.decode('utf-8', errors='replace'))
            return len(b)

        def flush(self):
            self._f.flush()

        def close(self):
            pass

    if sys.stdout is None:
        _outf = open(os.path.join(ROOT, '_memory', 'dashboard.out.log'), 'a', encoding='utf-8')
        sys.stdout = io.TextIOWrapper(_FileBinary(_outf), encoding='utf-8', errors='replace')
    if sys.stderr is None:
        _errf = open(os.path.join(ROOT, '_memory', 'dashboard.err.log'), 'a', encoding='utf-8')
        sys.stderr = io.TextIOWrapper(_FileBinary(_errf), encoding='utf-8', errors='replace')

    stock_dashboard.app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        try:
            with open(ERR_LOG, 'a', encoding='utf-8') as f:
                f.write('\n'.join([
                    '==== crash @ ' + __import__('datetime').datetime.now().isoformat(),
                    traceback.format_exc(), '',
                ]))
        except Exception:
            pass
        raise
