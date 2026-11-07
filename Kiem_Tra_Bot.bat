@echo off
chcp 65001 >nul
title KIỂM TRA TRẠNG THÁI BOT CHẠY NGẦM
echo ==============================================================================
echo       TIKTOK BETA US - KIỂM TRA TRẠNG THÁI TIẾN TRÌNH BOT
echo ==============================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run.py*' -or $_.CommandLine -like '*tiktok-auto-notifier*' }; if ($procs) { Write-Host '🟢 BOT ĐANG CHẠY NGẦM HOẠT ĐỘNG TỐT!' -ForegroundColor Green; foreach ($p in $procs) { Write-Host ('   • PID: ' + $p.ProcessId + ' | Bộ nhớ: ' + [math]::Round($p.WorkingSetSize/1MB, 1) + ' MB | Khởi chạy: ' + $p.CreationDate) } } else { Write-Host '🔴 BOT HIỆN TẠI KHÔNG CHẠY!' -ForegroundColor Red; Write-Host '   Hãy bấm file Chay_He_Thong.bat hoặc Chay_Ngam_Khong_Cua_So.vbs để bật bot lên.' }"

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để thoát...
pause >nul
