$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Ditado Inteligente.lnk")
$Shortcut.TargetPath = "C:\Users\ferna\OneDrive\Documentos\Projetos AntiGravity\Projetos no Desktop Consultorio\unified-transcription-suite\dist_v15\UnifiedTranscriptionSuite_v14_final\UnifiedTranscriptionSuite_v14_final.exe"
$Shortcut.WorkingDirectory = "C:\Users\ferna\OneDrive\Documentos\Projetos AntiGravity\Projetos no Desktop Consultorio\unified-transcription-suite\dist_v15\UnifiedTranscriptionSuite_v14_final"
$Shortcut.IconLocation = "C:\Users\ferna\OneDrive\Documentos\Projetos AntiGravity\Projetos no Desktop Consultorio\unified-transcription-suite\assets\icon.ico"
$Shortcut.Save()
Write-Host "Atalho criado com sucesso na área de trabalho!"
