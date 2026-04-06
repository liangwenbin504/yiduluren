#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 Flask 调试模式启动（为了查看详细错误）
"""

from api_server import app

print("=" * 60)
print("⚠️ 警告：调试模式已启用，仅用于开发测试！")
print("=" * 60)
print("服务地址：http://localhost:5000")
print("调试模式：ON")
print("=" * 60)

# 使用 Flask 调试模式启动
app.run(host='0.0.0.0', port=5000, debug=True, threaded=False)
