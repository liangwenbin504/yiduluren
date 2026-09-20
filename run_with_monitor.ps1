$python = ".venv\Scripts\python.exe"
$script = "train_r14_simple.py"
$logFile = "training_output.log"
$errFile = "training_error.log"

Write-Host "Starting training..."
$p = Start-Process -FilePath $python -ArgumentList $script -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errFile -PassThru
Write-Host ("PID: " + $p.Id)

while (!$p.HasExited) {
    Write-Host ("[heartbeat] " + (Get-Date -Format "HH:mm:ss") + " PID=" + $p.Id + " running")
    Start-Sleep -Seconds 10
    $p.Refresh()
}

Write-Host "Process exited with code: " + $p.ExitCode
Write-Host "Last 20 lines of output:"
Get-Content $logFile -Tail 20 -ErrorAction SilentlyContinue
