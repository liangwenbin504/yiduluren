const http = require('http');

const CHAT2API_PORT = 8080;
const MIDDLEWARE_PORT = 8081;

function getModelType(model) {
  if (!model) return 'unknown';
  const m = model.toLowerCase();
  if (m.includes('qwen')) return 'qwen';
  if (m.includes('kimi')) return 'kimi';
  if (m.includes('glm')) return 'glm';
  if (m.includes('deepseek')) return 'deepseek';
  return 'unknown';
}

function cleanQwenChunk(line) {
  if (!line.startsWith('data:')) return line;
  const jsonStr = line.slice(5).trim();
  if (!jsonStr || jsonStr === '[DONE]') return line;
  
  try {
    const data = JSON.parse(jsonStr);
    if (data.choices) {
      for (const choice of data.choices) {
        if (choice.delta) {
          if (choice.delta.reasoning_content) delete choice.delta.reasoning_content;
          if (choice.delta.thinking) delete choice.delta.thinking;
        }
      }
    }
    return 'data: ' + JSON.stringify(data);
  } catch (e) {
    return line;
  }
}

function cleanKimiChunk(line) {
  if (!line.startsWith('data:')) return line;
  const jsonStr = line.slice(5).trim();
  if (!jsonStr || jsonStr === '[DONE]') return line;
  
  try {
    const data = JSON.parse(jsonStr);
    if (!data.choices || data.choices.length === 0) return '';
    if (data.choices) {
      for (const choice of data.choices) {
        if (choice.delta) {
          if (choice.delta.reasoning_content) delete choice.delta.reasoning_content;
          if (choice.delta.thinking) delete choice.delta.thinking;
          if (choice.delta.thinking_content) delete choice.delta.thinking_content;
        }
      }
    }
    return 'data: ' + JSON.stringify(data);
  } catch (e) {
    return line;
  }
}

function processChunk(line, modelType) {
  if (!line || line.trim() === '') return '';
  if (modelType === 'qwen') return cleanQwenChunk(line);
  if (modelType === 'kimi') return cleanKimiChunk(line);
  return line;
}

const server = http.createServer((req, res) => {
  if (req.method === 'OPTIONS') {
    res.writeHead(200, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Authorization' });
    res.end();
    return;
  }

  let body = '';
  req.on('data', chunk => { body += chunk.toString(); });
  req.on('end', () => {
    let requestBody;
    try { requestBody = JSON.parse(body); } catch (e) { res.writeHead(400); res.end(JSON.stringify({ error: 'Invalid JSON' })); return; }

    const modelType = getModelType(requestBody.model);
    console.log(`[${new Date().toISOString()}] 模型: ${requestBody.model}, 类型: ${modelType}`);

    const options = { hostname: '127.0.0.1', port: CHAT2API_PORT, path: req.url, method: req.method, headers: { 'Content-Type': 'application/json', 'Authorization': req.headers['authorization'] || 'Bearer sk-local-free' } };
    const proxyReq = http.request(options, (proxyRes) => {
      const isStreaming = requestBody.stream !== false;
      res.writeHead(proxyRes.statusCode, { 'Content-Type': proxyRes.headers['content-type'] || 'application/json', 'Access-Control-Allow-Origin': '*' });
      if (!isStreaming || proxyRes.headers['content-type']?.includes('application/json')) { proxyRes.pipe(res); return; }

      let buffer = '';
      proxyRes.on('data', (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        const processedLines = [];
        for (const line of lines) {
          if (line.trim() === '') continue;
          const processed = processChunk(line, modelType);
          if (processed) processedLines.push(processed);
        }
        if (processedLines.length > 0) res.write(processedLines.join('\n') + '\n\n');
      });
      proxyRes.on('end', () => { if (buffer.trim()) { const processed = processChunk(buffer, modelType); if (processed) res.write(processed + '\n'); } res.end(); });
    });
    proxyReq.on('error', (err) => { res.writeHead(502); res.end(JSON.stringify({ error: 'Chat2API 连接失败', details: err.message })); });
    proxyReq.write(JSON.stringify(requestBody));
    proxyReq.end();
  });
});

server.listen(MIDDLEWARE_PORT, () => {
  console.log('='.repeat(60));
  console.log('SSE 清洗中间件已启动');
  console.log(`监听端口: ${MIDDLEWARE_PORT}`);
  console.log(`代理目标: Chat2API (端口 ${CHAT2API_PORT})`);
  console.log(`API 地址: http://127.0.0.1:${MIDDLEWARE_PORT}/v1`);
  console.log('='.repeat(60));
});