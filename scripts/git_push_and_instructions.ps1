<#
Usage: .\scripts\git_push_and_instructions.ps1 [-Message "Commit message"] [-All]

This script stages files, creates a commit (if there are changes) and pushes to
`origin main`. It then prints the commands you should run on PythonAnywhere to
pull the latest changes and reload the app.

Notes:
- This script does not run any remote commands on PythonAnywhere; it only prints
  the recommended steps.
- If you prefer to commit all changes, pass the -All switch.
#>

param(
    [string]$Message = "Actualización: sincronizar con PythonAnywhere",
    [switch]$All
)

# Move to repository root (script lives in scripts/)
$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location -Path $scriptDir
Set-Location -Path ..

Write-Host "Repository root: $(Get-Location)" -ForegroundColor Cyan

# Check git status
git status --porcelain
if ($LASTEXITCODE -ne 0) {
    Write-Error "git no está disponible o este no es un repositorio git."
    exit 1
}

if ($All) {
    Write-Host "Staging all changes..." -ForegroundColor Yellow
    git add -A
} else {
    Write-Host "Staging common files (app.py, templates/index.html, static/js/main.js)..." -ForegroundColor Yellow
    git add app.py templates/index.html static/js/main.js 2>$null
    # if explicit files don't exist, fall back to add all
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Fallo al añadir archivos concretos; añadiendo todo el working tree." -ForegroundColor Yellow
        git add -A
    }
}

# Commit
git commit -m "$Message" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "No se creó commit (posible: no hay cambios). Continuando con push..." -ForegroundColor Yellow
}

# Push to origin/main
Write-Host "Pushing to origin main..." -ForegroundColor Cyan
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Error "git push falló. Revisa autentificación/remote y vuelve a intentarlo."
    exit 1
}

Write-Host "\nPush completado correctamente." -ForegroundColor Green

# Instructions for PythonAnywhere
$paUser = "manuelvar22"  # cambia si tu usuario en PythonAnywhere es otro
Write-Host "\nSiguientes pasos (ejecutar en PythonAnywhere Bash):" -ForegroundColor Cyan
Write-Host "1) Conectarte via SSH (opcional) o abrir una consola Bash en PythonAnywhere" -ForegroundColor White
Write-Host "   ssh $paUser@ssh.pythonanywhere.com" -ForegroundColor Gray
Write-Host "2) Ir al directorio del proyecto" -ForegroundColor White
Write-Host "   cd ~/Lading-formulario" -ForegroundColor Gray
Write-Host "3) Traer los cambios" -ForegroundColor White
Write-Host "   git pull origin main" -ForegroundColor Gray
Write-Host "4) Activar virtualenv y actualizar dependencias (si aplica)" -ForegroundColor White
Write-Host "   source .venv/bin/activate" -ForegroundColor Gray
Write-Host "   pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "5) (Opcional) Ejecutar el helper de despliegue" -ForegroundColor White
Write-Host "   ./deploy/deploy_to_pa.sh" -ForegroundColor Gray
Write-Host "6) En el panel Web de PythonAnywhere, abrir tu app y pulsar 'Reload'" -ForegroundColor White

Write-Host "\nSi quieres que el script haga commit de todos los archivos, ejecuta:" -ForegroundColor Cyan
Write-Host "  .\\scripts\\git_push_and_instructions.ps1 -All -Message 'Tu mensaje'" -ForegroundColor Gray

Write-Host "\nListo. Pega aquí cualquier error de git push o la salida de git pull en PythonAnywhere si necesitas ayuda." -ForegroundColor Green
