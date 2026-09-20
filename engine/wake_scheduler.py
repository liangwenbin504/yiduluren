"""
Windows 唤醒调度器

功能：
  1. 在每次预测时间到达前，设置电脑唤醒定时器
  2. 电脑从睡眠中唤醒后自动执行预测
  3. 预测完成后可让电脑重新进入睡眠（可选）

原理：
  使用 Windows Task Scheduler 创建一次性唤醒任务，
  任务触发时从睡眠中唤醒电脑，运行预测脚本，然后自清理。
"""
import subprocess
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK_PREFIX = "DaLiuRenWake_"
PYTHON_EXE = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"

# ── PowerShell 脚本模板 ──

_CREATE_WAKE_TASK = """
$ErrorActionPreference = 'Stop'
$taskName = "{task_name}"
$scriptPath = "{script_path}"
$args = "{args}"
$hour = {hour}
$minute = {minute}

# 创建每日重复任务（周末由脚本内部判断是否执行）
$action = New-ScheduledTaskAction -Execute "{pythonExe}" -Argument "$scriptPath $args" -WorkingDirectory "{working_dir}"
$trigger = New-ScheduledTaskTrigger -Daily -At "$($hour.ToString('00')):$($minute.ToString('00'))"
$settings = New-ScheduledTaskSettingsSet `
    -WakeToRun `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -DisallowStartOnRemoteAppSession:$false `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force -ErrorAction Stop

Start-Sleep -Seconds 1
$next = (Get-ScheduledTask -TaskName $taskName -EA SilentlyContinue).NextRunTime
if ($next) {
    Write-Output "OK: {label} -> $($next.ToString('MM-dd HH:mm')) (daily recurring)"
} else {
    $timeStr = "$($hour.ToString('00')):$($minute.ToString('00'))"
    Write-Output "OK: {label} -> $timeStr (daily recurring)"
}
"""

_DELETE_TASK = """
$taskName = "{task_name}"
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Output "OK: $taskName deleted"
"""

_LIST_TASKS = """
Get-ScheduledTask -TaskName "{prefix}*" -ErrorAction SilentlyContinue |
    Select-Object TaskName, @{N='NextRunTime';E={$_.NextRunTime.ToString('MM-dd HH:mm')}},
                         State | Format-Table -AutoSize
"""

_CLEAR_ALL = """
Get-ScheduledTask -TaskName "{prefix}*" -ErrorAction SilentlyContinue |
    Unregister-ScheduledTask -Confirm:$false
Write-Output "OK: all wake tasks cleared"
"""


def _render(template: str, **kwargs) -> str:
    """安全的模板替换 — 只替换 {key} 占位符，不碰 PowerShell 的花括号"""
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


