$baseDir = Split-Path -Parent $PSScriptRoot

$vbsCode = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "$baseDir"
cmd = chr(34) & "$baseDir\.venv\Scripts\pythonw.exe" & chr(34) & " " & chr(34) & "$baseDir\run.py" & chr(34)
WshShell.Run cmd, 0, False
"@

$startupVbs = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'TikTok_Bot_AutoStart.vbs')
[System.IO.File]::WriteAllText($startupVbs, $vbsCode, [System.Text.Encoding]::ASCII)

$vbsRunPath = Join-Path $baseDir "Chay_Ngam_Khong_Cua_So.vbs"
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'TikTokAutoNotifier' -Value "wscript.exe `"$vbsRunPath`""

Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "[THANH CONG] DA CAI DAT BOT TU DONG CHAY KHI MO MAY TINH!" -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "* Da tao file khoi dong tai: $startupVbs" -ForegroundColor Cyan
Write-Host "* Da dang ky vao Registry: HKCU\...\Run\TikTokAutoNotifier" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tu nay moi khi ban bat may tinh len, Bot se tu dong chay ngam 24/7 khong can bam nut." -ForegroundColor Green
