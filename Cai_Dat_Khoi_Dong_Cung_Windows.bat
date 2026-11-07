@echo off
chcp 65001 >nul
title CÀI ĐẶT TỰ ĐỘNG CHẠY BOT CÙNG WINDOWS
echo ==============================================================================
echo       TIKTOK BETA US - CÀI ĐẶT BOT TỰ ĐỘNG CHẠY NGẦM KHI MỞ MÁY
echo ==============================================================================
echo.

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$vbsCode = @' `
Set WshShell = CreateObject(`"WScript.Shell`") `
WshShell.CurrentDirectory = `"%~dp0`" `
cmd = chr(34) & `"%~dp0.venv\Scripts\python.exe`" & chr(34) & `" `" & chr(34) & `"%~dp0run.py`" & chr(34) `
WshShell.Run cmd, 0, False `
'@; `
$startupVbs = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'TikTok_Bot_AutoStart.vbs'); `
[System.IO.File]::WriteAllText($startupVbs, $vbsCode.Replace('`n', [Environment]::NewLine), [System.Text.Encoding]::ASCII); `
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'TikTokAutoNotifier' -Value ('wscript.exe `"' + '%~dp0Chay_Ngam_Khong_Cua_So.vbs' + '`"'); `
Write-Host '[THÀNH CÔNG] Đã thiết lập tự khởi động cùng Windows (Startup Folder + Registry Run)!' -ForegroundColor Green"

echo.
echo ==============================================================================
echo Từ nay mỗi khi bật máy, bot sẽ tự động chạy ngầm 24/7.
echo Nhấn phím bất kỳ để thoát...
pause >nul
