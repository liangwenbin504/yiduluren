const fs = require('fs');
const path = require('path');

// 配置文件路径
const configPath = path.join(process.env.USERPROFILE, '.openclaw', 'openclaw.json');

console.log('Fixing OpenClaw configuration...');

try {
  // 读取现有配置
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  
  // 修复安全设置，使用正确的绑定模式
  config.gateway = {
    ...config.gateway,
    bind: 'loopback', // 使用loopback模式代替127.0.0.1
    port: 18789,
    auth: {
      ...config.gateway.auth,
      required: true
    }
  };
  
  // 写入更新后的配置
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  
  console.log('✅ OpenClaw configuration fixed successfully!');
  console.log('Security settings applied:');
  console.log('- Bind mode: loopback (local only)');
  console.log('- Port: 18789');
  console.log('- Authentication: Required');
  
} catch (error) {
  console.error('❌ Failed to fix configuration:', error.message);
  process.exit(1);
}
