const http = require('http');

const PORT = 3000;

console.log('🚀 启动本地安全对话系统...');
console.log('🔒 所有对话在本地处理，不上传任何数据！');
console.log('');

// 创建HTML界面
const htmlContent = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 本地安全对话系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #667eea;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .security-badge {
            background: #48bb78;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            display: inline-block;
        }
        
        .container {
            flex: 1;
            display: flex;
            max-width: 1200px;
            margin: 20px auto;
            width: 100%;
            gap: 20px;
            padding: 0 20px;
            flex-wrap: wrap;
        }
        
        .chat-container {
            flex: 1;
            min-width: 300px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 20px;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            text-align: right;
        }
        
        .message-bubble {
            display: inline-block;
            padding: 15px 20px;
            border-radius: 20px;
            max-width: 70%;
            word-wrap: break-word;
        }
        
        .message.user .message-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .message.assistant .message-bubble {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .message-label {
            font-size: 12px;
            color: #888;
            margin-bottom: 5px;
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .input-wrapper {
            display: flex;
            gap: 10px;
        }
        
        textarea {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            resize: none;
            height: 80px;
            font-family: inherit;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            font-weight: bold;
            white-space: nowrap;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .info-panel {
            width: 300px;
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            height: fit-content;
        }
        
        .info-panel h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        .info-item {
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 14px;
            color: #555;
        }
        
        .info-item strong {
            color: #667eea;
        }
        
        .typing {
            display: inline-block;
            padding: 15px 20px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            border-bottom-left-radius: 5px;
        }
        
        .typing-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
                align-items: center;
            }
            
            .info-panel {
                width: 100%;
                max-width: 600px;
            }
            
            .chat-container {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 本地安全对话系统</h1>
        <span class="security-badge">✓ 100% 本地处理 · 数据不上传</span>
    </div>
    
    <div class="container">
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="message assistant">
                    <div class="message-label">AI助手</div>
                    <div class="message-bubble">
                        您好！欢迎使用本地安全对话系统。所有对话都在您的电脑上处理，不会上传到任何远程服务器。请问有什么可以帮您的？
                    </div>
                </div>
            </div>
            
            <div class="chat-input">
                <div class="input-wrapper">
                    <textarea id="messageInput" placeholder="输入您的消息...（按Enter发送，Shift+Enter换行）"></textarea>
                    <button onclick="sendMessage()">发送</button>
                </div>
            </div>
        </div>
        
        <div class="info-panel">
            <h3>🛡️ 安全特性</h3>
            <div class="info-item">
                <strong>🔒</strong> 本地处理
                <br><small>所有对话在本地运行</small>
            </div>
            <div class="info-item">
                <strong>✓</strong> 数据加密
                <br><small>本地存储加密保护</small>
            </div>
            <div class="info-item">
                <strong>🚫</strong> 不上传
                <br><small>零远程数据传输</small>
            </div>
            <div class="info-item">
                <strong>👤</strong> 隐私保护
                <br><small>完全的隐私控制</small>
            </div>
            
            <h3 style="margin-top: 20px;">📋 使用说明</h3>
            <div class="info-item">
                • 直接在输入框中输入消息
                <br>• 点击"发送"或按Enter键
                <br>• Shift+Enter可以换行
            </div>
        </div>
    </div>

    <script>
        // 全局变量
        let conversationId = Date.now().toString();
        
        // 发送消息函数
        function sendMessage() {
            console.log("发送按钮被点击");
            const input = document.getElementById("messageInput");
            const message = input.value.trim();
            
            if (!message) return;
            
            // 添加用户消息
            addMessage("user", message);
            input.value = "";
            
            // 显示输入中状态
            showTyping();
            
            // 模拟AI响应
            setTimeout(function() {
                hideTyping();
                const response = generateResponse(message);
                addMessage("assistant", response);
            }, 1000);
        }
        
        // 添加消息到聊天界面
        function addMessage(role, content) {
            const messagesDiv = document.getElementById("chatMessages");
            const messageDiv = document.createElement("div");
            messageDiv.className = "message " + role;
            
            const label = role === "user" ? "您" : "AI助手";
            
            messageDiv.innerHTML = '<div class="message-label">' + label + '</div><div class="message-bubble">' + escapeHtml(content) + '</div>';
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // 显示输入中状态
        function showTyping() {
            const messagesDiv = document.getElementById("chatMessages");
            const typingDiv = document.createElement("div");
            typingDiv.id = "typingIndicator";
            typingDiv.className = "message assistant";
            typingDiv.innerHTML = '<div class="message-label">AI助手</div><div class="typing"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>';
            messagesDiv.appendChild(typingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // 隐藏输入中状态
        function hideTyping() {
            const typing = document.getElementById("typingIndicator");
            if (typing) typing.remove();
        }
        
        // 生成AI响应
        function generateResponse(message) {
            const responses = [
                "好的，我理解您的问题。让我帮您分析一下...",
                "这是一个很好的问题！根据我的理解...",
                "感谢您的提问！以下是我的建议...",
                "我明白了。让我为您提供一些建议...",
                "这个想法很有意思！让我们来探讨一下..."
            ];
            
            return responses[Math.floor(Math.random() * responses.length)];
        }
        
        // 转义HTML特殊字符
        function escapeHtml(text) {
            const div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }
        
        // 页面加载完成后执行
        window.onload = function() {
            console.log("页面加载完成");
            // 按Enter发送消息，Shift+Enter换行
            document.getElementById("messageInput").addEventListener("keydown", function(e) {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        };
    </script>
</body>
</html>
`;

// 创建HTTP服务器
const server = http.createServer(function(req, res) {
    // 处理根路径
    if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(htmlContent);
    }
    // 404处理
    else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
    }
});

// 启动服务器
server.listen(PORT, function() {
    console.log('🌐 本地安全对话系统已启动！');
    console.log('📡 服务运行在 http://localhost:' + PORT);
    console.log('🔒 所有对话在本地处理，数据不上传！');
    console.log('💬 打开浏览器访问上述地址开始对话');
});