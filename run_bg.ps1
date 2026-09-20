$python = "e:\仪度六壬择日\yiduluren\.venv\Scripts\python.exe"
$script = "e:\仪度六壬择日\yiduluren\start_training_v4.py"
$wd = "e:\仪度六壬择日\yiduluren"

Start-Process -FilePath $python -ArgumentList $script -WorkingDirectory $wd -WindowStyle Hidden

Write-Host "Training started in background!"
Write-Host "Use: Get-Process -Name python to check"
Write-Host "Log file: training_v4_*.txt"
