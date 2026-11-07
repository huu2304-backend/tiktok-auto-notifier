@echo off
chcp 65001 >nul
title HỦY TỰ ĐỘNG KHỞI ĐỘNG CÙNG WINDOWS
echo ==============================================================================
echo       TIKTOK BETA US - HỦY TỰ ĐỘNG CHẠY BOT KHI BẬT MÁY
echo ==============================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$startupVbs = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'TikTok_Bot_AutoStart.vbs'); `
if (Test-Path $startupVbs) { Remove-Item -Force $startupVbs; Write-Host '[ĐÃ XÓA] File trong thư mục Startup.' -ForegroundColor Yellow }; `
Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'TikTokAutoNotifier' -ErrorAction SilentlyContinue; `
Write-Host '✅ Đã hủy tự khởi động cùng Windows thành công.' -ForegroundColor Green"

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để thoát...
pause >nul
