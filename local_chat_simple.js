const http = require('http');

const PORT = 3000;

// 简化的HTML内容
const htmlContent = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>本地安全对话系统</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f0f0f0;
        }
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 20px;
        }
        .message {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 5px;
        }
        .message.user {
            background-color: #e3f2fd;
            text-align: right;
        }
        .message.assistant {
            background-color: #f1f1f1;
        }
        .chat-input {
            display: flex;
        }
        textarea {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            resize: none;
        }
        button {
            padding: 10px 20px;
            margin-left: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <h1>本地安全对话系统</h1>
        <div class="chat-messages" id="chatMessages">
            <div class="message assistant">
                您好！欢迎使用本地安全对话系统。
            </div>
        </div>
        <div class="chat-input">
            <textarea id="messageInput" placeholder="输入您的消息..."></textarea>
            <button onclick="sendMessage()">发送</button>
        </div>
    </div>

    <script>
        function sendMessage() {
            console.log('发送按钮被点击');
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // 添加用户消息
            addMessage('user', message);
            input.value = '';
            
            // 显示输入中状态
            showTyping();
            
            // 模拟AI响应
            setTimeout(function() {
                hideTyping();
                const response = generateResponse(message);
                addMessage('assistant', response);
            }, 1000);
        }
        
        function addMessage(role, content) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + role;
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function showTyping() {
            const messagesDiv = document.getElementById('chatMessages');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typingIndicator';
            typingDiv.className = 'message assistant';
            typingDiv.textContent = 'AI正在输入...';
            messagesDiv.appendChild(typingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typingIndicator');
            if (typing) typing.remove();
        }
        
        function generateResponse(message) {
            const responses = [
                "好的，我理解您的问题。",
                "这是一个很好的问题！",
                "感谢您的提问！",
                "我明白了。",
                "这个想法很有意思！"
            ];
            return responses[Math.floor(Math.random() * responses.length)];
        }
        
        // 按Enter发送消息
        document.getElementById('messageInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
`;

// 创建HTTP服务器
const server = http.createServer(function(req, res) {
    if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(htmlContent);
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
    }
});

// 启动服务器
server.listen(PORT, function() {
    console.log('本地安全对话系统已启动！');
    console.log('服务运行在 http://localhost:' + PORT);
});