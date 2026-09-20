$p = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "train_r14_simple.py" -WindowStyle Hidden -PassThru

if ($p -and $p.Id) {
    Write-Host ("Training PID: " + $p.Id)
} else {
    Write-Host "Failed to start process"
}
