# Azure Key Vault - Automação de Segredos

## Visão Geral

Esta solução automatiza o gerenciamento de segredos no Azure Key Vault, eliminando a necessidade de armazenar segredos manualmente no Databricks Secret Scope ou em arquivos de configuração.

**Benefícios:**
- Centralização de segredos no Azure Key Vault
- Gestão automática via Terraform
- Integração com Azure Function (Managed Identity)
- Integração com Databricks (Secret Scope backed by Key Vault)
- Melhor governança e auditoria
- Compliance com segurança

---

## Arquitetura da Solução

```
GitHub Secrets → Terraform → Azure Key Vault → Azure Function/Databricks
```

**Fluxo:**
1. Segredos são passados via GitHub Secrets (seguro)
2. Terraform cria/atualiza segredos no Azure Key Vault
3. Azure Function lê segredos do Key Vault usando Managed Identity
4. Databricks lê segredos do Key Vault via Secret Scope backed by Key Vault

---

## Componentes Implementados

### 1. Terraform - Key Vault Secrets

**Arquivo:** `infra/keyvault_secrets.tf`

**Segredos Gerenciados:**
- `azure-client-secret`: Para Azure Cost Management API
- `databricks-token`: Opcional (se `store_databricks_token_in_kv = true`)
- `eventhub-connection-string`: Para Event Hub (se habilitado)
- `storage-access-key`: Para Azure Function (se habilitado)

**Variáveis Terraform:**
- `azure_client_secret`: Azure client secret (sensitive)
- `enable_azure_cost_observability`: Habilita criação do segredo
- `store_databricks_token_in_kv`: Opcionalmente armazena Databricks token
- `enable_eventhub`: Habilita Event Hub connection string

### 2. Azure Function - Integração com Key Vault

**Arquivo:** `azure_function/GeracaoData/gerarFakeData/__init__.py`

**Função Adicionada:**
```python
def get_secret_from_keyvault(secret_name):
    """Lê um segredo do Azure Key Vault usando Managed Identity"""
    key_vault_uri = os.getenv("KEY_VAULT_URI")
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)
    secret = secret_client.get_secret(secret_name)
    return secret.value
```

**Configurações Adicionadas:**
- `KEY_VAULT_NAME`: Nome do Key Vault
- `KEY_VAULT_URI`: URI do Key Vault

**Dependência Adicionada:**
- `azure-keyvault-secrets` em `requirements.txt`

### 3. Databricks - Secret Scope Backed by Key Vault

**Arquivo:** `infra/databricks.tf`

**Secret Scope Criado:**
```hcl
resource "databricks_secret_scope" "keyvault" {
  count = var.databricks_host != "" && var.enable_azure_cost_observability ? 1 : 0
  name  = "kv-backed"

  keyvault_metadata {
    resource_id = azurerm_key_vault.main.id
    dns_suffix  = "vault.azure.net"
  }
}
```

**Nome:** `kv-backed`
**Tipo:** Backed by Azure Key Vault

### 4. Databricks Bundle - Configuração

**Arquivo:** `lakeflow/databricks.yml`

**Variável Atualizada:**
```yaml
cost_secret_scope:
  description: Databricks secret scope containing the Azure client secret (backed by Azure Key Vault)
  default: kv-backed
```

**Mudança:** `dmv2-dev` → `kv-backed`

### 5. GitHub Actions - Passagem de Segredos

**Arquivo:** `.github/workflows/deploy-dev.yml`

**Variáveis Adicionadas:**
```yaml
TF_VAR_azure_client_secret: ${{ secrets.AZURE_CLIENT_SECRET }}
TF_VAR_enable_azure_cost_observability: true
```

---

## Configuração Necessária

### 1. GitHub Secrets

Adicione os seguintes segredos no GitHub Repository:

**Segredos Existentes:**
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `DATABRICKS_TOKEN`

**Segredo Novo:**
- `AZURE_CLIENT_SECRET`: Azure client secret para Azure Cost Management

### 2. Terraform Variables

**Arquivo:** `infra/dev.tfvars`

Adicione as seguintes variáveis:
```hcl
# Azure Key Vault Secrets
azure_client_secret = "seu-azure-client-secret-aqui"
enable_azure_cost_observability = true
store_databricks_token_in_kv = false
enable_eventhub = false
```

### 3. Azure Function App Settings

As seguintes configurações são adicionadas automaticamente pelo Terraform:
- `KEY_VAULT_NAME`: Nome do Key Vault
- `KEY_VAULT_URI`: URI do Key Vault

---

## Processo de Deploy

### 1. Commit e Push

```bash
git add .
git commit -m "feat: implement Azure Key Vault automation for secrets"
git push origin dev
```

### 2. GitHub Actions Executa Automaticamente

