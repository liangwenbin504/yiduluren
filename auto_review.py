#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动盘后对照分析 — 调用 stock_result_check.py --auto"""
import subprocess, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
target_date = sys.argv[1] if len(sys.argv) > 1 else None

cmd = [sys.executable, "stock_result_check.py", "--auto"]
if target_date:
    cmd.append(target_date)

result = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
print(result.stdout, flush=True)
if result.stderr:
    print(result.stderr, flush=True)
sys.exit(result.returncode)
