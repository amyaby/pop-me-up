Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

srcFolder = fso.GetParentFolderName(WScript.ScriptFullName) & "\app"
dstFolder = WshShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\popup-reminder\app"

WshShell.Run "robocopy """ & srcFolder & """ """ & dstFolder & """ /E /XD node_modules /NFL /NDL /NJH /NJS", 0, True
WshShell.Run """" & dstFolder & "\node_modules\electron\dist\electron.exe"" """ & dstFolder & """", 0, False