Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\PC\.gemini\antigravity\scratch\tiktok-auto-notifier"
cmd = chr(34) & "C:\Users\PC\.gemini\antigravity\scratch\tiktok-auto-notifier\.venv\Scripts\pythonw.exe" & chr(34) & " " & chr(34) & "C:\Users\PC\.gemini\antigravity\scratch\tiktok-auto-notifier\run.py" & chr(34)
WshShell.Run cmd, 0, False
