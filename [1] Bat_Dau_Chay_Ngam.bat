@echo off
chcp 65001 >nul
title KHỞI ĐỘNG BOT CHẠY NGẦM
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_background.ps1"

echo.
echo Cửa sổ này sẽ tự động đóng sau 4 giây...
timeout /t 4 /nobreak >nul