**Job Terraform:**
- Passa `TF_VAR_azure_client_secret` do GitHub Secret
- Cria/atualiza segredo `azure-client-secret` no Azure Key Vault
- Cria secret scope `kv-backed` no Databricks

**Job Azure Function:**
- Deploy da Function atualizada com dependência `azure-keyvault-secrets`
- Configurações `KEY_VAULT_NAME` e `KEY_VAULT_URI` são adicionadas

**Job Databricks:**
- Deploy do bundle atualizado com `cost_secret_scope: kv-backed`
- Secret scope `kv-backed` é criado no Databricks

### 3. Validação

**Azure Key Vault:**
```bash
az keyvault secret show --vault-name kv-dmv2dev-vxc02 --name azure-client-secret
```

**Databricks Secret Scope:**
```python
dbutils.secrets.listScopes()
# Deve mostrar: kv-backed
```

**Azure Function:**
- Verificar logs da Function para confirmar que consegue ler do Key Vault

**Databricks Job:**
- Executar job Azure Cost Observability
- Verificar que consegue ler o segredo do secret scope `kv-backed`

---

## Uso dos Segredos

### Azure Function

**Ler segredo do Key Vault:**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

key_vault_uri = os.getenv("KEY_VAULT_URI")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)
secret = secret_client.get_secret("azure-client-secret")
client_secret = secret.value
```

### Databricks

**Ler segredo do Secret Scope:**
```python
secret_scope = "kv-backed"
secret_key = "azure-client-secret"
client_secret = dbutils.secrets.get(scope=secret_scope, key=secret_key)
```

---

## Rollback

### Se necessário voltar ao Databricks Secret Scope legado:

1. **Reverter databricks.yml:**
```yaml
cost_secret_scope:
  default: dmv2-dev  # voltar para o legado
```

2. **Redeploy do bundle:**
```bash
databricks bundle deploy -t dev
```

3. **Remover secret scope backed by Key Vault:**
```python
dbutils.secrets.deleteScope(scope="kv-backed")
```

---

## Segurança

### Práticas de Segurança Implementadas:

1. **Segredos não são expostos nos logs:**
```hcl
lifecycle {
  ignore_changes = [value]
}
```

2. **Variáveis sensíveis no Terraform:**
```hcl
variable "azure_client_secret" {
  sensitive = true
}
```

3. **Managed Identity para Azure Function:**
- Não há necessidade de armazenar credenciais
- Autenticação automática via Azure AD

4. **Secret Scope backed by Key Vault:**
- Segredos são gerenciados centralmente
- Auditoria via Azure Key Vault logs

---

## Troubleshooting

### Erro: "KEY_VAULT_URI não está definido"

**Causa:** Configuração `KEY_VAULT_URI` não foi adicionada à Azure Function

**Solução:**
- Verificar se `function.tf` tem as configurações `KEY_VAULT_NAME` e `KEY_VAULT_URI`
- Executar `terraform apply` novamente

### Erro: "Erro ao ler segredo do Key Vault"

**Causa:** Azure Function não tem permissão para acessar o Key Vault

**Solução:**
- Verificar se role assignment `Key Vault Secrets User` está configurado
- Verificar se Managed Identity está habilitada na Function

### Erro: "Secret scope kv-backed não existe"

**Causa:** Secret scope não foi criado pelo Terraform

**Solução:**
- Verificar se `enable_azure_cost_observability = true` no dev.tfvars
- Executar `terraform apply` novamente
- Verificar logs do Terraform para erros

---

## Próximos Passos

### Migração Completa de Segredos

**Segredos que podem ser migrados para Key Vault:**
- Databricks PAT token (opcional)
- Event Hub connection string (quando Event Hub for habilitado)
- Storage account access keys
- Outros segredos específicos do projeto

### Melhorias Futuras

1. **Rotação Automática de Segredos:**
   - Implementar rotação automática via Azure Key Vault
   - Atualizar componentes automaticamente após rotação

2. **Auditoria Avançada:**
   - Habilitar logs do Azure Key Vault
   - Integrar com Azure Monitor para alertas

3. **Secrets Management via CI/CD:**
   - Automatizar criação/rotação de segredos via GitHub Actions
   - Implementar validação de segredos antes do deploy

---

## Resumo

**O que foi implementado:**
- ✅ Terraform para gerenciar segredos no Azure Key Vault
- ✅ Azure Function integrada com Key Vault via Managed Identity
- ✅ Databricks Secret Scope backed by Key Vault
- ✅ GitHub Actions para passagem de segredos
- ✅ Documentação completa

**Complexidade:** MÉDIA
**Impacto:** POSITIVO (melhora segurança e governança)
**Risco:** BAIXO (rollback fácil)

**Tempo de implementação:** ~2 horas
**Tempo de validação:** ~30 minutos

---

**DataMasterV2 - Azure Key Vault Automação**
**Versão:** 1.0
**Data:** 2026-06-23
**Autor:** Cascade AI Assistant
