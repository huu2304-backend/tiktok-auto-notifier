' TikTok Beta US - VBScript Chạy Ngầm Không Hiện Cửa Sổ (Silent Background Runner)
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Lay duong dan thu muc chua script nay
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

' Lenh thuc thi Python run.py (an hoan toan cua so cmd)
cmd = """" & scriptDir & "\.venv\Scripts\python.exe"" """ & scriptDir & "\run.py"""

' Tham so 0: Chay an hoan toan khong hien popup hay console
WshShell.Run cmd, 0, False
