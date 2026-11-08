@echo off
chcp 65001 >nul
title THEO DÕI NHẬT KÝ BOT (REALTIME LOG VIEWER)
cd /d "%~dp0"

echo ==============================================================================
echo       TIKTOK BETA US - CỬA SỔ THEO DÕI NHẬT KÝ THỜI GIAN THỰC
echo ==============================================================================
echo • Đang hiển thị log trực tiếp từ file logs/app.log.
echo • LƯU Ý: Khi bạn bấm [X] tắt cửa sổ này, BOT VẪN TIẾP TỤC CHẠY NGẦM 24/7!
echo ==============================================================================
echo.

if not exist "logs\app.log" (
    echo [THÔNG BÁO] Chưa có file logs\app.log! Vui lòng khởi động bot trước.
    pause
    exit /b 0
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content -Path 'logs\app.log' -Wait -Tail 25"
