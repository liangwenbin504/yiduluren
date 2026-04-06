/**
 * 网络请求恢复模块
 * 
 * 功能特性：
 * 1. 实时监测网络连接状态
 * 2. 自动缓存因网络问题挂起的请求
 * 3. 网络恢复后自动重试队列中的请求
 * 4. 支持配置重试次数、重试间隔
 * 5. 提供请求状态回调接口
 * 6. 支持请求幂等性处理
 * 
 * @version 1.0.0
 * @author 仪度六壬
 */

class NetworkRequestRecovery {
    // 默认配置
    static DEFAULT_CONFIG = {
        maxRetries: 3,              // 最大重试次数
        retryInterval: 2000,        // 重试间隔（毫秒）
        exponentialBackoff: true,   // 是否使用指数退避
        timeout: 30000,             // 请求超时时间（毫秒）
        enableQueue: true,          // 是否启用请求队列
        enableIdempotency: true,    // 是否启用幂等性处理
        debug: false                // 是否开启调试模式
    };

    /**
     * 构造函数
     * @param {Object} config 配置对象
     */
    constructor(config = {}) {
        this.config = { ...NetworkRequestRecovery.DEFAULT_CONFIG, ...config };
        
        // 请求队列
        this.requestQueue = [];
        
        // 正在处理的请求
        this.processingRequests = new Map();
        
        // 已完成的请求缓存（用于幂等性）
        this.completedRequests = new Map();
        
        // 网络状态
        this.isOnline = navigator.onLine;
        
        // 状态回调
        this.callbacks = {
            onQueued: null,         // 请求入队回调
            onRetry: null,          // 重试回调
            onSuccess: null,        // 成功回调
            onError: null,          // 错误回调
            onRecover: null,        // 网络恢复回调
            onOffline: null         // 网络断开回调
        };
        
        // 初始化
        this.init();
    }

    /**
     * 初始化模块
     */
    init() {
        // 监听网络状态变化
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // 启动队列处理器
        if (this.config.enableQueue) {
            this.startQueueProcessor();
        }
        
        this.log('🚀 网络请求恢复模块已初始化');
        this.log(`📋 配置：最大重试=${this.config.maxRetries}, 重试间隔=${this.config.retryInterval}ms`);
    }

    /**
     * 处理网络恢复事件
     */
    handleOnline() {
        if (!this.isOnline) {
            this.isOnline = true;
            this.log('🟢 网络已恢复');
            
            if (this.callbacks.onRecover) {
                this.callbacks.onRecover({ timestamp: Date.now() });
            }
            
            // 立即处理队列中的请求
            this.processQueue();
        }
    }

    /**
     * 处理网络断开事件
     */
    handleOffline() {
        if (this.isOnline) {
            this.isOnline = false;
            this.log('🔴 网络已断开');
            
            if (this.callbacks.onOffline) {
                this.callbacks.onOffline({ timestamp: Date.now() });
            }
        }
    }

    /**
     * 发送请求（核心方法）
     * @param {Object} requestOptions 请求配置
     * @returns {Promise} 请求结果
     */
    async request(requestOptions) {
        const requestId = this.generateRequestId(requestOptions);
        const requestInfo = {
            id: requestId,
            options: { ...requestOptions },
            retries: 0,
            createdAt: Date.now(),
            status: 'pending'
        };

        // 检查是否已处理过（幂等性）
        if (this.config.enableIdempotency && this.completedRequests.has(requestId)) {
            const cachedResult = this.completedRequests.get(requestId);
            this.log(`⏭️  使用缓存结果：${requestId}`);
            return cachedResult;
        }

        // 如果网络断开且启用队列，加入队列
        if (!this.isOnline && this.config.enableQueue) {
            this.log(`📦 网络断开，请求入队：${requestId}`);
            requestInfo.status = 'queued';
            this.requestQueue.push(requestInfo);
            
            if (this.callbacks.onQueued) {
                this.callbacks.onQueued({
                    requestId,
                    options: requestOptions,
                    queueLength: this.requestQueue.length
                });
            }
            
            // 返回一个待处理的 Promise
            return new Promise((resolve, reject) => {
                requestInfo.resolve = resolve;
                requestInfo.reject = reject;
            });
        }

        // 执行请求
        return this.executeRequest(requestInfo);
    }

