Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

strDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strDir

pythonwPath = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe")
If Not fso.FileExists(pythonwPath) Then
    pythonwPath = "pythonw.exe"
End If

WshShell.Run """" & pythonwPath & """ -X utf8 canvas_app.py", 1, False
