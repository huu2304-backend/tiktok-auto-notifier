@echo off
chcp 65001 >nul
title TIKTOK BETA US - KHỞI TẠO MỐC DỮ LIỆU BAN ĐẦU (SEED BASELINE)
echo ==============================================================================
echo       TIKTOK BETA US - KHỞI TẠO MỐC DỮ LIỆU (SEED BASELINE)
echo ==============================================================================
echo.
echo [MỤC ĐÍCH]
echo   Quét toàn bộ video hiện có trên các kênh YouTube và lưu vào cơ sở dữ liệu làm
echo   mốc cơ sở.
echo   -> KHÔNG GỬI THÔNG BÁO VỀ TELEGRAM (Tránh spam hàng trăm video cũ).
echo   -> Kể từ sau lệnh này, chỉ những video MỚI RA LÒ mới được gửi về máy bạn!
echo.
echo ==============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LỖI] Không tìm thấy môi trường ảo .venv! Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

echo Đang tiến hành quét và nạp mốc dữ liệu...
.\.venv\Scripts\python.exe run.py --seed

echo.
echo ==============================================================================
echo Hoàn thành! Nhấn phím bất kỳ để đóng cửa sổ này...
pause >nul
