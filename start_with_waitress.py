# 生产级启动器：用 waitress 托管 Flask 应用（替代 flask 开发服务器）
# 用法：python start_with_waitress.py   （端口取环境变量 PORT，默认 5555）
import os
from waitress import serve
from stock_dashboard import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    # 默认只监听本机回环，仅允许本机 Nginx 反代访问，避免 5555 直接暴露公网
    bind = os.environ.get('BIND', '127.0.0.1')
    print(f"[waitress] 仪度六壬择日 启动于 {bind}:{port}")
    serve(app, host=bind, port=port, threads=8, channel_timeout=120)
