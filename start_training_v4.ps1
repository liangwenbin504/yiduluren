$python = "e:\仪度六壬择日\yiduluren\.venv\Scripts\python.exe"
$wd = "e:\仪度六壬择日\yiduluren"
$logFile = "e:\仪度六壬择日\yiduluren\training_v4_log.txt"

$cmd = "import sys; sys.path.insert(0, '$wd'); sys.argv = ['train_r14_simple.py', '--input', 'unified_cases_training.json', '--output', 'r14_training_results_v3.json', '--few-shot-pool', 'few_shot_pool.json']; exec(open('$wd/train_r14_simple.py', encoding='utf-8').read())"

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python
$psi.Arguments = "-c `"$cmd`""
$psi.WorkingDirectory = $wd
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError = $false
$psi.CreateNoWindow = $true
$psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
$psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"

$log = New-Object System.Diagnostics.ProcessStartInfo
$log.FileName = "cmd.exe"
$log.Arguments = "/c `"type nul > `"$logFile`"`""
$log.UseShellExecute = $false
$log.CreateNoWindow = $true
[System.Diagnostics.Process]::Start($log) | Out-Null

$p = [System.Diagnostics.Process]::Start($psi)
Write-Host ("Training PID: " + $p.Id)
Write-Host ("Log: $logFile")
Write-Host ("Dataset: unified_cases_training.json (920 cases)")
Write-Host ("Pool: few_shot_pool.json (887 seeds)")
Write-Host ("Output: r14_training_results_v3.json")
