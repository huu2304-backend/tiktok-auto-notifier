@echo off
chcp 65001 >nul
title CÀI ĐẶT TỰ ĐỘNG CHẠY BOT KHI MỞ MÁY TÍNH
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_autostart.ps1"

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để thoát...
pause >nul
