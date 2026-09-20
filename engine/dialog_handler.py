"""
dialog_handler.py - 自动对话框处理器
======================================
功能: 自动检测并点击 Windows 弹窗对话框
  - 包含「白名单」→ 自动按 Enter (运行白名单)
  - 包含「删除」  → 自动按 Enter (确认删除)
  - 包含「继续」  → 自动按 Enter (继续运行)

依赖: pygetwindow, pyautogui (通过 pip install pyautogui 自动安装)
用法:
  from engine.dialog_handler import start_dialog_handler
  start_dialog_handler()   # 启动后台守护线程
"""
import time
import threading

try:
    import pygetwindow as gw
    import pyautogui
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

# 检测间隔（秒）
CHECK_INTERVAL = 1.0

# 对话框匹配规则: 关键字 → 策略
DIALOG_RULES = {
    '白名单': 'enter',
    '删除':   'enter',
    '继续':   'enter',
}

_handled = set()
_handled_lock = threading.Lock()


def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] [dialog] {msg}')
    try:
        with open(__import__('os').path.join(
            __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))),
            'watcher.log'
        ), 'a', encoding='utf-8') as f:
            f.write(f'[{timestamp}] [dialog] {msg}\n')
    except Exception:
        pass


def handle_dialog(window):
    title = window.title
    hwnd = window._hWnd

    with _handled_lock:
        if hwnd in _handled:
            return False
        _handled.add(hwnd)

    matched_keyword = None
    for keyword in DIALOG_RULES:
        if keyword in title:
            matched_keyword = keyword
            break

    if matched_keyword is None:
        return False

    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.3)

        for _ in range(2):
            pyautogui.press('enter')
            time.sleep(0.15)

        log(f"已自动点击对话框: 「{title}」 → [{matched_keyword}]")
        return True
    except Exception as e:
        log(f"点击对话框失败: 「{title}」 → {e}")
        return False


def scan_dialogs():
    if not HAS_GUI:
        return
    try:
        for win in gw.getAllWindows():
            if win.title and win.visible:
                for keyword in DIALOG_RULES:
                    if keyword in win.title:
                        handle_dialog(win)
                        break
    except Exception:
        pass


def start_dialog_handler():
    if not HAS_GUI:
        log("pyautogui 未安装，对话框自动处理已禁用")
        log("请运行: pip install pyautogui")
        return None

    def _loop():
        log("对话框自动处理器已启动 (每1秒扫描)")
        while True:
            try:
                scan_dialogs()
            except Exception:
                pass
            time.sleep(CHECK_INTERVAL)

    t = threading.Thread(target=_loop, daemon=True, name='dialog-handler')
    t.start()
    log(f"对话框处理线程已启动 (PID: {threading.get_ident()})")
    return t


def test_scan():
    """测试模式: 列出当前所有可见窗口"""
    if not HAS_GUI:
        print("pygetwindow 未安装")
        return
    print("当前可见窗口列表:")
    for win in gw.getAllWindows():
        if win.title and win.visible:
            match = " ← 匹配" if any(k in win.title for k in DIALOG_RULES) else ""
            print(f"  HWND={win._hWnd} [{win.left},{win.top}] {win.width}x{win.height} 「{win.title}」{match}")


if __name__ == '__main__':
    print("=" * 60)
    print("  对话框自动处理器 — 测试模式")
    print("=" * 60)
    print("匹配规则:")
    for kw in DIALOG_RULES:
        print(f"  - 窗口标题包含「{kw}」→ 自动按 Enter")
    print("-" * 60)
    test_scan()
    print("-" * 60)
    print("开始监控 (按 Ctrl+C 退出)...")
    t = start_dialog_handler()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("已退出")
