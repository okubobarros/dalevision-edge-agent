Option Explicit

Dim fso, shell, scriptPath, installRoot, runCmdPath, cmd, rc
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptPath = WScript.ScriptFullName
installRoot = fso.GetParentFolderName(scriptPath)
runCmdPath = installRoot & "\run_agent.cmd"

If Not fso.FileExists(runCmdPath) Then
  WScript.Quit 3
End If

cmd = "cmd.exe /c " & """" & runCmdPath & """"
rc = shell.Run(cmd, 0, True)
WScript.Quit rc
