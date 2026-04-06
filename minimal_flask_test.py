#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小 Flask 测试
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test')
def test():
    print("收到请求！")
    return jsonify({'success': True, 'message': 'Hello World'})

if __name__ == '__main__':
    from waitress import serve
    print("启动最小 Flask 应用...")
    serve(app, host='0.0.0.0', port=5000, threads=2)
