<#
Helper PowerShell script to initialize a git repo and push to GitHub.
This script does NOT store your credentials. Replace <REMOTE_URL> with your repo URL.

Usage (PowerShell):
  .\scripts\push_to_github.ps1 -RemoteUrl 'https://github.com/USER/REPO.git' -Branch 'main'
#>

param(
    [string]$RemoteUrl,
    [string]$Branch = 'main'
)

if (-not $RemoteUrl) {
    Write-Host "Please provide -RemoteUrl 'https://github.com/USER/REPO.git'"
    exit 1
}

Write-Host "Initializing git (if needed) and pushing to $RemoteUrl ..."
if (-not (Test-Path .git)) {
    git init
    git add .
    git commit -m "Prepare repo for deployment"
    git branch -M $Branch
    git remote add origin $RemoteUrl
} else {
    git add .
    git commit -m "Prepare repo for deployment" -ErrorAction SilentlyContinue
}

Write-Host "Now attempting to push. You may be prompted for credentials or use an SSH key."
git push -u origin $Branch
