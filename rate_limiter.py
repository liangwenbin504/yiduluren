#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
请求限流和缓存策略模块
用于保护 API 免受过度请求和资源耗尽
"""

import time
from functools import wraps
from threading import Lock
from collections import defaultdict
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


class RateLimiter:
    """令牌桶限流器"""
    
    def __init__(self, rate: float = 10.0, capacity: float = 20.0):
        """
        初始化限流器
        
        Args:
            rate: 令牌生成速率（个/秒）
            capacity: 桶容量（最大令牌数）
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = Lock()
    
    def acquire(self, tokens: float = 1.0) -> bool:
        """
        获取令牌
        
        Args:
            tokens: 需要的令牌数
            
        Returns:
            是否成功获取
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # 添加令牌
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            # 检查是否有足够令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_token(self, tokens: float = 1.0, timeout: float = 30.0) -> bool:
        """
        等待令牌（阻塞式）
        
        Args:
            tokens: 需要的令牌数
            timeout: 最大等待时间（秒）
            
        Returns:
            是否成功获取
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.acquire(tokens):
                return True
            time.sleep(0.1)  # 等待 100ms
        
        return False


class RequestRateLimiter:
    """基于请求者的限流器"""
    
    def __init__(self):
        """初始化请求限流器"""
        self.limiters: Dict[str, RateLimiter] = {}
        self.lock = Lock()
        
        # 默认配置
        self.default_rate = 10.0  # 10 请求/秒
        self.default_capacity = 20.0  # 最大 20 请求
    
    def get_limiter(self, key: str) -> RateLimiter:
        """获取或创建限流器"""
        with self.lock:
            if key not in self.limiters:
                self.limiters[key] = RateLimiter(self.default_rate, self.default_capacity)
            return self.limiters[key]
    
    def is_allowed(self, key: str, tokens: float = 1.0) -> Tuple[bool, float]:
        """
        检查请求是否被允许
        
        Args:
            key: 请求者标识（如 IP 地址）
            tokens: 需要的令牌数
            
        Returns:
            (是否允许，剩余令牌数)
        """
        limiter = self.get_limiter(key)
        allowed = limiter.acquire(tokens)
        remaining = limiter.tokens
        
        return allowed, remaining


class ResponseCache:
    """响应缓存管理器"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认 TTL（秒）
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.lock = Lock()
        self.access_times: Dict[str, float] = {}
    
    def _generate_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        import hashlib
        key_data = f"{endpoint}:{sorted(params.items())}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """获取缓存的响应"""
        key = self._generate_key(endpoint, params)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # 检查是否过期
                if time.time() - entry['timestamp'] < entry['ttl']:
                    # 更新访问时间（LRU）
                    self.access_times[key] = time.time()
                    return entry['data']
                else:
                    # 删除过期条目
                    del self.cache[key]
                    del self.access_times[key]
        
        return None
    
    def set(self, endpoint: str, params: Dict[str, Any], data: Any, ttl: int = None):
        """缓存响应"""
        key = self._generate_key(endpoint, params)
        
        with self.lock:
            # 如果缓存已满，删除最久未使用的条目
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times, key=self.access_times.get)
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'ttl': ttl or self.default_ttl
            }
            self.access_times[key] = time.time()
    
    def invalidate(self, endpoint: str = None):
        """清除缓存"""
        with self.lock:
            if endpoint:
                # 清除特定端点的缓存
                keys_to_delete = [
                    k for k, v in self.cache.items()
                    if k.startswith(endpoint)
                ]
                for key in keys_to_delete:
                    del self.cache[key]
                    del self.access_times[key]
            else:
                # 清除所有缓存
                self.cache.clear()
                self.access_times.clear()
    
    def cleanup_expired(self):
        """清理所有过期条目"""
        with self.lock:
            now = time.time()
            keys_to_delete = [
                k for k, v in self.cache.items()
                if now - v['timestamp'] >= v['ttl']
            ]
            
            for key in keys_to_delete:
                del self.cache[key]
                del self.access_times[key]


# 全局实例
request_limiter = RequestRateLimiter()
response_cache = ResponseCache(max_size=1000, default_ttl=300)


def rate_limit(limit: float = 10.0, capacity: float = 20.0):
    """
    限流装饰器
    
    使用示例:
    @app.route('/api/test')
    @rate_limit(limit=5.0, capacity=10.0)
    def test_api():
        return jsonify({'success': True})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, jsonify
            
            # 获取请求者标识（IP 地址）
            client_ip = request.remote_addr or 'unknown'
            
            # 创建限流器
            limiter = RateLimiter(rate=limit, capacity=capacity)
            
            # 检查是否允许请求
            if not limiter.acquire():
                return jsonify({
                    'success': False,
                    'error': '请求过于频繁，请稍后再试',
                    'retry_after': 1.0 / limit
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def cache_response(ttl: int = 300):
    """
    缓存响应装饰器
    
    使用示例:
    @app.route('/api/data')
    @cache_response(ttl=600)
    def get_data():
        return jsonify({'data': 'example'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            
            # 尝试从缓存获取
            cached = response_cache.get(request.path, dict(request.args))
            if cached is not None:
                return cached
            
            # 执行实际函数
            result = f(*args, **kwargs)
            
            # 缓存响应
            if hasattr(result, 'get_json'):
                response_cache.set(
                    request.path,
                    dict(request.args),
                    result,
                    ttl=ttl
                )
            
            return result
        
        return decorated_function
    return decorator


# 定期清理过期缓存
def start_cache_cleanup(interval: int = 60):
    """启动定期缓存清理任务"""
    import threading
    
    def cleanup_loop():
        while True:
            time.sleep(interval)
            response_cache.cleanup_expired()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    print(f"✅ 缓存清理任务已启动，清理间隔：{interval}秒")


if __name__ == '__main__':
    # 测试限流器
    print("测试限流器...")
    
    limiter = RateLimiter(rate=2.0, capacity=5.0)
    
    for i in range(10):
        if limiter.acquire():
            print(f"请求 {i+1}: 允许")
        else:
            print(f"请求 {i+1}: 拒绝")
        time.sleep(0.3)
    
    # 测试缓存
    print("\n测试缓存...")
    
    cache = ResponseCache(max_size=5, default_ttl=10)
    
    for i in range(7):
        cache.set('/api/test', {'id': i}, {'data': f'value_{i}'})
        print(f"缓存 {i+1}: 当前大小 {len(cache.cache)}")
    
    print(f"\n最终缓存大小：{len(cache.cache)}")
