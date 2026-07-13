# Create a desktop shortcut that launches local_whisper_nemo minimized.
$root = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut((Join-Path $desktop 'local_whisper_nemo.lnk'))
$lnk.TargetPath = Join-Path $root 'run.bat'
$lnk.WorkingDirectory = $root
$lnk.IconLocation = 'shell32.dll,138'
$lnk.WindowStyle = 7  # minimized
$lnk.Description = 'local_whisper_nemo push-to-talk dictation'
$lnk.Save()
Write-Host "Shortcut created on the desktop."