    /**
     * 执行单个请求
     * @param {Object} requestInfo 请求信息
     */
    async executeRequest(requestInfo) {
        const { id, options } = requestInfo;
        
        this.processingRequests.set(id, requestInfo);
        this.log(`📡 发送请求：${id}`);

        try {
            // 使用 fetch API 发送请求
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
            
            // 处理进度监听
            const fetchOptions = {
                ...options,
                signal: controller.signal
            };
            
            // 如果需要进度监听，使用 Response body 的 getReader
            const response = await fetch(options.url, fetchOptions);
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 检查是否需要进度监听
            const contentLength = response.headers.get('content-length');
            const total = contentLength ? parseInt(contentLength) : 0;
            
            if ((options.onDownloadProgress || options.onUploadProgress) && total > 0) {
                // 使用 reader 监听下载进度
                const reader = response.body.getReader();
                let loaded = 0;
                const chunks = [];
                
                while (true) {
                    const { done, value } = await reader.read();
                    
                    if (done) break;
                    
                    chunks.push(value);
                    loaded += value.length;
                    
                    if (options.onDownloadProgress) {
                        options.onDownloadProgress({
                            loaded: loaded,
                            total: total,
                            percent: (loaded / total) * 100
                        });
                    }
                }
                
                // 合并所有 chunk
                const responseData = new Uint8Array(loaded);
                let position = 0;
                for (const chunk of chunks) {
                    responseData.set(chunk, position);
                    position += chunk.length;
                }
                
                // 解析 JSON
                const decoder = new TextDecoder();
                const result = JSON.parse(decoder.decode(responseData));
                
                // 标记为成功
                requestInfo.status = 'success';
                this.completedRequests.set(id, result);
                
                // 清理处理中的记录
                this.processingRequests.delete(id);
                
                this.log(`✅ 请求成功：${id}`);
                
                if (this.callbacks.onSuccess) {
                    this.callbacks.onSuccess({
                        requestId: id,
                        result,
                        retries: requestInfo.retries
                    });
                }
                
                // 如果请求有 resolve 函数（来自队列），调用它
                if (requestInfo.resolve) {
                    requestInfo.resolve(result);
                }
                
                return result;
            } else {
                // 不需要进度监听，直接解析
                const result = await response.json();
                
                // 标记为成功
                requestInfo.status = 'success';
                this.completedRequests.set(id, result);
                
                // 清理处理中的记录
                this.processingRequests.delete(id);
                
                this.log(`✅ 请求成功：${id}`);
                
                if (this.callbacks.onSuccess) {
                    this.callbacks.onSuccess({
                        requestId: id,
                        result,
                        retries: requestInfo.retries
                    });
                }
                
                // 如果请求有 resolve 函数（来自队列），调用它
                if (requestInfo.resolve) {
                    requestInfo.resolve(result);
                }
                
                return result;
            }
            
        } catch (error) {
            this.log(`❌ 请求失败：${id}`, error.message);
            
            // 判断是否需要重试
            if (this.shouldRetry(error, requestInfo)) {
                return this.retryRequest(requestInfo, error);
            } else {
                // 不再重试，标记为失败
                requestInfo.status = 'failed';
                this.processingRequests.delete(id);
                
                if (this.callbacks.onError) {
                    this.callbacks.onError({
                        requestId: id,
                        error,
                        retries: requestInfo.retries
                    });
                }
                
                if (requestInfo.reject) {
                    requestInfo.reject(error);
                }
                
                throw error;
            }
        }
    }

    /**
     * 判断是否应该重试
     * @param {Error} error 错误对象
     * @param {Object} requestInfo 请求信息
     */
    shouldRetry(error, requestInfo) {
        // 网络错误可以重试
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return requestInfo.retries < this.config.maxRetries;
        }
        
        // 超时错误可以重试
        if (error.name === 'AbortError') {
            return requestInfo.retries < this.config.maxRetries;
        }
        
        // 5xx 服务器错误可以重试
        if (error.message.includes('5')) {
            return requestInfo.retries < this.config.maxRetries;
        }
        
