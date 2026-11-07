@echo off
chcp 65001 >nul
title CÀI ĐẶT TỰ ĐỘNG CHẠY BOT CÙNG WINDOWS
echo ==============================================================================
echo       TIKTOK BETA US - CÀI ĐẶT BOT TỰ ĐỘNG CHẠY NGẦM KHI MỞ MÁY
echo ==============================================================================
echo.

cd /d "%~dp0"

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TARGET_VBS=%STARTUP_DIR%\TikTok_Bot_AutoStart.vbs"

echo Đang tạo cấu hình tự khởi động tại:
echo %TARGET_VBS%
echo.

(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.CurrentDirectory = "%~dp0"
echo cmd = """" ^& "%~dp0.venv\Scripts\python.exe" ^& """ """ ^& "%~dp0run.py" ^& """"
echo WshShell.Run cmd, 0, False
) > "%TARGET_VBS%"

if exist "%TARGET_VBS%" (
    echo [THÀNH CÔNG] Đã cài đặt tự khởi động thành công!
    echo Từ nay, mỗi khi bạn bật máy tính hoặc mở máy lên:
    echo  • Bot sẽ TỰ ĐỘNG CHẠY NGẦM 24/7 (không hiện cửa sổ làm phiền).
    echo  • Bạn có thể mở Telegram ở bất kỳ đâu trên điện thoại để điều khiển ngay lập tức.
) else (
    echo [LỖI] Không thể tạo file trong thư mục Startup.
)

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để thoát...
pause >nul
