# Setup do GitHub Actions para Deploy do DataMasterV2

Este documento descreve tudo que precisa estar configurado para executar o workflow `Deploy Dev` e realizar o deploy automatizado do projeto.

O workflow faz:

```text
1. Prepara o backend remoto do Terraform.
2. Executa Terraform para criar/atualizar a infraestrutura Azure.
3. Publica a Azure Function.
4. Faz deploy do Databricks Bundle.
5. Injeta a Storage Account Key no Databricks Bundle.
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

Selecionar a subscription correta, se necessário:

```powershell
az account set --subscription "<SUBSCRIPTION_ID>"
```

Validar conta ativa:

```powershell
az account show -o table
```

## 4. Criar ou recuperar Service Principal do Azure

O GitHub Actions usa um Service Principal para autenticar no Azure.

### 4.1. Criar Service Principal

Substitua `<SUBSCRIPTION_ID>` pela subscription correta:

```powershell
az ad sp create-for-rbac `
  --name "sp-datamasterv2-github-actions-dev" `
  --role Contributor `
  --scopes "/subscriptions/<SUBSCRIPTION_ID>" `
  --sdk-auth
```

O retorno terá este formato:

```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "..."
}
```

Guarde esses valores para cadastrar no GitHub Secrets.

### 4.2. Cadastrar secrets Azure no GitHub

```powershell
gh secret set AZURE_CLIENT_ID --body "<clientId>" --repo ThallysonDinizdebrito/DataMasterV2
gh secret set AZURE_CLIENT_SECRET --body "<clientSecret>" --repo ThallysonDinizdebrito/DataMasterV2
gh secret set AZURE_SUBSCRIPTION_ID --body "<subscriptionId>" --repo ThallysonDinizdebrito/DataMasterV2
gh secret set AZURE_TENANT_ID --body "<tenantId>" --repo ThallysonDinizdebrito/DataMasterV2
```

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

## 7. Cadastrar Storage Account Key no GitHub Actions

Storage Account usado pela pipeline:

```text
stdmv2devvxc02
```

Resource Group:

```text
rg-dmv2-dev
```

Obter a key e cadastrar como secret:

```powershell
$key = (az storage account keys list --resource-group rg-dmv2-dev --account-name stdmv2devvxc02 --query "[0].value" -o tsv).Trim()
gh secret set STORAGE_ACCOUNT_KEY --body $key --repo ThallysonDinizdebrito/DataMasterV2
```

Esse secret é usado no workflow como:

```yaml
BUNDLE_VAR_storage_account_key: ${{ secrets.STORAGE_ACCOUNT_KEY }}
```

Essa variável preenche a variável do Databricks Bundle:

```yaml
storage_account_key
```

E alimenta a configuração Spark:

```yaml
spark.hadoop.fs.azure.account.key.stdmv2devvxc02.dfs.core.windows.net: ${var.storage_account_key}
```

## 8. Validar todos os GitHub Secrets obrigatórios

Listar secrets:

```powershell
gh secret list --repo ThallysonDinizdebrito/DataMasterV2
```

Resultado esperado:

```text
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
AZURE_SUBSCRIPTION_ID
AZURE_TENANT_ID
DATABRICKS_TOKEN
STORAGE_ACCOUNT_KEY
```

## 9. Conferir arquivos obrigatórios do projeto

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
  BUNDLE_VAR_storage_account_key: ${{ secrets.STORAGE_ACCOUNT_KEY }}
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

## 10. Commitar e enviar alterações para a branch dev

Na raiz do projeto:

```powershell
Set-Location C:\Users\Thall\infra\DataMasterV2
git status
git add .github/workflows/deploy-dev.yml lakeflow/databricks.yml docs/REPLICACAO.md docs/GITHUB_ACTIONS_SETUP.md
git commit -m "Document GitHub Actions deployment setup"
git push origin dev
```

Se não houver alterações para commit, o Git informará que não há nada para commitar.

## 11. Executar o workflow Deploy Dev

Pelo terminal:

```powershell
gh workflow run "Deploy Dev" --repo ThallysonDinizdebrito/DataMasterV2 --ref dev
```

Pelo GitHub:

```text
GitHub > DataMasterV2 > Actions > Deploy Dev > Run workflow > branch dev
```

## 12. Acompanhar execução da Action

Listar execuções recentes:

```powershell
gh run list --repo ThallysonDinizdebrito/DataMasterV2 --workflow "Deploy Dev" --limit 5
```

Ver detalhes do último run:

```powershell
gh run view --repo ThallysonDinizdebrito/DataMasterV2 --log
```

## 13. Validar pipeline DLT no Databricks

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

## 14. Validar tabelas no Databricks SQL

Executar:

```sql
SELECT COUNT(*) FROM dbw_dmv2_dev_7405608830882565.default.bronze_eventhub_capture_raw;
SELECT COUNT(*) FROM dbw_dmv2_dev_7405608830882565.default.bronze_delivery_batches;
SELECT COUNT(*) FROM dbw_dmv2_dev_7405608830882565.default.silver_orders;
SELECT COUNT(*) FROM dbw_dmv2_dev_7405608830882565.default.gold_daily_delivery_kpis;
```

## 15. Troubleshooting rápido

### Erro: `DATABRICKS_TOKEN` inválido

Recriar token:

```powershell
databricks tokens create --comment "github-actions-cicd" --lifetime-seconds 7776000 --profile dbw-dmv2-dev
gh secret set DATABRICKS_TOKEN --body "<TOKEN_VALUE>" --repo ThallysonDinizdebrito/DataMasterV2
```

### Erro: `Invalid configuration value detected for fs.azure.account.key`

Atualizar `STORAGE_ACCOUNT_KEY`:

```powershell
$key = (az storage account keys list --resource-group rg-dmv2-dev --account-name stdmv2devvxc02 --query "[0].value" -o tsv).Trim()
gh secret set STORAGE_ACCOUNT_KEY --body $key --repo ThallysonDinizdebrito/DataMasterV2
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

## 16. Resumo dos comandos principais

```powershell
gh auth login
az login
gh secret list --repo ThallysonDinizdebrito/DataMasterV2
$key = (az storage account keys list --resource-group rg-dmv2-dev --account-name stdmv2devvxc02 --query "[0].value" -o tsv).Trim()
gh secret set STORAGE_ACCOUNT_KEY --body $key --repo ThallysonDinizdebrito/DataMasterV2
databricks tokens create --comment "github-actions-cicd" --lifetime-seconds 7776000 --profile dbw-dmv2-dev
gh secret set DATABRICKS_TOKEN --body "<TOKEN_VALUE>" --repo ThallysonDinizdebrito/DataMasterV2
gh workflow run "Deploy Dev" --repo ThallysonDinizdebrito/DataMasterV2 --ref dev
gh run list --repo ThallysonDinizdebrito/DataMasterV2 --workflow "Deploy Dev" --limit 5
```
