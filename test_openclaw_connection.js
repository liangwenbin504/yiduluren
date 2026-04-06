const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

// 配置文件路径
const configPath = path.join(process.env.USERPROFILE, '.openclaw', 'openclaw.json');

console.log('Testing OpenClaw connection...');

try {
  // 读取配置文件获取认证令牌
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const token = config.gateway.auth.token;
  
  // OpenClaw WebSocket地址
  const wsUrl = `ws://127.0.0.1:18789`;
  
  console.log(`Connecting to: ${wsUrl}`);
  console.log(`Using token: ${token.substring(0, 8)}...`);
  
  // 创建WebSocket连接
  const ws = new WebSocket(wsUrl, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  ws.on('open', () => {
    console.log('✅ Connection established!');
    console.log('Testing message sending...');
    
    // 发送测试消息
    const testMessage = {
      type: 'agent',
      message: '你好，OpenClaw！',
      agent: 'main'
    };
    
    ws.send(JSON.stringify(testMessage));
  });
  
  ws.on('message', (data) => {
    console.log('✅ Received response:');
    try {
      const response = JSON.parse(data);
      console.log(JSON.stringify(response, null, 2));
    } catch (e) {
      console.log(data.toString());
    }
    ws.close();
  });
  
  ws.on('error', (error) => {
    console.error('❌ Connection error:', error.message);
    process.exit(1);
  });
  
  ws.on('close', () => {
    console.log('✅ Connection closed');
    console.log('\nTest completed successfully!');
    console.log('Trae Solo can now connect to OpenClaw securely.');
  });
  
} catch (error) {
  console.error('❌ Failed to test connection:', error.message);
  process.exit(1);
}
