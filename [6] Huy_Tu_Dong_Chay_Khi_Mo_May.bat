@echo off
chcp 65001 >nul
title HỦY TỰ ĐỘNG CHẠY BOT KHI MỞ MÁY
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\uninstall_autostart.ps1"

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để thoát...
pause >nul
