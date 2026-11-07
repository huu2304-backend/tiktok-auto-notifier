@echo off
chcp 65001 >nul
title HỦY TỰ ĐỘNG KHỞI ĐỘNG CÙNG WINDOWS
echo ==============================================================================
echo       TIKTOK BETA US - HỦY TỰ ĐỘNG CHẠY BOT KHI BẬT MÁY
echo ==============================================================================
echo.

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TARGET_VBS=%STARTUP_DIR%\TikTok_Bot_AutoStart.vbs"

if exist "%TARGET_VBS%" (
    del /f /q "%TARGET_VBS%"
    echo [ĐÃ HỦY] Đã xóa file tự khởi động khỏi thư mục Windows Startup.
) else (
    echo [THÔNG BÁO] Hệ thống chưa từng cài đặt tự khởi động.
)

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để thoát...
pause >nul
