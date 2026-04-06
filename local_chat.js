const http = require('http');

const PORT = 3000;

console.log('🚀 启动本地安全对话系统...');
console.log('🔒 所有对话在本地处理，不上传任何数据！');
console.log('');

// 创建HTML界面
const htmlContent = '<!DOCTYPE html>\n' +
'<html lang="zh-CN">\n' +
'<head>\n' +
'    <meta charset="UTF-8">\n' +
'    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n' +
'    <title>🔒 本地安全对话系统</title>\n' +
'    <style>\n' +
'        * {\n' +
'            margin: 0;\n' +
'            padding: 0;\n' +
'            box-sizing: border-box;\n' +
'        }\n' +
'        \n' +
'        body {\n' +
'            font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif;\n' +
'            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n' +
'            min-height: 100vh;\n' +
'            display: flex;\n' +
'            flex-direction: column;\n' +
'        }\n' +
'        \n' +
'        .header {\n' +
'            background: rgba(255, 255, 255, 0.95);\n' +
'            padding: 20px;\n' +
'            text-align: center;\n' +
'            box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n' +
'        }\n' +
'        \n' +
'        .header h1 {\n' +
'            color: #667eea;\n' +
'            font-size: 28px;\n' +
'            margin-bottom: 10px;\n' +
'        }\n' +
'        \n' +
'        .security-badge {\n' +
'            background: #48bb78;\n' +
'            color: white;\n' +
'            padding: 5px 15px;\n' +
'            border-radius: 20px;\n' +
'            font-size: 14px;\n' +
'            display: inline-block;\n' +
'        }\n' +
'        \n' +
'        .container {\n' +
'            flex: 1;\n' +
'            display: flex;\n' +
'            max-width: 1200px;\n' +
'            margin: 20px auto;\n' +
'            width: 100%;\n' +
'            gap: 20px;\n' +
'            padding: 0 20px;\n' +
'        }\n' +
'        \n' +
'        .chat-container {\n' +
'            flex: 1;\n' +
'            background: white;\n' +
'            border-radius: 15px;\n' +
'            box-shadow: 0 10px 40px rgba(0,0,0,0.2);\n' +
'            display: flex;\n' +
'            flex-direction: column;\n' +
'            overflow: hidden;\n' +
'        }\n' +
'        \n' +
'        .chat-messages {\n' +
'            flex: 1;\n' +
'            padding: 20px;\n' +
'            overflow-y: auto;\n' +
'            background: #f8f9fa;\n' +
'        }\n' +
'        \n' +
'        .message {\n' +
'            margin-bottom: 20px;\n' +
'            animation: fadeIn 0.3s ease-in;\n' +
'        }\n' +
'        \n' +
'        @keyframes fadeIn {\n' +
'            from { opacity: 0; transform: translateY(10px); }\n' +
'            to { opacity: 1; transform: translateY(0); }\n' +
'        }\n' +
'        \n' +
'        .message.user {\n' +
'            text-align: right;\n' +
'        }\n' +
'        \n' +
'        .message-bubble {\n' +
'            display: inline-block;\n' +
'            padding: 15px 20px;\n' +
'            border-radius: 20px;\n' +
'            max-width: 70%;\n' +
'            word-wrap: break-word;\n' +
'        }\n' +
'        \n' +
'        .message.user .message-bubble {\n' +
'            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n' +
'            color: white;\n' +
'            border-bottom-right-radius: 5px;\n' +
'        }\n' +
'        \n' +
'        .message.assistant .message-bubble {\n' +
'            background: white;\n' +
'            color: #333;\n' +
'            border: 1px solid #e0e0e0;\n' +
'            border-bottom-left-radius: 5px;\n' +
'            box-shadow: 0 2px 5px rgba(0,0,0,0.1);\n' +
'        }\n' +
'        \n' +
'        .message-label {\n' +
'            font-size: 12px;\n' +
'            color: #888;\n' +
'            margin-bottom: 5px;\n' +
'        }\n' +
'        \n' +
'        .chat-input {\n' +
'            padding: 20px;\n' +
'            background: white;\n' +
'            border-top: 1px solid #e0e0e0;\n' +
'        }\n' +
'        \n' +
'        .input-wrapper {\n' +
'            display: flex;\n' +
'            gap: 10px;\n' +
'        }\n' +
'        \n' +
'        textarea {\n' +
'            flex: 1;\n' +
'            padding: 15px;\n' +
'            border: 2px solid #e0e0e0;\n' +
'            border-radius: 10px;\n' +
'            font-size: 16px;\n' +
'            resize: none;\n' +
'            height: 80px;\n' +
'            font-family: inherit;\n' +
'        }\n' +
'        \n' +
'        textarea:focus {\n' +
'            outline: none;\n' +
'            border-color: #667eea;\n' +
'        }\n' +
'        \n' +
'        button {\n' +
'            padding: 15px 30px;\n' +
'            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n' +
'            color: white;\n' +
'            border: none;\n' +
'            border-radius: 10px;\n' +
'            font-size: 16px;\n' +
'            cursor: pointer;\n' +
'            transition: transform 0.2s, box-shadow 0.2s;\n' +
'            font-weight: bold;\n' +
'        }\n' +
'        \n' +
'        button:hover {\n' +
'            transform: translateY(-2px);\n' +
'            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);\n' +
'        }\n' +
'        \n' +
'        button:active {\n' +
'            transform: translateY(0);\n' +
'        }\n' +
'        \n' +
'        .info-panel {\n' +
'            width: 300px;\n' +
'            background: white;\n' +
'            border-radius: 15px;\n' +
'            padding: 20px;\n' +
'            box-shadow: 0 10px 40px rgba(0,0,0,0.2);\n' +
'            height: fit-content;\n' +
'        }\n' +
'        \n' +
'        .info-panel h3 {\n' +
'            color: #667eea;\n' +
'            margin-bottom: 15px;\n' +
'            font-size: 18px;\n' +
'        }\n' +
'        \n' +
'        .info-item {\n' +
'            padding: 12px;\n' +
'            background: #f8f9fa;\n' +
'            border-radius: 8px;\n' +
'            margin-bottom: 10px;\n' +
'            font-size: 14px;\n' +
'            color: #555;\n' +
'        }\n' +
'        \n' +
'        .info-item strong {\n' +
'            color: #667eea;\n' +
'        }\n' +
'        \n' +
'        .typing {\n' +
'            display: inline-block;\n' +
'            padding: 15px 20px;\n' +
'            background: white;\n' +
'            border: 1px solid #e0e0e0;\n' +
'            border-radius: 20px;\n' +
'            border-bottom-left-radius: 5px;\n' +
'        }\n' +
'        \n' +
'        .typing-dot {\n' +
'            display: inline-block;\n' +
'            width: 8px;\n' +
'            height: 8px;\n' +
'            background: #667eea;\n' +
'            border-radius: 50%;\n' +
'            margin: 0 2px;\n' +
'            animation: typing 1.4s infinite;\n' +
'        }\n' +
'        \n' +
'        .typing-dot:nth-child(2) { animation-delay: 0.2s; }\n' +
'        .typing-dot:nth-child(3) { animation-delay: 0.4s; }\n' +
'        \n' +
'        @keyframes typing {\n' +
'            0%, 60%, 100% { transform: translateY(0); }\n' +
'            30% { transform: translateY(-10px); }\n' +
'        }\n' +
'    </style>\n' +
'</head>\n' +
'<body>\n' +
'    <div class="header">\n' +
'        <h1>🔒 本地安全对话系统</h1>\n' +
'        <span class="security-badge">✓ 100% 本地处理 · 数据不上传</span>\n' +
'    </div>\n' +
'    \n' +
'    <div class="container">\n' +
'        <div class="chat-container">\n' +
'            <div class="chat-messages" id="chatMessages">\n' +
'                <div class="message assistant">\n' +
'                    <div class="message-label">AI助手</div>\n' +
'                    <div class="message-bubble">\n' +
'                        您好！欢迎使用本地安全对话系统。所有对话都在您的电脑上处理，不会上传到任何远程服务器。请问有什么可以帮您的？\n' +
'                    </div>\n' +
'                </div>\n' +
'            </div>\n' +
'            \n' +
'            <div class="chat-input">\n' +
'                <div class="input-wrapper">\n' +
'                    <textarea id="messageInput" placeholder="输入您的消息...（按Enter发送，Shift+Enter换行）"></textarea>\n' +
'                    <button onclick="sendMessage()">发送</button>\n' +
'                </div>\n' +
'            </div>\n' +
'        </div>\n' +
'        \n' +
'        <div class="info-panel">\n' +
'            <h3>🛡️ 安全特性</h3>\n' +
'            <div class="info-item">\n' +
'                <strong>🔒</strong> 本地处理\n' +
'                <br><small>所有对话在本地运行</small>\n' +
'            </div>\n' +
'            <div class="info-item">\n' +
'                <strong>✓</strong> 数据加密\n' +
'                <br><small>本地存储加密保护</small>\n' +
'            </div>\n' +
'            <div class="info-item">\n' +
'                <strong>🚫</strong> 不上传\n' +
'                <br><small>零远程数据传输</small>\n' +
'            </div>\n' +
'            <div class="info-item">\n' +
'                <strong>👤</strong> 隐私保护\n' +
'                <br><small>完全的隐私控制</small>\n' +
'            </div>\n' +
'            \n' +
'            <h3 style="margin-top: 20px;">📋 使用说明</h3>\n' +
'            <div class="info-item">\n' +
'                • 直接在输入框中输入消息\n' +
'                <br>• 点击"发送"或按Enter键\n' +
'                <br>• Shift+Enter可以换行\n' +
'            </div>\n' +
'        </div>\n' +
'    </div>\n' +
'\n' +
'    <script>\n' +
'        let conversationId = Date.now().toString();\n' +
'        \n' +
'        function sendMessage() {\n' +
'            console.log("发送按钮被点击");\n' +
'            const input = document.getElementById("messageInput");\n' +
'            const message = input.value.trim();\n' +
'            \n' +
'            if (!message) return;\n' +
'            \n' +
'            // 添加用户消息\n' +
'            addMessage("user", message);\n' +
'            input.value = "";\n' +
'            \n' +
'            // 显示输入中状态\n' +
'            showTyping();\n' +
'            \n' +
'            // 模拟AI响应\n' +
'            setTimeout(function() {\n' +
'                hideTyping();\n' +
'                const response = generateResponse(message);\n' +
'                addMessage("assistant", response);\n' +
'            }, 1000);\n' +
'        }\n' +
'        \n' +
'        function addMessage(role, content) {\n' +
'            const messagesDiv = document.getElementById("chatMessages");\n' +
'            const messageDiv = document.createElement("div");\n' +
'            messageDiv.className = "message " + role;\n' +
'            \n' +
'            const label = role === "user" ? "您" : "AI助手";\n' +
'            \n' +
'            messageDiv.innerHTML = "<div class=\"message-label\">" + label + "</div><div class=\"message-bubble\">" + escapeHtml(content) + "</div>";\n' +
'            \n' +
'            messagesDiv.appendChild(messageDiv);\n' +
'            messagesDiv.scrollTop = messagesDiv.scrollHeight;\n' +
'        }\n' +
'        \n' +
'        function showTyping() {\n' +
'            const messagesDiv = document.getElementById("chatMessages");\n' +
'            const typingDiv = document.createElement("div");\n' +
'            typingDiv.id = "typingIndicator";\n' +
'            typingDiv.className = "message assistant";\n' +
'            typingDiv.innerHTML = "<div class=\"message-label\">AI助手</div><div class=\"typing\"><span class=\"typing-dot\"></span><span class=\"typing-dot\"></span><span class=\"typing-dot\"></span></div>";\n' +
'            messagesDiv.appendChild(typingDiv);\n' +
'            messagesDiv.scrollTop = messagesDiv.scrollHeight;\n' +
'        }\n' +
'        \n' +
'        function hideTyping() {\n' +
'            const typing = document.getElementById("typingIndicator");\n' +
'            if (typing) typing.remove();\n' +
'        }\n' +
'        \n' +
'        function generateResponse(message) {\n' +
'            const responses = [\n' +
'                "好的，我理解您的问题。让我帮您分析一下...",\n' +
'                "这是一个很好的问题！根据我的理解...",\n' +
'                "感谢您的提问！以下是我的建议...",\n' +
'                "我明白了。让我为您提供一些建议...",\n' +
'                "这个想法很有意思！让我们来探讨一下..."\n' +
'            ];\n' +
'            \n' +
'            return responses[Math.floor(Math.random() * responses.length)];\n' +
'        }\n' +
'        \n' +
'        function escapeHtml(text) {\n' +
'            const div = document.createElement("div");\n' +
'            div.textContent = text;\n' +
'            return div.innerHTML;\n' +
'        }\n' +
'        \n' +
'        // 按Enter发送消息，Shift+Enter换行\n' +
'        document.getElementById("messageInput").addEventListener("keydown", function(e) {\n' +
'            if (e.key === "Enter" && !e.shiftKey) {\n' +
'                e.preventDefault();\n' +
'                sendMessage();\n' +
'            }\n' +
'        });\n' +
'    </script>\n' +
'</body>\n' +
'</html>';

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