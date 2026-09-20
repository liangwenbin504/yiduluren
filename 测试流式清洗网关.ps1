$models = @('qwen-turbo', 'kimi-k2-0711-preview', 'glm-5.1')
foreach ($model in $models) {
    Write-Host "`n测试模型: $model" -ForegroundColor Cyan
    $body = @{ model = $model; messages = @(@{ role = "user"; content = "你好" }); max_tokens = 50 } | ConvertTo-Json -Depth 3
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:8081/v1/chat/completions" -Method Post -ContentType "application/json" -Headers @{ Authorization = "Bearer sk-local-free" } -Body $body -TimeoutSec 30
        Write-Host "成功: $($r.choices[0].message.content)" -ForegroundColor Green
    } catch {
        Write-Host "失败: $_" -ForegroundColor Red
    }
}