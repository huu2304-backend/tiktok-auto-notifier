@echo off
chcp 65001 >nul
title THIẾT LẬP KẾT NỐI TELEGRAM BOT TỰ ĐỘNG
echo ==============================================================================
echo           TIKTOK BETA US - CÀI ĐẶT TELEGRAM BOT TỰ ĐỘNG
echo ==============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LỖI] Không tìm thấy môi trường ảo .venv! Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

.\.venv\Scripts\python.exe scripts/setup_telegram.py

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để đóng cửa sổ này...
pause >nul
