@echo off
chcp 65001 >nul
title DỪNG TOÀN BỘ TIẾN TRÌNH BOT TIKTOK
echo ==============================================================================
echo       TIKTOK BETA US - DỪNG BOT VÀ TIẾN TRÌNH CHẠY NGẦM
echo ==============================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run.py*' -or $_.CommandLine -like '*tiktok-auto-notifier*' }; if ($procs) { foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force; Write-Host ('[ĐÃ DỪNG] Tiến trình PID: ' + $p.ProcessId) -ForegroundColor Yellow } Write-Host '✅ Đã dừng toàn bộ bot thành công.' -ForegroundColor Green } else { Write-Host 'ℹ️ Không có tiến trình bot nào đang chạy.' -ForegroundColor Cyan }"

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để thoát...
pause >nul
