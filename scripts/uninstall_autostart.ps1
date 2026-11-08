$startupVbs = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'TikTok_Bot_AutoStart.vbs')
if (Test-Path $startupVbs) {
    Remove-Item -Path $startupVbs -Force
    Write-Host "* Da xoa file khoi dong tai Windows Startup." -ForegroundColor Yellow
}

Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'TikTokAutoNotifier' -ErrorAction SilentlyContinue
Write-Host "* Da xoa khoi Registry HKCU Run." -ForegroundColor Yellow

Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "[THANH CONG] DA HUY TU DONG KHOI DONG CUNG WINDOWS!" -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Green
