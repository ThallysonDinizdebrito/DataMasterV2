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

## 12. Código Python da Azure Function

O código da Function foi criado em:

```text
azure_function/GeracaoData
```

Arquivos principais:

```text
host.json
requirements.txt
gerarFakeData/function.json
gerarFakeData/__init__.py
```

A Function replica a lógica do gerador de dados fake do projeto anterior, gerando:

```text
clientes
restaurantes
items
drivers
orders
```

No DataMasterV2, o envio foi adaptado para Event Hub usando Managed Identity:

```text
Azure Function Timer
  -> Event Hub delivery-events
  -> Event Hub Capture
  -> ADLS Gen2 source/eventhub-capture
```

Dependências:

```text
azure-functions
azure-eventhub
azure-identity
faker
```

Deploy usando Azure Functions Core Tools:

```powershell
func --version

func azure functionapp publish func-dmv2-dev-generator --build remote --python
```

Validação da função publicada:

```powershell
az functionapp function list `
  --resource-group rg-dmv2-dev `
  --name func-dmv2-dev-generator `
  --query "[].{name:name,trigger:config.bindings[0].type}" `
  -o table
```

Resultado:

```text
Name                                   Trigger
-------------------------------------  ------------
func-dmv2-dev-generator/gerarFakeData  timerTrigger
```

## 13. Pipeline GitHub Actions para recriação completa

A pipeline de desenvolvimento foi criada em:

```text
.github/workflows/deploy-dev.yml
```

Ela executa automaticamente em:

```text
push na branch dev
workflow_dispatch manual
```

Fluxo automatizado:

```text
Checkout
Azure Login
Bootstrap do backend remoto Terraform
Terraform Init
Terraform Format Check
Terraform Validate
Terraform Apply
Instala Azure Functions Core Tools
Valida sintaxe Python
Publica Azure Function via func CLI
Reinicia Function App
Valida trigger publicado
```

Assim, se a infraestrutura do projeto for destruída, um novo push na branch `dev` pode recriar o backend remoto do Terraform, recriar os recursos e publicar novamente o pacote Python da Azure Function.

Backend remoto criado automaticamente se não existir:

```text
Resource Group: rg-datamasterv2-tfstate-dev
Storage Account: stdmv2tfstatedev
Container: tfstate
State key: datamasterv2-dev.tfstate
```

Publicação da Function na pipeline:

```powershell
func azure functionapp publish func-dmv2-dev-generator --build remote --python
```

Secrets necessários no GitHub:

```text
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
```

Agora não precisa mais criar o state remoto na mão, desde que os GitHub Secrets existam e o Service Principal tenha permissão para criar Resource Group, Storage Account e Container.

Status: automação de recriação completa adicionada e validada.

## 14. Passo 2 - Pipeline Databricks Lakeflow/DLT

Com a Azure Function pausada para controle de volume, o próximo componente criado é o pipeline Databricks para processar os arquivos AVRO já gerados pelo Event Hub Capture.

Estrutura criada:

```text
lakeflow/
  databricks.yml
  README.md
  bronze/bronze_eventhub_capture.py
  silver/silver_delivery_entities.py
  gold/gold_delivery_metrics.py
```

Fonte dos dados:

```text
abfss://source@stdmv2devvxc02.dfs.core.windows.net/eventhub-capture
```

Fluxo medallion:

```text
Event Hub Capture AVRO
  -> Bronze raw
  -> Bronze batches parseados
  -> Silver entidades delivery
  -> Gold métricas de negócio
```

Tabelas planejadas:

```text
bronze_eventhub_capture_raw
bronze_delivery_batches
silver_clientes
silver_restaurantes
silver_drivers
silver_items
silver_orders
silver_order_items
gold_daily_delivery_kpis
gold_restaurant_performance
gold_item_category_metrics
```

Deploy do bundle:

```powershell
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

A pipeline GitHub Actions também recebeu um job `databricks` para validar e publicar o bundle automaticamente após o Terraform.

Configuração inicial do bundle:

```text
Workspace: adb-7405606740420312.12.azuredatabricks.net
Target schema: default
Unity Catalog: não obrigatório nesta primeira versão, pois enable_unity_catalog está desabilitado no Terraform.
```

Pré-requisito importante:

```text
O Service Principal usado nos GitHub Secrets precisa ter acesso ao Databricks Workspace e permissão para criar/atualizar pipelines Lakeflow/DLT.
```
