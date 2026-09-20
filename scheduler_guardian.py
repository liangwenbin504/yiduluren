"""
调度器守护程序 — 防误杀保护

功能:
  1. 启动 auto_scheduler.py 作为子进程
  2. 显示一个小型保护窗口（可最小化）
  3. 子进程被杀死时自动弹窗提示，可选择重启或退出
  4. 守护窗口关闭时也需确认

用法:
  python scheduler_guardian.py              # 启动守护模式
  python scheduler_guardian.py --minimized   # 最小化启动
"""
import os, sys, subprocess, time, threading, signal, atexit
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

# 全局变量
_scheduler_proc = None
_guard_window = None
_running = True
_restarting = False


def _beijing_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)


def _log(msg):
    print(f"[守护] {_beijing_now().strftime('%H:%M:%S')} {msg}", flush=True)


def start_scheduler():
    """启动调度器子进程"""
    global _scheduler_proc
    
    if _scheduler_proc is not None and _scheduler_proc.poll() is None:
        _log("调度器已在运行")
        return True
    
    try:
        _scheduler_proc = subprocess.Popen(
            [sys.executable, "auto_scheduler.py"],
            cwd=BASE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )
        _log(f"调度器已启动 (PID: {_scheduler_proc.pid})")
        
        # 启动输出监控线程
        t = threading.Thread(target=_monitor_output, daemon=True)
        t.start()
        
        # 启动状态监控线程
        t2 = threading.Thread(target=_monitor_process, daemon=True)
        t2.start()
        
        return True
    except Exception as e:
        _log(f"启动失败: {e}")
        return False


def _monitor_output():
    """实时转发调度器输出"""
    if not _scheduler_proc:
        return
    for line in iter(_scheduler_proc.stdout.readline, b''):
        if line:
            try:
                text = line.decode('utf-8', errors='replace').rstrip()
                print(text, flush=True)
            except Exception:
                pass
        else:
            break


def _monitor_process():
    """监控子进程状态，异常退出时弹窗"""
    global _running, _restarting
    
    while _running:
        if _scheduler_proc is None:
            time.sleep(1)
            continue
            
        ret = _scheduler_proc.poll()
        if ret is not None:
            # 子进程已退出
            if _restarting or not _running:
                break
            
            exit_type = "正常退出" if ret == 0 else f"异常退出(码:{ret})"
            _log(f"⚠️ 调度器{exit_type}!")
            
            # 弹窗询问
            import tkinter as tk
            from tkinter import messagebox as msgbox
            
            root = tk.Tk()
            root.withdraw()
            
            result = msgbox.askyesno(
                "调度器保护",
                f"⚠️ 大六壬自动调度器{exit_type}！\n\n"
                f"PID: {_scheduler_proc.pid}\n"
                f"时间: {_beijing_now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"是否重新启动调度器？",
                icon='warning'
            )
            
            root.destroy()
            
            if result and _running:
                _log("用户选择 → 重新启动...")
                time.sleep(1)
                start_scheduler()
            else:
                _log("用户选择 → 不重启")
                _running = False
                if _guard_window:
                    _guard_window.destroy()
            break
        
        time.sleep(2)


def stop_scheduler(force=False):
    """停止调度器子进程"""
    global _scheduler_proc
    
    if _scheduler_proc is None or _scheduler_proc.poll() is not None:
        return True
    
    if force:
        try:
            _scheduler_proc.kill()
            _log("调度器已强制终止")
        except Exception:
            pass
        _scheduler_proc = None
        return True
    
    # 先尝试优雅关闭
    try:
        _scheduler_proc.terminate()
        # 等待5秒
        try:
            _scheduler_proc.wait(timeout=5)
            _log("调度器已优雅停止")
        except subprocess.TimeoutExpired:
            _scheduler_proc.kill()
            _log("调度器超时，已强制终止")
    except Exception as e:
        _log(f"停止失败: {e}")
    
    _scheduler_proc = None
    return True


