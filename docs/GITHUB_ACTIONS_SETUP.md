# Setup do GitHub Actions para Deploy do DataMasterV2

Este documento descreve tudo que precisa estar configurado para executar o workflow `Deploy Dev` e realizar o deploy automatizado do projeto.

O workflow faz:

```text
1. Prepara o backend remoto do Terraform.
2. Executa Terraform para criar/atualizar a infraestrutura Azure.
3. Publica a Azure Function.
4. Faz deploy do Databricks Bundle.
5. Usa Unity Catalog External Location para acesso ao ADLS.
6. Inicia a pipeline DLT/Lakeflow no Databricks.
```

## 1. Pré-requisitos no computador

Instalar os CLIs necessários:

```text
Git
GitHub CLI
Azure CLI
Databricks CLI
Terraform
```

### 1.1. Validar instalações

No PowerShell:

```powershell
git --version
gh --version
az --version
databricks --version
terraform version
```

Se algum comando não existir, instale o CLI correspondente antes de continuar.

## 2. Autenticar no GitHub CLI

Entrar no GitHub pelo PowerShell:

```powershell
gh auth login
```

Selecione:

```text
GitHub.com
HTTPS
Login with a web browser
```

Validar autenticação:

```powershell
gh auth status
```

Repositório usado pelo projeto:

```text
ThallysonDinizdebrito/DataMasterV2
```

## 3. Autenticar no Azure CLI

Entrar no Azure:

```powershell
az login
```

Se o login interativo falhar por MFA ou política de autenticação, usar device code:

```powershell
az login --tenant 1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d --use-device-code
```

Selecionar a subscription correta, se necessário:

```powershell
az account set --subscription "<SUBSCRIPTION_ID>"
```

Validar conta ativa:

```powershell
az account show -o table
```

## 4. Configurar Service Principal com GitHub OIDC

O GitHub Actions usa um Service Principal para autenticar no Azure via OIDC, sem `AZURE_CLIENT_SECRET`.

### 4.1. Criar ou recuperar Service Principal

Substitua `<SUBSCRIPTION_ID>` pela subscription correta:

```powershell
az ad sp create-for-rbac `
  --name "sp-datamasterv2-github-actions-dev" `
  --role Contributor `
  --scopes "/subscriptions/<SUBSCRIPTION_ID>"
```

Recuperar dados do App Registration/Service Principal:

```powershell
az ad app list --display-name "sp-datamasterv2-github-actions-dev" --query "[].{name:displayName, clientId:appId, objectId:id}" -o table
```

### 4.2. Criar Federated Credential para GitHub Actions

O projeto possui um script de bootstrap:

```text
scripts/setup-github-oidc.ps1
```

Antes de rodar, valide que o Azure CLI está logado como usuário, não como Service Principal:

```powershell
az account show
```

Resultado esperado:

```text
user.type = user
```

Se aparecer `servicePrincipal`, faça:

```powershell
az logout
az login --tenant 1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d --use-device-code
```

Rodar o bootstrap OIDC:

```powershell
.\scripts\setup-github-oidc.ps1 `
  -AzureClientId "<AZURE_CLIENT_ID>" `
  -AzureTenantId "1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d" `
  -AzureSubscriptionId "97eb265c-59ce-4122-bbe4-98f0d58d9208" `
  -GitHubOrg "ThallysonDinizdebrito" `
  -GitHubRepo "DataMasterV2" `
  -EntityType Environment `
  -EnvironmentName "dev" `
  -CredentialName "github-actions-dev-environment-oidc"
```

Subject esperado no Entra ID:

```text
repo:ThallysonDinizdebrito/DataMasterV2:environment:dev
```

### 4.3. Secrets/identificadores Azure no GitHub

O projeto não usa mais `AZURE_CLIENT_SECRET`.

O workflow ainda precisa dos identificadores:

```text
AZURE_CLIENT_ID
AZURE_SUBSCRIPTION_ID
AZURE_TENANT_ID
```

Esses valores são identificadores, não senha.

## 5. Configurar Databricks CLI local

Workspace Databricks do projeto:

```text
https://adb-7405608830882565.5.azuredatabricks.net/
```

Autenticar localmente:

```powershell
databricks auth login `
  --host https://adb-7405608830882565.5.azuredatabricks.net/ `
  --profile dbw-dmv2-dev
