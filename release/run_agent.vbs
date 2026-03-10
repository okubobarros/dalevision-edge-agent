Option Explicit

Dim fso, shell, scriptPath, installRoot, psExe, ps1, cmd, rc
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptPath = WScript.ScriptFullName
installRoot = fso.GetParentFolderName(scriptPath)
psExe = shell.ExpandEnvironmentStrings("%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe")
ps1 = installRoot & "\scripts\internal\Start_DaleVision_Agent.ps1"

If Not fso.FileExists(psExe) Then
  WScript.Quit 2
End If

If Not fso.FileExists(ps1) Then
  WScript.Quit 3
End If

cmd = """" & psExe & """" & _
      " -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass" & _
      " -File " & """" & ps1 & """" & _
      " -InstallDir " & """" & installRoot & """"

rc = shell.Run(cmd, 0, True)
WScript.Quit rc

