# Script to register secrets in GitHub Secrets via GitHub CLI
# Usage: .\scripts\setup-github-secrets.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$SecretValue,

    [Parameter(Mandatory=$false)]
    [string]$SecretName = "AZURE_CLIENT_SECRET",

    [Parameter(Mandatory=$false)]
    [string]$Repository = "seu-usuario/DataMasterV2"
)

# Check if GitHub CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) not installed. Install at: https://cli.github.com/"
    exit 1
}

# Check if authenticated in GitHub
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "You are not authenticated in GitHub CLI. Run: gh auth login"
    exit 1
}

Write-Host "Authenticated in GitHub CLI" -ForegroundColor Green

# Check if repository exists
Write-Host "Checking repository: $Repository" -ForegroundColor Yellow
$repoInfo = gh repo view $Repository 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Repository $Repository not found or you do not have access."
    Write-Host "Use format: usuario/repositorio"
    exit 1
}

Write-Host "Repository found: $Repository" -ForegroundColor Green

# Register the secret
Write-Host "Registering secret: $SecretName" -ForegroundColor Yellow
$secretOutput = gh secret set $SecretName --body $SecretValue --repo $Repository 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Secret registered successfully!" -ForegroundColor Green
    Write-Host "Name: $SecretName" -ForegroundColor Cyan
    Write-Host "Repository: $Repository" -ForegroundColor Cyan
} else {
    Write-Error "Error registering secret: $secretOutput"
    exit 1
}

# List repository secrets (optional, for verification)
Write-Host ""
Write-Host "Current secrets in repository:" -ForegroundColor Yellow
gh secret list --repo $Repository