```

Validar usuário:

```powershell
databricks current-user me --profile dbw-dmv2-dev
```

Validar profiles:

```powershell
databricks auth profiles
```

Resultado esperado:

```text
dbw-dmv2-dev  https://adb-7405608830882565.5.azuredatabricks.net  YES
```

## 6. Criar token Databricks para GitHub Actions

Criar PAT no Databricks pelo PowerShell:

```powershell
databricks tokens create --comment "github-actions-cicd" --lifetime-seconds 7776000 --profile dbw-dmv2-dev
```

O retorno contém `token_value`.

O `token_value` aparece apenas uma vez.

Cadastrar no GitHub Secret:

```powershell
gh secret set DATABRICKS_TOKEN --body "<TOKEN_VALUE>" --repo ThallysonDinizdebrito/DataMasterV2
```

## 7. Acesso ao ADLS via Unity Catalog External Location

O projeto não usa mais Storage Account Key no Databricks Bundle.

O acesso ao ADLS ocorre por:

```text
Unity Catalog
External Location: extloc_dmv2_source_lab
Storage Credential: cred_dmv2_source_lab
Access Connector: unity-catalog-access-connector
Storage Account: stdmv2devvxc02
```

Não cadastrar `STORAGE_ACCOUNT_KEY` para o bundle.

## 8. Validar todos os GitHub Secrets obrigatórios

Listar secrets:

```powershell
gh secret list --repo ThallysonDinizdebrito/DataMasterV2
```

Resultado esperado:

```text
AZURE_CLIENT_ID
AZURE_SUBSCRIPTION_ID
AZURE_TENANT_ID
DATABRICKS_TOKEN
```

## 9. Configurar permissões para observabilidade de custos Azure

O projeto possui um job Databricks para consultar a Azure Cost Management API e gravar tabelas de custo no Unity Catalog.

Job no bundle:

```text
azure_cost_observability
```

Tabelas geradas:

```text
delivery_datamaster.observability.azure_cost_by_resource_daily
delivery_datamaster.observability.azure_cost_summary_daily
```

Para esse job funcionar, o Service Principal precisa ter permissão para ler custos da subscription.

Service Principal usado:

```text
Application/Client ID: 7da295f3-e9d6-4a72-9f47-8e3bde7fcc92
Subscription ID:       97eb265c-59ce-4122-bbe4-98f0d58d9208
```

Role aplicada:

```text
Cost Management Reader
```

Comando usado:

```powershell
az role assignment create `
  --assignee 7da295f3-e9d6-4a72-9f47-8e3bde7fcc92 `
  --role "Cost Management Reader" `
  --scope "/subscriptions/97eb265c-59ce-4122-bbe4-98f0d58d9208"
```

Validar a role:

```powershell
az role assignment list `
  --assignee 7da295f3-e9d6-4a72-9f47-8e3bde7fcc92 `
  --scope "/subscriptions/97eb265c-59ce-4122-bbe4-98f0d58d9208" `
  -o table
```

Se a API retornar `403`, aguardar alguns minutos para propagação da role.

## 10. Configurar secret Databricks para chamada da Azure Cost Management API

O job `azure_cost_observability` usa client credentials para gerar token contra o Azure Resource Manager.

O client secret não fica no GitHub nem no código. Ele precisa estar em um Databricks Secret Scope.

Secret scope esperado:

```text
dmv2-dev
```

Secret key esperada:

```text
azure-client-secret
```

Criar o scope, se ainda não existir:

```powershell
databricks secrets create-scope dmv2-dev --profile dbw-dmv2-dev
```

Se retornar `Scope dmv2-dev already exists!`, seguir para a criação da secret.

Criar ou atualizar a secret:

```powershell
databricks secrets put-secret dmv2-dev azure-client-secret --profile dbw-dmv2-dev
```

Quando o editor abrir, informar o valor do `AZURE_CLIENT_SECRET` do Service Principal.

Validar scopes e secrets:

```powershell
databricks secrets list-scopes --profile dbw-dmv2-dev
databricks secrets list-secrets dmv2-dev --profile dbw-dmv2-dev
```

Resultado esperado:

```text
Scope        Backend Type
dmv2-dev     DATABRICKS

Key                  Last Updated Timestamp
azure-client-secret  <timestamp>
```

O Databricks não exibe o valor da secret, apenas o nome da key.

## 11. Conferir arquivos obrigatórios do projeto

Workflow GitHub Actions:

```text
.github/workflows/deploy-dev.yml
```

Bundle Databricks:

```text
lakeflow/databricks.yml
```

O job Databricks do workflow precisa ter:

```yaml
env:
  DATABRICKS_HOST: https://adb-7405608830882565.5.azuredatabricks.net/
  DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

E os comandos precisam rodar em:

```yaml
working-directory: lakeflow
```

Comandos esperados:

```bash
databricks current-user me
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle summary -t dev
databricks bundle run delivery_eventhub_medallion_v2 -t dev
```

## 12. Commitar e enviar alterações para a branch dev

Na raiz do projeto:

```powershell
Set-Location C:\Users\Thall\infra\DataMasterV2
git status
git add .github/workflows/deploy-dev.yml lakeflow/databricks.yml docs/REPLICACAO.md docs/GITHUB_ACTIONS_SETUP.md scripts/setup-github-oidc.ps1
git commit -m "Document GitHub Actions deployment setup"
git push origin dev
```

Se não houver alterações para commit, o Git informará que não há nada para commitar.

## 13. Executar o workflow Deploy Dev

Pelo terminal:

```powershell
gh workflow run "Deploy Dev" --repo ThallysonDinizdebrito/DataMasterV2 --ref dev
```

