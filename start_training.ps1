$logFile = "e:\仪度六壬择日\yiduluren\training_stdout.txt"
$errFile = "e:\仪度六壬择日\yiduluren\training_stderr.txt"

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "e:\仪度六壬择日\yiduluren\.venv\Scripts\python.exe"
$psi.Arguments = "train_r14_simple.py"
$psi.WorkingDirectory = "e:\仪度六壬择日\yiduluren"
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError = $false
$psi.CreateNoWindow = $true

# Use file-level redirection
$psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
$psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"

$p = [System.Diagnostics.Process]::Start($psi)
Write-Host ("PID: " + $p.Id)
$p.WaitForExit(3000)  # 3s check
if (-not $p.HasExited) {
    Write-Host "Training running in background (PID: $($p.Id))"
} else {
    Write-Host "Exit code: $($p.ExitCode)"
}
