# Manual de Replicação - DataMasterV2

Este documento registra todos os comandos e decisões usados para criar o projeto DataMasterV2 do zero.

## 1. Pré-requisitos verificados

```powershell
git --version
az --version
gh --version
databricks --version
terraform version
python --version
node --version
npm --version
func --version
make --version
```

## 2. Informações do ambiente

- Tenant ID: `1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d`
- Subscription ID: `97eb265c-59ce-4122-bbe4-98f0d58d9208`
- Região: `brazilsouth`
- Projeto: `DataMasterV2`
- Repositório: `ThallysonDinizdebrito/DataMasterV2`
- Branch de deploy: `dev`

## 3. Bootstrap local

```powershell
New-Item -ItemType Directory -Force -Path C:\Users\Thall\infra\DataMasterV2
```

Diretórios principais criados:

```text
infra/
azure_function/
masterdatabricks/
grafana/
.github/workflows/
scripts/
docs/
```

## 4. Repositório Git

```powershell
git init
git checkout -b dev
```

## 5. Repositório GitHub

```powershell
gh repo create ThallysonDinizdebrito/DataMasterV2 --public --source . --remote origin --description "Professional Azure Databricks data engineering project with Terraform, Azure Functions, DLT, CI/CD and observability"
git add .
git commit -m "bootstrap DataMasterV2 project structure"
git push -u origin dev
```

## 6. Backend remoto do Terraform

```powershell
az group create --name rg-datamasterv2-tfstate-dev --location brazilsouth

az storage account create `
  --name stdmv2tfstatedev `
  --resource-group rg-datamasterv2-tfstate-dev `
  --location brazilsouth `
  --sku Standard_LRS `
  --kind StorageV2 `
  --min-tls-version TLS1_2 `
  --allow-blob-public-access false

$key = az storage account keys list `
  --resource-group rg-datamasterv2-tfstate-dev `
  --account-name stdmv2tfstatedev `
  --query '[0].value' `
  -o tsv

az storage container create `
  --name tfstate `
  --account-name stdmv2tfstatedev `
  --account-key $key
```

## 7. Service Principal e GitHub Secrets

```powershell
$subscriptionId = "97eb265c-59ce-4122-bbe4-98f0d58d9208"
$tenantId = "1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d"
$spName = "sp-datamasterv2-dev"
$scope = "/subscriptions/$subscriptionId"

$spJson = az ad sp create-for-rbac `
  --name $spName `
  --role Contributor `
  --scopes $scope `
  --query "{clientId:appId, clientSecret:password, tenant:tenant}" `
  -o json | ConvertFrom-Json

az role assignment create `
  --assignee $spJson.clientId `
  --role "User Access Administrator" `
  --scope $scope

$spJson.clientId | gh secret set AZURE_CLIENT_ID --repo ThallysonDinizdebrito/DataMasterV2
$spJson.clientSecret | gh secret set AZURE_CLIENT_SECRET --repo ThallysonDinizdebrito/DataMasterV2
$tenantId | gh secret set AZURE_TENANT_ID --repo ThallysonDinizdebrito/DataMasterV2
$subscriptionId | gh secret set AZURE_SUBSCRIPTION_ID --repo ThallysonDinizdebrito/DataMasterV2
```

## 8. Terraform init e validação

```powershell
Copy-Item infra\dev.tfvars.example infra\dev.tfvars -Force
terraform -chdir=infra init
terraform -chdir=infra validate
```

Para execução local no Windows, foi usado `dev.auto.tfvars` para evitar problema de parsing com `-var-file`:

```powershell
Copy-Item dev.tfvars dev.auto.tfvars -Force
terraform plan
```

Resultado esperado do primeiro plan:

```text
Plan: 25 to add, 0 to change, 0 to destroy.
```

## 9. Ajuste arquitetural com Event Hub Capture

A arquitetura da ingestão foi ajustada para o fluxo profissional:

```text
Azure Function Timer
  -> Event Hub delivery-events
  -> Event Hub Capture
  -> ADLS Gen2 container source
  -> Databricks DLT Bronze/Silver/Gold
```

Recursos adicionados no Terraform:

```text
azurerm_eventhub_namespace.main
azurerm_eventhub.delivery_events
azurerm_monitor_diagnostic_setting.eventhub_namespace
```

O Capture foi configurado para gravar arquivos Avro no container `source`:

```text
source/eventhub-capture/{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}
```

Validação:

```powershell
az eventhubs eventhub show `
  --resource-group rg-dmv2-dev `
  --namespace-name evhns-dmv2-dev-vxc02 `
  --name delivery-events `
  --query "{name:name,partitionCount:partitionCount,messageRetentionInDays:messageRetentionInDays,capture:captureDescription.enabled}" `
  -o json
```

Resultado:

```json
{
  "capture": true,
  "messageRetentionInDays": 1,
  "name": "delivery-events",
  "partitionCount": 2
}
```

## 10. Terraform apply da infraestrutura base

Primeira tentativa:

```powershell
terraform apply -auto-approve
```

A maior parte da infraestrutura foi criada, mas ocorreram dois ajustes:

```text
1. Azure Function/App Service Plan falhou por quota da subscription:
   Current Limit (Total VMs): 0
   Amount required: 1

2. Grafana com SKU Essential falhou:
   Supported sku values are: Standard
```

Correções aplicadas:

```text
enable_function_app = false
Grafana SKU = Standard
```

Com isso, a Function App ficou preparada no Terraform, mas desligada até a quota ser liberada.

Segunda execução:

```powershell
terraform apply -auto-approve
```

Resultado:

```text
Apply complete.
```

Outputs principais:

```text
resource_group_name       = rg-dmv2-dev
storage_account_name      = stdmv2devvxc02
source_container_name     = source
rejected_container_name   = rejeitados
eventhub_namespace_name   = evhns-dmv2-dev-vxc02
eventhub_name             = delivery-events
databricks_workspace_name = dbw-dmv2-dev
databricks_workspace_url  = adb-7405606740420312.12.azuredatabricks.net
grafana_name              = grafana-dmv2-dev
grafana_endpoint          = https://grafana-dmv2-dev-dwcaceg3ceg2c3bm.sbr.grafana.azure.com
key_vault_name            = kv-dmv2dev-vxc02
```

## 11. Azure Function em West Europe

A Azure Function foi ativada em `westeurope` para contornar a quota zero de App Service em `brazilsouth`, mantendo o restante da arquitetura em Brazil South.

Configuração usada no `dev.auto.tfvars` local:

```hcl
enable_function_app = true
function_location   = "westeurope"
```

Recursos criados:

```text
asp-dmv2-dev-function
func-dmv2-dev-generator
```

Validação:

```powershell
az functionapp show `
  --name func-dmv2-dev-generator `
  --resource-group rg-dmv2-dev `
  --query "{name:name,location:location,state:state,hostNames:defaultHostName,kind:kind}" `
  -o json
```

Resultado:

```json
{
  "hostNames": "func-dmv2-dev-generator.azurewebsites.net",
  "kind": "functionapp,linux",
  "location": "West Europe",
  "name": "func-dmv2-dev-generator",
  "state": "Running"
}
```

O `terraform plan` final retornou:

```text
No changes. Your infrastructure matches the configuration.
```