Pelo GitHub:

```text
GitHub > DataMasterV2 > Actions > Deploy Dev > Run workflow > branch dev
```

## 14. Acompanhar execução da Action

Listar execuções recentes:

```powershell
gh run list --repo ThallysonDinizdebrito/DataMasterV2 --workflow "Deploy Dev" --limit 5
```

Ver detalhes do último run:

```powershell
gh run view --repo ThallysonDinizdebrito/DataMasterV2 --log
```

## 15. Validar pipeline DLT no Databricks

O workflow deve fazer deploy e iniciar a pipeline:

```text
dlt-dmv2-delivery-eventhub-dev
```

No Databricks UX, validar se o novo update ficou como:

```text
COMPLETED
```

Também é possível validar pelo CLI se tiver o `pipeline_id` e `update_id`:

```powershell
databricks pipelines get-update <PIPELINE_ID> <UPDATE_ID> --profile dbw-dmv2-dev
```

## 16. Validar tabelas no Databricks SQL

Executar:

```sql
SELECT COUNT(*) FROM dbw_dmv2_dev_7405608830882565.default.bronze_eventhub_capture_raw;
SELECT COUNT(*) FROM dbw_dmv2_dev_7405608830882565.default.bronze_delivery_batches;
SELECT COUNT(*) FROM dbw_dmv2_dev_7405608830882565.default.silver_orders;
SELECT COUNT(*) FROM dbw_dmv2_dev_7405608830882565.default.gold_daily_delivery_kpis;
```

## 17. Executar job de observabilidade de custos

O job de custos fica com schedule pausado para evitar execução automática e custo inesperado.

Executar manualmente:

```powershell
databricks bundle run azure_cost_observability -t dev --profile dbw-dmv2-dev
```

Depois validar as tabelas:

```sql
SELECT * FROM delivery_datamaster.observability.azure_cost_by_resource_daily LIMIT 100;
SELECT * FROM delivery_datamaster.observability.azure_cost_summary_daily ORDER BY usage_date DESC;
```

Essas tabelas são a base para dashboard de FinOps com:

```text
custo diário
custo por resource group
custo por serviço Azure
custo por tipo de recurso
ranking de recursos mais caros
```

## 18. Troubleshooting rápido

### Erro: `DATABRICKS_TOKEN` inválido

Recriar token:

```powershell
databricks tokens create --comment "github-actions-cicd" --lifetime-seconds 7776000 --profile dbw-dmv2-dev
gh secret set DATABRICKS_TOKEN --body "<TOKEN_VALUE>" --repo ThallysonDinizdebrito/DataMasterV2
```

### Erro: `AADSTS700213 No matching federated identity record found`

O subject da Federated Credential não bate com o token emitido pelo GitHub Actions.

Para workflow com `environment: dev`, a Federated Credential deve ter:

```text
repo:ThallysonDinizdebrito/DataMasterV2:environment:dev
```

Recriar via script:

```powershell
.\scripts\setup-github-oidc.ps1 `
  -AzureClientId "<AZURE_CLIENT_ID>" `
  -AzureTenantId "1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d" `
  -AzureSubscriptionId "97eb265c-59ce-4122-bbe4-98f0d58d9208" `
  -GitHubOrg "ThallysonDinizdebrito" `
  -GitHubRepo "DataMasterV2" `
  -EntityType Environment `
  -EnvironmentName "dev" `
  -CredentialName "github-actions-dev-environment-oidc"
```

### Erro: `databricks.yml not found`

O comando Databricks Bundle precisa rodar dentro de:

```text
lakeflow
```

No workflow, usar:

```yaml
working-directory: lakeflow
```

### Erro: pipeline já está rodando

Aguardar o update atual terminar antes de iniciar outro run.

## 19. Resumo dos comandos principais

```powershell
gh auth login
az login
az login --tenant 1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d --use-device-code
.\scripts\setup-github-oidc.ps1 `
  -AzureClientId "<AZURE_CLIENT_ID>" `
  -AzureTenantId "1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d" `
  -AzureSubscriptionId "97eb265c-59ce-4122-bbe4-98f0d58d9208" `
  -GitHubOrg "ThallysonDinizdebrito" `
  -GitHubRepo "DataMasterV2" `
  -EntityType Environment `
  -EnvironmentName "dev" `
  -CredentialName "github-actions-dev-environment-oidc"
gh secret list --repo ThallysonDinizdebrito/DataMasterV2
databricks tokens create --comment "github-actions-cicd" --lifetime-seconds 7776000 --profile dbw-dmv2-dev
gh secret set DATABRICKS_TOKEN --body "<TOKEN_VALUE>" --repo ThallysonDinizdebrito/DataMasterV2
gh workflow run "Deploy Dev" --repo ThallysonDinizdebrito/DataMasterV2 --ref dev
gh run list --repo ThallysonDinizdebrito/DataMasterV2 --workflow "Deploy Dev" --limit 5
```