def create_guard_window(minimized=False):
    """创建守护窗口（带防误杀确认）"""
    global _guard_window
    
    import tkinter as tk
    from tkinter import ttk, messagebox as msgbox
    
    root = tk.Tk()
    _guard_window = root
    
    root.title("🛡️ 调度器守护 - 大六壬预测系统")
    root.geometry("420x380+100+100")
    root.resizable(True, True)
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap(default='')
    except Exception:
        pass
    
    # 禁止默认关闭行为
    def on_closing():
        global _running
        result = msgbox.askyesno(
            "确认退出",
            "⚠️ 您正在关闭调度器守护程序！\n\n"
            "关闭后，自动预测和对照分析将停止运行。\n"
            "确定要退出吗？\n\n"
            "点击【是】→ 确认退出\n"
            "点击【否】→ 继续运行（窗口最小化）",
            icon='question'
        )
        if result:
            _log("用户确认退出")
            _running = False
            stop_scheduler(force=True)
            root.destroy()
        else:
            _log("用户取消退出，继续运行")
            root.iconify()  # 最小化而不是关闭
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 标题区
    title_frame = ttk.Frame(root, padding=10)
    title_frame.pack(fill=tk.X)
    
    ttk.Label(title_frame, text="🛡️ 大六壬自动调度器", font=('Microsoft YaHei UI', 14, 'bold')).pack(anchor=tk.W)
    
    status_label = ttk.Label(title_frame, text="● 启动中...", foreground='orange', font=('Microsoft YaHei UI', 10))
    status_label.pack(anchor=tk.W, pady=(5, 0))
    
    # 信息区
    info_frame = ttk.LabelFrame(root, text=" 运行信息 ", padding=10)
    info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    info_text = tk.Text(info_frame, height=12, wrap=tk.WORD, font=('Consolas', 9),
                       bg='#1e1e1e', fg='#d4d4d4',
                       insertbackground='white',
                       state=tk.DISABLED)
    info_text.pack(fill=tk.BOTH, expand=True)
    
    # 按钮区
    btn_frame = ttk.Frame(root, padding=10)
    btn_frame.pack(fill=tk.X)
    
    def on_restart():
        global _restarting
        _restarting = True
        stop_scheduler()
        time.sleep(1)
        _restarting = False
        start_scheduler()
        update_status(status_label, info_text)
    
    def on_stop():
        result = msgbox.askyesno(
            "停止调度器",
            "确定要停止自动调度器吗？\n\n"
            "停止后将不会自动执行预测和对照分析。",
            icon='question'
        )
        if result:
            stop_scheduler()
            update_status(status_label, info_text)
    
    def on_minimize():
        root.iconify()
    
    ttk.Button(btn_frame, text="🔄 重启调度器", command=on_restart).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="⏹ 停止调度器", command=on_stop).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="📋 最小化", command=on_minimize).pack(side=tk.RIGHT, padx=2)
    ttk.Button(btn_frame, text="❌ 退出守护", command=on_closing).pack(side=tk.RIGHT, padx=2)
    
    def update_status(lbl, txt):
        global _scheduler_proc
        
        if _scheduler_proc and _scheduler_proc.poll() is None:
            lbl.config(text=f"● 运行中 (PID: {_scheduler_proc.pid})", foreground='green')
        else:
            lbl.config(text="● 未运行", foreground='red')
        
        txt.config(state=tk.NORMAL)
        txt.delete(1.0, tk.END)
        
        lines = [
            f"守护启动时间: {_beijing_now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"调度器PID: {_scheduler_proc.pid if _scheduler_proc else 'N/A'}",
            f"调度器状态: {'运行中' if (_scheduler_proc and _scheduler_proc.poll() is None) else '未运行'}",
            f"",
            f"━━━ 保护说明 ━━━",
            f"• 关闭此窗口时会弹出确认框",
            f"• 调度器被意外终止时会自动提醒",
            f"• 可选择重启或彻底退出",
            f"",
            f"━━━ 调度规则 ━━━",
            f"• 交易日 09:00~14:00 自动占课",
            f"• 交易日 15:30 自动对照分析",
            f"• 周末休市不执行操作",
        ]
        txt.insert(tk.END, '\n'.join(lines))
        txt.config(state=tk.DISABLED)
    
    # 定时刷新状态
    def refresh_status():
        if _running:
            update_status(status_label, info_text)
            root.after(3000, refresh_status)
    
    # 启动后初始化
    root.after(500, lambda: [
        start_scheduler(),
        update_status(status_label, info_text),
        refresh_status(),
        _log("守护窗口已创建"),
    ])
    
    if minimized:
        root.after(1000, root.iconify)
    
    root.mainloop()


def main():
    global _running
    
    minimized = "--minimized" in sys.argv
    
    _log("=" * 50)
    _log("调度器守护程序启动")
    _log(f"工作目录: {BASE}")
    _log("=" * 50)
    
    create_guard_window(minimized=minimized)
    
    _log("守护程序退出")


if __name__ == "__main__":
    main()
