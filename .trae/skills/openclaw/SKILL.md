***

name: "openclaw"
description: "OpenClaw本地AI代理网关，提供安全的本地对话功能。Invoke when user needs to use local AI for security and privacy, especially when handling sensitive information like passwords, bank accounts, etc."
---------------------------------------------------------------------------------------------------------------

# OpenClaw 本地集成

## 技能信息
- **名称**: OpenClaw
- **版本**: 2026.3.26
- **描述**: 本地AI代理网关，提供安全的对话功能

## 连接配置
- **服务地址**: ws://127.0.0.1:18789
- **认证方式**: 本地令牌
- **安全模式**: 仅本地通信

## 功能特性
- 本地AI对话
- 多通道集成
- 安全数据处理
- 隐私保护

## 安全设置
- **网络访问**: 仅限本地
- **数据存储**: 本地加密
- **敏感信息**: 本地处理，不上传
- **认证**: 必需

## 使用方法
1. 确保OpenClaw Gateway服务正在运行
2. 在Trae Solo中选择OpenClaw技能
3. 开始安全对话

## 配置文件
- **配置路径**: C:\Users\Administrator\.openclaw\openclaw.json
- **认证令牌**: 从配置文件中获取 `gateway.auth.token`

## 健康检查
```
node openclaw.mjs health
```

## 启动命令
```
node openclaw.mjs gateway --port 18789
```

## 安全保障
- 所有通信在本地网络进行
- 敏感信息不会传输到远程服务器
- 数据加密存储
- 认证机制保护

## 故障排除
- 确保端口18789未被占用
- 检查防火墙设置
- 验证配置文件权限
