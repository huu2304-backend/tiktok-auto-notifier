@echo off
chcp 65001 >nul
title TIKTOK BETA US - TELEGRAM BOT INTERACTIVE LISTENER
echo ==============================================================================
echo       TIKTOK BETA US - BỘ LẮNG NGHE LỆNH & NÚT BẤM TELEGRAM BOT
echo ==============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LỖI] Không tìm thấy môi trường ảo .venv! Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

echo Đang khởi động bộ nhận lệnh Telegram Bot...
echo Các lệnh hỗ trợ từ điện thoại:
echo   • Bấm [ 🚀 Quét Video Mới ]       hoặc gõ /videos
echo   • Bấm [ 🔄 Cập Nhật Google Drive ] hoặc gõ /update
echo   • Bấm [ 📊 Xem Báo Cáo 22 Máy ]   hoặc gõ /status
echo   • Bấm [ 💡 Hướng Dẫn ]            hoặc gõ /help
echo.
echo (Nhấn Ctrl+C để dừng bot bất kỳ lúc nào)
echo.

.\.venv\Scripts\python.exe run.py --bot

echo.
echo ==============================================================================
echo Bot đã dừng. Nhấn phím bất kỳ để thoát...
pause >nul
