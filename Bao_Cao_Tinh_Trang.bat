@echo off
chcp 65001 >nul
title TIKTOK BETA US - BÁO CÁO TÌNH TRẠNG HỆ THỐNG
echo ==============================================================================
echo       TIKTOK BETA US - BÁO CÁO SỨC KHỎE MẠNG LƯỚI & THỐNG KÊ
echo ==============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LỖI] Không tìm thấy môi trường ảo .venv! Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

.\.venv\Scripts\python.exe run.py --status

echo ==============================================================================
echo Nhấn phím bất kỳ để đóng cửa sổ này...
pause >nul
