@echo off
chcp 65001 >nul
title TIKTOK BETA US - AUTOMATION NOTIFIER ENGINE
cd /d "%~dp0"

echo ==============================================================================
echo           TIKTOK BETA US - HỆ THỐNG TỰ ĐỘNG QUÉT VIDEO MỚI (CHẠY NGẦM)
echo ==============================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_background.ps1"

echo.
echo Cửa sổ này sẽ tự động đóng sau 4 giây...
timeout /t 4 /nobreak >nul
