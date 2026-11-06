@echo off
chcp 65001 >nul
title TIKTOK BETA US - AUTOMATION NOTIFIER ENGINE
echo ==============================================================================
echo           TIKTOK BETA US - HỆ THỐNG TỰ ĐỘNG QUÉT VIDEO MỚI
echo ==============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LỖI] Không tìm thấy môi trường ảo .venv! Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

echo Đang khởi động hệ thống quét liên tục...
echo (Nhấn Ctrl+C để dừng hệ thống bất kỳ lúc nào)
echo.

.\.venv\Scripts\python.exe run.py

echo.
echo ==============================================================================
echo Hệ thống đã dừng. Nhấn phím bất kỳ để thoát...
pause >nul
