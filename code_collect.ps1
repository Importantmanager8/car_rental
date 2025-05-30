# pour laner l'application tape:powershell.exe -ExecutionPolicy Bypass -File .\code_collect.ps1
$workspaceDir = Get-Location
$tempFile = "$env:TEMP\code_content.txt"

# Définir les extensions de fichiers à inclure
$fileExtensions = "*.php", "*.blade.php", "*.py", "*.html", "*.css"

# Trouver les fichiers
$files = Get-ChildItem -Path $workspaceDir -Recurse -Include $fileExtensions -File | 
    Where-Object { $_.FullName -notmatch '\\vendor\\|\\node_modules\\|\\.git\\|\\storage\\|\\public\\|\\bootstrap\\|\\dist\\|\\build\\' }

# Vérifier les fichiers
$fileCount = $files.Count
if ($fileCount -eq 0) {
    Write-Host "Aucun fichier trouvé."
    exit
}
Write-Host "Nombre de fichiers trouvés: $fileCount"

# Vider le fichier temporaire
"" | Out-File -FilePath $tempFile -Encoding UTF8

# Ajouter le contenu des fichiers
foreach ($file in $files) {
    "// FICHIER: $($file.FullName)" | Add-Content -Path $tempFile -Encoding UTF8
    Get-Content -Path $file.FullName | Add-Content -Path $tempFile -Encoding UTF8
    "`n" | Add-Content -Path $tempFile -Encoding UTF8
}

# Copier dans le presse-papiers
Get-Content -Path $tempFile | Set-Clipboard
Write-Host "Contenu copié dans le presse-papiers!"

# Nettoyer
Remove-Item -Path $tempFile -ErrorAction SilentlyContinue