const fs = require('fs');
const path = require('path');

// 配置文件路径
const configPath = path.join(process.env.USERPROFILE, '.openclaw', 'openclaw.json');

console.log('Enabling OpenClaw HTTP API...');

try {
  // 读取现有配置
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  
  // 启用HTTP API端点
  config.gateway = {
    ...config.gateway,
    http: {
      endpoints: {
        responses: { enabled: true }
      }
    }
  };
  
  // 写入更新后的配置
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  
  console.log('✅ OpenClaw HTTP API enabled successfully!');
  console.log('API endpoint: http://127.0.0.1:18789/v1/responses');
  console.log('Auth token:', config.gateway.auth.token.substring(0, 8) + '...');
  
} catch (error) {
  console.error('❌ Failed to enable HTTP API:', error.message);
  process.exit(1);
}
