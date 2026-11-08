@echo off
chcp 65001 >nul
title KIỂM TRA TRẠNG THÁI BOT CHẠY NGẦM
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\status_bot.ps1"

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để đóng bảng kiểm tra...
pause >nul
