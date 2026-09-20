# -*- coding: utf-8 -*-
"""pytest 共享配置（2026-09-06 引入 pytest 统一测试框架）

职责：
  1. 根目录注入 sys.path（各测试文件不再自带 _ROOT 样板，pytest.ini pythonpath=. 兜底双保险）
  2. session 级 client fixture：Flask test_client（寻物入口 API 测试用；
     stock_dashboard.app 为模块级单例，惰性 import 一次即可）
"""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


@pytest.fixture(scope='session')
def root_path():
    """项目根目录（前端入口断言等读根文件用）。"""
    return _ROOT


@pytest.fixture(scope='session')
def client():
    """Flask test_client（import stock_dashboard 安全：app 模块级、akshare 无顶层预取、__main__ 守卫）。"""
    from stock_dashboard import app
    app.testing = True
    return app.test_client()