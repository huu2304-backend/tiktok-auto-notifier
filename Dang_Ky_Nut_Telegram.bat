@echo off
chcp 65001 >nul
title TIKTOK BETA US - ĐĂNG KÝ MENU & NÚT BẤM TELEGRAM BOT
echo ==============================================================================
echo       TIKTOK BETA US - ĐĂNG KÝ SLASH COMMANDS & BÀN PHÍM TƯƠNG TÁC
echo ==============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LỖI] Không tìm thấy môi trường ảo .venv! Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

echo Đang gửi cấu hình menu và bàn phím tương tác lên Telegram...
echo.

.\.venv\Scripts\python.exe run.py --setup-bot-commands

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để thoát...
pause >nul
