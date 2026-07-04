# Script to create secrets in Azure Key Vault
# Usage: .\scripts\set-keyvault-secret.ps1 -VaultName "kv-dmv2dev-vxc02" -SecretName "test-secret" -SecretValue "my-secret-value"

param(
    [Parameter(Mandatory=$true)]
    [string]$VaultName,

    [Parameter(Mandatory=$true)]
    [string]$SecretName,

    [Parameter(Mandatory=$true)]
    [string]$SecretValue,

    [Parameter(Mandatory=$false)]
    [string]$ContentType = "text/plain"
)

# Check if Azure PowerShell module is installed
if (-not (Get-Module -ListAvailable -Name Az.KeyVault -ErrorAction SilentlyContinue)) {
    Write-Error "Az.KeyVault module not installed. Install with: Install-Module -Name Az -AllowClobber"
    exit 1
}

# Check if authenticated in Azure
try {
    $context = Get-AzContext -ErrorAction Stop
    if (-not $context) {
        Write-Error "Not authenticated in Azure. Run: Connect-AzAccount"
        exit 1
    }
    Write-Host "Authenticated in Azure as: $($context.Account)" -ForegroundColor Green
} catch {
    Write-Error "Error checking Azure authentication: $_"
    Write-Host "Run: Connect-AzAccount"
    exit 1
}

# Check if Key Vault exists
Write-Host "Checking Key Vault: $VaultName" -ForegroundColor Yellow
try {
    $vault = Get-AzKeyVault -VaultName $VaultName -ErrorAction Stop
    Write-Host "Key Vault found: $($vault.VaultName) in $($vault.Location)" -ForegroundColor Green
} catch {
    Write-Error "Key Vault '$VaultName' not found or you do not have access."
    exit 1
}

# Create or update the secret
Write-Host "Creating/Updating secret: $SecretName" -ForegroundColor Yellow
try {
    $secretValueSecure = ConvertTo-SecureString -String $SecretValue -AsPlainText -Force
    Set-AzKeyVaultSecret -VaultName $VaultName -Name $SecretName -SecretValue $secretValueSecure -ContentType $ContentType -ErrorAction Stop
    Write-Host "Secret '$SecretName' created/updated successfully!" -ForegroundColor Green
} catch {
    Write-Error "Error creating secret: $_"
    exit 1
}

# List secrets in Key Vault (optional, for verification)
Write-Host ""
Write-Host "Current secrets in Key Vault:" -ForegroundColor Yellow
Get-AzKeyVaultSecret -VaultName $VaultName | Select-Object Name, ContentType, @{Name="LastUpdated"; Expression={$_.Updated}}
