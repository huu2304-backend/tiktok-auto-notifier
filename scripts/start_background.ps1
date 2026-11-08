$baseDir = Split-Path -Parent $PSScriptRoot

$procs = Get-CimInstance Win32_Process | Where-Object { 
    $_.CommandLine -like "*run.py*" -and ($_.Name -like "python*.exe")
}

if ($procs) {
    Write-Host "[CANH BAO] Bot hien da dang chay roi (PID: $(($procs.ProcessId) -join ', '))." -ForegroundColor Yellow
} else {
    $pythonwPath = Join-Path $baseDir ".venv\Scripts\pythonw.exe"
    $runPyPath = Join-Path $baseDir "run.py"
    $cmdLine = "`"$pythonwPath`" `"$runPyPath`""

    $result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine = $cmdLine
        CurrentDirectory = $baseDir
    }

    Start-Sleep -Seconds 3

    $newProcs = Get-CimInstance Win32_Process | Where-Object { 
        $_.CommandLine -like "*run.py*" -and ($_.Name -like "python*.exe")
    }

    if ($newProcs) {
        Write-Host "==============================================================================" -ForegroundColor Green
        Write-Host "[THANH CONG] BOT DA DUOC KHOI DONG CHAY NGAM HOAN TOAN 100%!" -ForegroundColor Green
        Write-Host "==============================================================================" -ForegroundColor Green
        foreach ($p in $newProcs) {
            $memMB = [math]::Round($p.WorkingSetSize / 1MB, 1)
            Write-Host "   * PID: $($p.ProcessId) | RAM: $memMB MB | Khoi chay: $($p.CreationDate)" -ForegroundColor Cyan
        }
        Write-Host ""
        Write-Host "• Bot dang chay ngam tang hinh, KHONG co bat ky cua so CMD nao tren man hinh." -ForegroundColor Cyan
        Write-Host "• Ban co the tat Antigravity thoai mai ma bot van hoat dong 24/7 tren may tinh." -ForegroundColor Cyan
    } else {
        Write-Host "[LOI] Khong the khoi dong bot. Vui long kiem tra file logs\app.log." -ForegroundColor Red
    }
}
