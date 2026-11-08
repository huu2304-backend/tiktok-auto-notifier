$baseDir = Split-Path -Parent $PSScriptRoot

$procs = Get-CimInstance Win32_Process | Where-Object { 
    $_.CommandLine -like "*run.py*" -and ($_.Name -like "python*.exe")
}

if ($procs) {
    Write-Host "==============================================================================" -ForegroundColor Green
    Write-Host "[DANG CHAY] BOT DANG CHAY NGAM HOAT DONG TOT 24/7!" -ForegroundColor Green
    Write-Host "==============================================================================" -ForegroundColor Green
    foreach ($p in $procs) {
        $memMB = [math]::Round($p.WorkingSetSize / 1MB, 1)
        Write-Host "   * PID: $($p.ProcessId) | RAM: $memMB MB | Start: $($p.CreationDate)" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "--- 10 DONG NHAT KY MOI NHAT (logs/app.log) ---" -ForegroundColor Yellow
    $logPath = Join-Path $baseDir "logs\app.log"
    if (Test-Path $logPath) {
        Get-Content $logPath -Tail 10
    }
} else {
    Write-Host "==============================================================================" -ForegroundColor Red
    Write-Host "[DANG TAT] BOT HIEN TAI DANG TAT (KHONG CHAY)!" -ForegroundColor Red
    Write-Host "==============================================================================" -ForegroundColor Red
    Write-Host "   Hay bam file [1] Bat_Dau_Chay_Ngam.bat de bat bot len." -ForegroundColor Yellow
}
