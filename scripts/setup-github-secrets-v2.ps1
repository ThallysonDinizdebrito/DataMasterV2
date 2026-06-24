param(
    [Parameter(Mandatory=$true)]
    [string]$SecretValue,
    [Parameter(Mandatory=$false)]
    [string]$SecretName = "AZURE_CLIENT_SECRET",
    [Parameter(Mandatory=$false)]
    [string]$Repository = "seu-usuario/DataMasterV2"
)

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) not installed"
    exit 1
}

$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Not authenticated in GitHub CLI"
    exit 1
}

Write-Host "Authenticated in GitHub CLI" -ForegroundColor Green

Write-Host "Checking repository: $Repository" -ForegroundColor Yellow
$repoInfo = gh repo view $Repository 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Repository not found"
    exit 1
}

Write-Host "Repository found: $Repository" -ForegroundColor Green

Write-Host "Registering secret: $SecretName" -ForegroundColor Yellow
gh secret set $SecretName --body $SecretValue --repo $Repository

if ($LASTEXITCODE -eq 0) {
    Write-Host "Secret registered successfully!" -ForegroundColor Green
} else {
    Write-Error "Error registering secret"
    exit 1
}

Write-Host "Current secrets:" -ForegroundColor Yellow
gh secret list --repo $Repository