def _run_ps(script: str) -> tuple[bool, str]:
    """执行 PowerShell 脚本，返回 (成功, 输出)"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30
        )
        out = (result.stdout + result.stderr).strip()
        return result.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, "PowerShell 执行超时"
    except FileNotFoundError:
        return False, "PowerShell 不可用"
    except Exception as e:
        return False, str(e)


def set_wake(category: str, hour: int, minute: int, label: str = "") -> tuple[bool, str]:
    """
    创建一条唤醒任务。

    参数：
      category : fixed_time / ri_gan_pian_cai / ri_zhi_pian_cai / ri_gan_shi_shen / ri_zhi_shi_shen / ri_gan_zheng_yin / ri_gan_pian_yin / ri_zhi_zheng_yin / ri_zhi_pian_yin / random / manual
      hour, minute : 唤醒时间（24小时制）
      label : 显示标签（如"固定时辰课"）

    返回：
      (成功, 描述文字)
    """
    task_name = f"{TASK_PREFIX}{category}"
    script_path = os.path.join(BASE, "stock_daily_predict.py")
    args = f"--category {category}"
    working_dir = BASE
    label = label or category

    script = _render(_CREATE_WAKE_TASK,
        task_name=task_name,
        script_path=script_path,
        args=args,
        hour=hour,
        minute=minute,
        working_dir=working_dir,
        label=label,
        pythonExe=PYTHON_EXE,
    )
    ok, out = _run_ps(script)
    return ok, out


def set_review_wake(hour: int = 15, minute: int = 30):
    """创建盘后分析唤醒任务"""
    task_name = f"{TASK_PREFIX}review"
    script_path = os.path.join(BASE, "auto_review.py")
    args = ""
    working_dir = BASE

    script = _render(_CREATE_WAKE_TASK,
        task_name=task_name,
        script_path=script_path,
        args=args,
        hour=hour,
        minute=minute,
        working_dir=working_dir,
        label="盘后分析",
        pythonExe=PYTHON_EXE,
    )
    ok, out = _run_ps(script)
    return ok, out


def cancel_wake(category: str) -> tuple[bool, str]:
    """取消指定类别的唤醒任务"""
    task_name = f"{TASK_PREFIX}{category}"
    script = _render(_DELETE_TASK, task_name=task_name)
    return _run_ps(script)


def cancel_review_wake():
    """取消盘后分析唤醒任务"""
    task_name = f"{TASK_PREFIX}review"
    script = _render(_DELETE_TASK, task_name=task_name)
    return _run_ps(script)


def list_wake_tasks() -> str:
    """列出所有唤醒任务"""
    script = _render(_LIST_TASKS, prefix=TASK_PREFIX)
    ok, out = _run_ps(script)
    if ok and out:
        return out
    return "（无唤醒任务）"


def clear_all_wake_tasks() -> tuple[bool, str]:
    """清除所有唤醒任务"""
    script = _render(_CLEAR_ALL, prefix=TASK_PREFIX)
    return _run_ps(script)


def set_next_predict_wake() -> str:
    """
    自动计算下一次需要唤醒的时间，创建唤醒任务。
    由 auto_scheduler.py 在每次预测完成后调用。

    返回：描述文字
    """
    sys.path.insert(0, BASE)
    from engine.experiment_engine import get_today_schedule
    from datetime import date

    today = date.today()
    sched = get_today_schedule(today)
    lines = []

    for entry in sched:
        cat = entry["category"]
        cat_minute = entry["minute"]

        hour = cat_minute // 60
        minute = cat_minute % 60
        ok, out = set_wake(cat, hour, minute, entry["label"])
        if ok:
            lines.append(f"  ✓ {entry['label']} → {hour:02d}:{minute:02d} 唤醒已设定")
        else:
            lines.append(f"  ✗ {entry['label']} → 设定失败: {out[:80]}")

    ok, out = set_review_wake()
    if ok:
        lines.append(f"  ✓ 盘后分析 → 15:30 唤醒已设定")
    else:
        lines.append(f"  ✗ 盘后分析 → 设定失败: {out[:80]}")

    return "\n".join(lines) if lines else "  （今日所有排程已过期）"


def put_computer_to_sleep(delay_seconds: int = 60):
    """
    让电脑进入睡眠模式（在所有任务完成后调用）。
    延迟几秒，确保日志写完。
    """
    ps = f"""
    Start-Sleep -Seconds {delay_seconds}
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.Application]::SetSuspendState('Sleep', $false, $false)
    """
    subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", ps],
        creationflags=subprocess.CREATE_NO_WINDOW
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        print(list_wake_tasks())
    elif len(sys.argv) > 1 and sys.argv[1] == "clear":
        ok, out = clear_all_wake_tasks()
        print(out)
    elif len(sys.argv) > 1 and sys.argv[1] == "set":
        result = set_next_predict_wake()
        print(result)
    elif len(sys.argv) > 1 and sys.argv[1] == "sleep":
        delay = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        put_computer_to_sleep(delay)
        print(f"  电脑将在 {delay} 秒后进入睡眠...")
    else:
        print("用法:")
        print("  python engine/wake_scheduler.py list    — 查看所有唤醒任务")
        print("  python engine/wake_scheduler.py clear   — 清除所有唤醒任务")
        print("  python engine/wake_scheduler.py set     — 设置下一次唤醒")
        print("  python engine/wake_scheduler.py sleep   — 让电脑进入睡眠")
