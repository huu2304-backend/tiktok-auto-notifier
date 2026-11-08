$procs = Get-CimInstance Win32_Process | Where-Object { 
    $_.CommandLine -like "*run.py*" -and ($_.Name -like "python*.exe")
}

if ($procs) {
    foreach ($p in $procs) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[DA DUNG] Tien trinh PID: $($p.ProcessId)" -ForegroundColor Yellow
    }
    Write-Host "==============================================================================" -ForegroundColor Green
    Write-Host "[THANH CONG] Da dung toan bo tien trinh bot chay ngam an toan!" -ForegroundColor Green
    Write-Host "==============================================================================" -ForegroundColor Green
} else {
    Write-Host "[THONG BAO] Khong co tien trinh bot nao dang chay." -ForegroundColor Cyan
}
