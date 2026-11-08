@echo off
chcp 65001 >nul
title DỪNG BOT CHẠY NGẦM
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_bot.ps1"

echo.
echo Cửa sổ này sẽ tự động đóng sau 3 giây...
timeout /t 3 /nobreak >nul