        // 其他错误不重试
        return false;
    }

    /**
     * 重试请求
     * @param {Object} requestInfo 请求信息
     * @param {Error} lastError 上次错误
     */
    async retryRequest(requestInfo, lastError) {
        const { id, retries } = requestInfo;
        requestInfo.retries++;
        
        // 计算重试延迟（支持指数退避）
        let delay = this.config.retryInterval;
        if (this.config.exponentialBackoff) {
            delay = delay * Math.pow(2, retries - 1);
        }
        
        // 添加随机抖动（避免同时重试）
        delay = delay * (0.5 + Math.random());
        
        this.log(`🔄 重试请求：${id} (第${requestInfo.retries}次，延迟${Math.round(delay)}ms)`);
        
        if (this.callbacks.onRetry) {
            this.callbacks.onRetry({
                requestId: id,
                retryCount: requestInfo.retries,
                delay,
                lastError
            });
        }
        
        // 延迟后重试
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.executeRequest(requestInfo);
    }

    /**
     * 启动队列处理器
     */
    startQueueProcessor() {
        // 每秒检查一次队列
        setInterval(() => {
            if (this.isOnline && this.requestQueue.length > 0) {
                this.processQueue();
            }
        }, 1000);
    }

    /**
     * 处理队列中的请求
     */
    async processQueue() {
        if (this.requestQueue.length === 0) return;
        
        this.log(`📬 开始处理队列，当前队列长度：${this.requestQueue.length}`);
        
        // 按顺序处理队列
        while (this.requestQueue.length > 0 && this.isOnline) {
            const requestInfo = this.requestQueue.shift();
            
            if (requestInfo) {
                try {
                    await this.executeRequest(requestInfo);
                } catch (error) {
                    // 如果重试后仍然失败，且队列已满，重新加入队列末尾
                    if (requestInfo.retries < this.config.maxRetries) {
                        this.requestQueue.push(requestInfo);
                        this.log(`⚠️  请求失败，重新入队：${requestInfo.id}`);
                    }
                }
            }
        }
        
        this.log(`📬 队列处理完成，剩余队列长度：${this.requestQueue.length}`);
    }

    /**
     * 生成请求 ID（用于幂等性）
     * @param {Object} options 请求配置
     * @returns {String} 请求 ID
     */
    generateRequestId(options) {
        // 使用请求方法 + URL + 参数（如果有）生成唯一 ID
        const method = options.method || 'GET';
        const url = options.url;
        const body = options.body ? JSON.stringify(options.body) : '';
        
        const str = `${method}:${url}:${body}`;
        return this.md5(str);
    }

    /**
     * 简单的 MD5 实现（用于生成请求 ID）
     * @param {String} str 输入字符串
     * @returns {String} MD5 哈希值
     */
    md5(str) {
        // 简化的哈希实现（实际项目中建议使用 crypto-js 库）
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(16);
    }

    /**
     * 设置状态回调
     * @param {Object} callbacks 回调函数对象
     */
    setCallbacks(callbacks) {
        this.callbacks = { ...this.callbacks, ...callbacks };
        this.log('📞 状态回调已设置');
    }

    /**
     * 获取队列状态
     * @returns {Object} 队列状态信息
     */
    getQueueStatus() {
        return {
            queueLength: this.requestQueue.length,
            processingCount: this.processingRequests.size,
            completedCount: this.completedRequests.size,
            isOnline: this.isOnline,
            queue: this.requestQueue.map(req => ({
                id: req.id,
                url: req.options.url,
                retries: req.retries,
                status: req.status
            }))
        };
    }

    /**
     * 清空队列
     */
    clearQueue() {
        this.requestQueue = [];
        this.log('🗑️ 队列已清空');
    }

    /**
     * 清空完成缓存
     */
    clearCompletedCache() {
        this.completedRequests.clear();
        this.log('🗑️ 完成缓存已清空');
    }

    /**
     * 手动触发重试某个请求
     * @param {String} requestId 请求 ID
     */
    async retryRequestManually(requestId) {
        const requestInfo = this.requestQueue.find(req => req.id === requestId);
        
        if (requestInfo) {
            requestInfo.retries = 0; // 重置重试次数
            return this.executeRequest(requestInfo);
        } else {
            throw new Error(`请求不存在：${requestId}`);
        }
    }

    /**
     * 日志输出
     * @param {String} message 日志消息
     * @param {Any} data 附加数据
     */
    log(message, data = null) {
        if (this.config.debug) {
            const timestamp = new Date().toLocaleTimeString();
            console.log(`[${timestamp}] [NetworkRecovery] ${message}`, data || '');
        }
    }

    /**
     * 销毁模块
     */
    destroy() {
        window.removeEventListener('online', () => this.handleOnline());
        window.removeEventListener('offline', () => this.handleOffline());
        this.clearQueue();
        this.clearCompletedCache();
        this.log('🔚 模块已销毁');
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NetworkRequestRecovery;
} else {
    window.NetworkRequestRecovery = NetworkRequestRecovery;
}
