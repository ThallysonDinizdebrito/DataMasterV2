param(
    [Parameter(Mandatory = $true)]
    [string]$DatabricksAccountId,

    [string]$AppName = "databricks-terraform-unity-catalog",

    [string[]]$Groups = @("data-engineers", "data-scientists", "data-analysts")
)

$ErrorActionPreference = "Stop"

Write-Host "Validating Azure CLI login..."
az account show | Out-Null

Write-Host "Creating App Registration '$AppName'..."
$App = az ad app create `
    --display-name $AppName `
    --web-redirect-uris "https://accounts.azuredatabricks.net" `
    --only-show-errors | ConvertFrom-Json

$ClientId = $App.appId
$AppObjectId = $App.id

Write-Host "App Registration created:"
Write-Host "  Application (client) ID: $ClientId"
Write-Host "  Object ID: $AppObjectId"

Write-Host "Creating client secret..."
$Secret = az ad app credential reset `
    --id $ClientId `
    --append `
    --only-show-errors | ConvertFrom-Json

$ClientSecret = $Secret.password
$SecretEndDate = $Secret.endDateTime

Write-Host "Client secret created (expires: $SecretEndDate)"
Write-Host "  WARNING: Save this secret securely, it won't be shown again!"

Write-Host "Creating service principal..."
$ServicePrincipal = az ad sp create `
    --id $ClientId `
    --only-show-errors | ConvertFrom-Json

Write-Host "Service principal created: $($ServicePrincipal.displayName)"

Write-Host "Creating Databricks account-level groups..."
foreach ($Group in $Groups) {
    Write-Host "  Creating group: $Group"
    
    # Note: Databricks CLI doesn't support account-level groups creation via CLI
    # Groups need to be created manually in Account Console or via API
    # This script will provide the instructions
    
    Write-Host "  To create group '$Group' manually:"
    Write-Host "    1. Access: https://accounts.azuredatabricks.net"
    Write-Host "    2. Go to User Management -> Groups"
    Write-Host "    3. Click Create Group"
    Write-Host "    4. Enter name: $Group"
    Write-Host "    5. Click Create"
}

Write-Host ""
Write-Host "Unity Catalog setup completed!"
Write-Host ""
Write-Host "Add these variables to your dev.tfvars:"
Write-Host "  client_id     = '$ClientId'"
Write-Host "  client_secret = '$ClientSecret'"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Create the groups manually in Databricks Account Console"
Write-Host "  2. Update dev.tfvars with the credentials above"
Write-Host "  3. Run Terraform to create account-level groups and grants"
