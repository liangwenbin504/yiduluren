const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 80;
const API_KEY = "local-safe-chat-123456";

console.log('🚀 启动本地安全对话API服务...');
console.log('🔒 所有对话在本地处理，不上传任何数据！');
console.log('');
console.log('📡 API 服务地址: http://127.0.0.1:' + PORT);
console.log('🔑 API 密钥: ' + API_KEY);
console.log('');
console.log('在 Trae Solo 中配置:');
console.log('  - API 基础 URL: http://127.0.0.1:' + PORT + '/v1');
console.log('  - API 密钥: ' + API_KEY);
console.log('  - 模型名称: local-safe-model');
console.log('');
console.log('========================================');
console.log('');

// 简单的AI回复逻辑
function generateAIResponse(userMessage) {
    const lowerMsg = userMessage.toLowerCase();
    
    // 问候语
    if (lowerMsg.includes('你好') || lowerMsg.includes('您好') || lowerMsg.includes('hi') || lowerMsg.includes('hello')) {
        return '您好！我是您的本地安全AI助手。所有对话都在您的电脑上处理，不会上传到任何远程服务器。请问有什么可以帮您的？';
    }
    
    // 询问功能
    if (lowerMsg.includes('你能做什么') || lowerMsg.includes('功能') || lowerMsg.includes('帮助')) {
        return '我可以帮您：\n\n1. 回答各种问题\n2. 进行对话交流\n3. 帮助分析问题\n4. 提供建议和意见\n\n所有对话都在本地处理，确保您的数据安全！';
    }
    
    // 安全相关
    if (lowerMsg.includes('安全') || lowerMsg.includes('隐私') || lowerMsg.includes('数据')) {
        return '请放心！我们的系统采用100%本地处理模式：\n\n✅ 所有对话数据仅在您的电脑上处理\n✅ 不会上传到任何远程服务器\n✅ 没有网络传输风险\n✅ 完全保护您的隐私安全';
    }
    
    // 默认回复
    const responses = [
        '好的，我理解您的问题。虽然我是一个本地安全助手，但我会尽力帮助您！',
        '这是一个很好的话题！让我们来探讨一下。',
        '感谢您的提问！作为本地安全助手，我的使命是保护您的隐私。',
        '我明白了。让我为您提供一些安全的建议。',
        '这个想法很有意思！在本地安全的环境下，我们可以畅所欲言。'
    ];
    
    return responses[Math.floor(Math.random() * responses.length)] + 
           '\n\n💡 提示：所有对话都在本地处理，您的数据完全安全！';
}

// 创建HTTP服务器
const server = http.createServer((req, res) => {
    // 设置CORS头
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    // 处理OPTIONS预检请求
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    // 验证API密钥
    const authHeader = req.headers.authorization;
    if (req.url.startsWith('/v1/') && !authHeader?.includes(API_KEY)) {
        res.writeHead(401, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: { message: 'Invalid API key' } }));
        return;
    }
    
    // 路由处理
    if (req.method === 'GET' && req.url === '/') {
        // 首页
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>本地安全API服务</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        h1 { color: #667eea; margin-bottom: 20px; }
        .success { color: #48bb78; font-weight: bold; }
        .config { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .config-item { margin: 10px 0; }
        .label { font-weight: bold; color: #667eea; display: inline-block; width: 120px; }
        .badge { background: #48bb78; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 本地安全API服务已启动</h1>
        <p class="badge">✓ 100% 本地处理 · 数据不上传</p>
        
        <div class="config">
            <h2>📋 Trae Solo 配置信息</h2>
            <div class="config-item">
                <span class="label">API 基础 URL:</span>
                <code>http://127.0.0.1:${PORT}/v1</code>
            </div>
            <div class="config-item">
                <span class="label">API 密钥:</span>
                <code>${API_KEY}</code>
            </div>
            <div class="config-item">
                <span class="label">模型名称:</span>
                <code>local-safe-model</code>
            </div>
        </div>
        
        <h2>🎯 使用步骤</h2>
        <ol>
            <li>保持这个窗口运行（不要关闭）</li>
            <li>打开 Trae Solo</li>
            <li>找到模型选择器</li>
            <li>选择"添加自定义模型"或"OpenAI 兼容 API"</li>
            <li>填入上面的配置信息</li>
            <li>开始安全对话！</li>
        </ol>
    </div>
</body>
</html>
        `);
        return;
    }
    
    if (req.method === 'GET' && req.url === '/v1/models') {
        // 返回模型列表
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            object: 'list',
            data: [
                {
                    id: 'local-safe-model',
                    object: 'model',
                    created: Date.now(),
                    owned_by: 'local'
                }
            ]
        }));
        return;
    }
    
    if (req.method === 'POST' && req.url === '/v1/chat/completions') {
        // 聊天完成API
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const messages = data.messages || [];
                const lastUserMessage = messages.filter(m => m.role === 'user').pop()?.content || '';
                const stream = data.stream || false;
                
                const aiResponse = generateAIResponse(lastUserMessage);
                
                if (stream) {
                    // 流式响应
                    res.writeHead(200, { 
                        'Content-Type': 'text/event-stream',
                        'Cache-Control': 'no-cache'
                    });
                    
                    // 模拟流式输出
                    const chunks = aiResponse.split('');
                    let i = 0;
                    const interval = setInterval(() => {
                        if (i < chunks.length) {
                            const chunk = {
                                id: 'chatcmpl-local',
                                object: 'chat.completion.chunk',
                                created: Date.now(),
                                model: 'local-safe-model',
                                choices: [{
                                    index: 0,
                                    delta: { content: chunks[i] },
                                    finish_reason: null
                                }]
                            };
                            res.write('data: ' + JSON.stringify(chunk) + '\n\n');
                            i++;
                        } else {
                            // 发送结束标记
                            const endChunk = {
                                id: 'chatcmpl-local',
                                object: 'chat.completion.chunk',
                                created: Date.now(),
                                model: 'local-safe-model',
                                choices: [{
                                    index: 0,
                                    delta: {},
                                    finish_reason: 'stop'
                                }]
                            };
                            res.write('data: ' + JSON.stringify(endChunk) + '\n\n');
                            res.write('data: [DONE]\n\n');
                            res.end();
                            clearInterval(interval);
                        }
                    }, 20);
                } else {
                    // 非流式响应
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        id: 'chatcmpl-local',
                        object: 'chat.completion',
                        created: Date.now(),
                        model: 'local-safe-model',
                        choices: [{
                            index: 0,
                            message: {
                                role: 'assistant',
                                content: aiResponse
                            },
                            finish_reason: 'stop'
                        }],
                        usage: {
                            prompt_tokens: lastUserMessage.length,
                            completion_tokens: aiResponse.length,
                            total_tokens: lastUserMessage.length + aiResponse.length
                        }
                    }));
                }
            } catch (error) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: { message: error.message } }));
            }
        });
        return;
    }
    
    // 404
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: { message: 'Not found' } }));
});

// 启动服务器
server.listen(PORT, '127.0.0.1', () => {
    console.log('✅ 服务启动成功！');
    console.log('');
    console.log('🌐 打开浏览器访问: http://127.0.0.1:' + PORT);
    console.log('');
});
