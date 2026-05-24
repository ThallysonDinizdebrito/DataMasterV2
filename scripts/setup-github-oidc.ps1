param(
    [Parameter(Mandatory = $true)]
    [string]$AzureClientId,

    [Parameter(Mandatory = $true)]
    [string]$AzureTenantId,

    [Parameter(Mandatory = $true)]
    [string]$AzureSubscriptionId,

    [Parameter(Mandatory = $true)]
    [string]$GitHubOrg,

    [Parameter(Mandatory = $true)]
    [string]$GitHubRepo,

    [string]$Branch = "dev",

    [string]$CredentialName = "github-actions-dev-oidc",

    [string]$RoleScope = ""
)

$ErrorActionPreference = "Stop"

Write-Host "Validating Azure CLI login..."
az account show | Out-Null

Write-Host "Validating GitHub CLI login..."
gh auth status | Out-Null

Write-Host "Selecting Azure subscription..."
az account set --subscription $AzureSubscriptionId

Write-Host "Resolving App Registration object ID..."
$AppObjectId = az ad app show `
    --id $AzureClientId `
    --query id `
    -o tsv

if (-not $AppObjectId) {
    throw "App Registration not found for AzureClientId '$AzureClientId'."
}

$Subject = "repo:$GitHubOrg/$GitHubRepo:ref:refs/heads/$Branch"

Write-Host "Checking existing federated credentials..."
$ExistingCredential = az ad app federated-credential list `
    --id $AppObjectId `
    --query "[?name=='$CredentialName'].name | [0]" `
    -o tsv

if ($ExistingCredential) {
    Write-Host "Federated credential '$CredentialName' already exists. Skipping creation."
}
else {
    Write-Host "Creating federated credential '$CredentialName'..."
    $Credential = @{
        name        = $CredentialName
        issuer      = "https://token.actions.githubusercontent.com"
        subject     = $Subject
        description = "GitHub Actions OIDC for $GitHubOrg/$GitHubRepo branch $Branch"
        audiences   = @("api://AzureADTokenExchange")
    } | ConvertTo-Json -Depth 10

    $Credential | az ad app federated-credential create `
        --id $AppObjectId `
        --parameters "@-" | Out-Null
}

if ($RoleScope) {
    Write-Host "Ensuring Contributor role assignment on scope '$RoleScope'..."
    az role assignment create `
        --assignee $AzureClientId `
        --role "Contributor" `
        --scope $RoleScope `
        --only-show-errors | Out-Null

    Write-Host "Ensuring User Access Administrator role assignment on scope '$RoleScope'..."
    az role assignment create `
        --assignee $AzureClientId `
        --role "User Access Administrator" `
        --scope $RoleScope `
        --only-show-errors | Out-Null
}
else {
    Write-Host "RoleScope not provided. Skipping Azure role assignments."
}

Write-Host "Setting required GitHub secrets..."
gh secret set AZURE_CLIENT_ID --body $AzureClientId --repo "$GitHubOrg/$GitHubRepo"
gh secret set AZURE_TENANT_ID --body $AzureTenantId --repo "$GitHubOrg/$GitHubRepo"
gh secret set AZURE_SUBSCRIPTION_ID --body $AzureSubscriptionId --repo "$GitHubOrg/$GitHubRepo"

Write-Host ""
Write-Host "GitHub OIDC bootstrap completed."
Write-Host "Federated subject: $Subject"
Write-Host "After validating the workflow, remove AZURE_CLIENT_SECRET from GitHub Secrets."
