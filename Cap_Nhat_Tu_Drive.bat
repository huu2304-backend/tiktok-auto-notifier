@echo off
chcp 65001 >nul
title ĐỒNG BỘ CẤU HÌNH TIKTOK BETA US TỪ GOOGLE DRIVE
echo ==============================================================================
echo           TIKTOK BETA US - ĐỒNG BỘ CẤU HÌNH TỪ GOOGLE DRIVE
echo ==============================================================================
echo.
echo [GHI CHÚ]:
echo - File này sẽ tự động kết nối Google Sheets và tải bảng tính mới nhất về máy.
echo - Nếu sau này bạn đổi link Google Sheets, chỉ cần mở file .env và sửa dòng:
echo   GOOGLE_SHEET_URL=link_moi_cua_ban
echo.
echo ==============================================================================

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LỖI] Không tìm thấy môi trường ảo .venv! Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

echo Đang kết nối tới Google Sheets và cập nhật file cấu hình...
echo.

.\.venv\Scripts\python.exe run.py --sync-gdrive

echo.
echo ==============================================================================
echo Nhấn phím bất kỳ để đóng cửa sổ này...
pause >nul
