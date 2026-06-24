# DataMasterV2 - Documentação Completa da Arquitetura

## Índice
1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Configuração Azure e Autenticação](#configuração-azure-e-autenticação)
3. [Infraestrutura Terraform](#infraestrutura-terraform)
4. [Databricks Workspace e Unity Catalog](#databricks-workspace-e-unity-catalog)
5. [Pipelines DLT e Lakeflow](#pipelines-dlt-e-lakeflow)
6. [Governança de Dados](#governança-de-dados)
7. [GitHub Actions e CI/CD](#github-actions-e-cicd)
8. [Observabilidade e Monitoramento](#observabilidade-e-monitoramento)
9. [Scripts de Automação](#scripts-de-automação)

---

## Visão Geral do Projeto

**DataMasterV2** é um projeto profissional de Engenharia de Dados que combina:
- **Azure**: Infraestrutura cloud (Resource Groups, Storage, Key Vault, Function App)
- **Databricks**: Workspace, Delta Live Tables (DLT), Unity Catalog
- **Lakeflow**: Pipelines de dados Bronze/Silver/Gold
- **Governança**: Tags, Views Mascaradas, Permissões Granulares
- **CI/CD**: GitHub Actions com Terraform e Databricks Bundle
- **Observabilidade**: Azure Monitor, Log Analytics, Application Insights

**Arquitetura Resumida:**
```
GitHub Actions → Terraform → Azure Resources → Databricks Workspace → DLT Pipelines → Unity Catalog → Governança
```

**Ambiente:**
- Ambiente: dev
- Região Azure: brazilsouth
- Subscription ID: 97eb265c-59ce-4122-bbe4-98f0d58d9208
- Tenant ID: 1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d
- Databricks Account ID: 953205e1-ba48-45aa-a0bf-77ae9a7a5240

---

## Configuração Azure e Autenticação

### 1. Autenticação Azure CLI

**Objetivo:** Autenticar o usuário no Azure para operações de infraestrutura.

**Processo:**
```bash
az login --tenant 1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d
```

**Resultado:** O usuário é autenticado no Azure CLI com permissões para gerenciar recursos na subscription.

### 2. Criação de Service Principal para Unity Catalog

**Objetivo:** Criar uma Azure AD App Registration (Service Principal) para autenticação do Databricks provider account-level.

**Script:** `scripts/setup-unity-catalog.ps1`

**Processo:**
1. Valida login do Azure CLI
2. Cria Azure AD App Registration
3. Cria Client Secret
4. Cria Service Principal
5. Atribui permissões (Contributor no Resource Group)
6. Imprime credenciais para uso no Terraform

**Credenciais Geradas:**
- Client ID: e02d0bb3-9850-41da-b590-1e9f7a0de7d5
- Client Secret: [REDACTED]
- Tenant ID: 1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d

**Uso:** Configurado em `infra/dev.tfvars` para autenticação do Databricks provider account-level.

### 3. Configuração GitHub OIDC

**Objetivo:** Configurar autenticação federada entre GitHub Actions e Azure AD.

**Script:** `scripts/setup-github-oidc.ps1`

**Processo:**
1. Valida login do Azure CLI e GitHub CLI
2. Resolve Object ID da App Registration
3. Cria credencial federada se não existir
4. Atribui roles do Azure (Contributor, Storage Blob Data Contributor)
5. Configura segredos do GitHub

**Segredos GitHub Configurados:**
- AZURE_CLIENT_ID
- AZURE_TENANT_ID
- AZURE_SUBSCRIPTION_ID
- DATABRICKS_TOKEN

### 4. Criação de Usuário Organizacional para Unity Catalog

**Objetivo:** Criar usuário organizacional com permissão Global Admin para gerenciar Unity Catalog.

**Processo:**
1. Criar usuário organizacional via Azure CLI:
```bash
az ad user create --display-name "Admin User" --user-principal-name admin@thallysoncamila2017outlook.onmicrosoft.com --password "SuaSenhaSegura123!"
```

2. Atribuir permissão Global Admin via Azure Portal
3. Login com novo usuário no Databricks Account Console
4. Criar grupos account-level: data-engineers, data-scientists, data-analysts

**Resultado:** Usuário com permissões para gerenciar Unity Catalog no nível de conta.

---

## Infraestrutura Terraform

### 1. Configuração Terraform

**Arquivo:** `infra/providers.tf`

**Providers Configurados:**
- **azurerm**: Versão ~> 4.0 - Gerencia recursos Azure
- **databricks**: Versão >= 1.50.0, < 2.0.0 - Gerencia recursos Databricks
- **random**: Versão ~> 3.6 - Gera strings aleatórias para nomes

**Provider Azure:**
```hcl
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
  subscription_id = var.subscription_id
}
```

**Provider Databricks (Account-level):**
```hcl
provider "databricks" {
  alias               = "account"
  host                = "https://accounts.azuredatabricks.net"
  azure_client_id     = var.client_id
  azure_client_secret = var.client_secret
  azure_tenant_id     = var.tenant_id
  auth_type           = "azure-client-secret"
}
```

**Provider Databricks (Workspace-level):**
```hcl
provider "databricks" {
  host      = var.databricks_host
  auth_type = "azure-cli"
}
```

### 2. Variáveis Terraform

**Arquivo:** `infra/variables.tf`

**Variáveis Principais:**
- `project_name`: Nome do projeto (DataMasterV2)
- `environment`: Ambiente (dev/prod)
- `location`: Região Azure (brazilsouth)
- `subscription_id`: ID da subscription Azure
- `tenant_id`: ID do tenant Azure
- `client_id`: Client ID do service principal
- `client_secret`: Client secret do service principal
- `databricks_host`: URL do Databricks workspace
- `databricks_token`: PAT token do Databricks
- `enable_unity_catalog`: Habilita recursos Unity Catalog
- `enable_function_app`: Habilita Azure Function
- `databricks_sku`: SKU do Databricks workspace (premium)

**Variáveis de Geração de Dados:**
- `fake_num_clientes`: Número de clientes fake (1)
- `fake_num_restaurantes`: Número de restaurantes fake (1)
- `fake_num_drivers`: Número de drivers fake (1)
- `fake_num_items_per_restaurante`: Número de itens por restaurante (8)
- `fake_num_pedidos`: Número de pedidos fake (8)

### 3. Backend Terraform

**Arquivo:** `infra/backend.tf`

**Configuração:**
```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-datamasterv2-tfstate-dev"
    storage_account_name = "stdmv2tfstatedev"
    container_name       = "tfstate"
    key                  = "datamasterv2-dev.tfstate"
  }
}
```

**Objetivo:** Armazenar o estado do Terraform em Azure Storage para colaboração e persistência.

### 4. Infraestrutura Azure

**Arquivo:** `infra/infrastructure.tf`

**Recursos Criados:**

#### 4.1 Resource Group
```hcl
resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = local.tags
}
```
**Nome:** rg-dmv2-dev
**Objetivo:** Agrupar todos os recursos Azure do projeto.

#### 4.2 Virtual Network
```hcl
resource "azurerm_virtual_network" "main" {
  name                = "vnet-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = ["10.40.0.0/16"]
  tags                = local.tags
}
```
**Nome:** vnet-dmv2-dev
**CIDR:** 10.40.0.0/16
**Objetivo:** Isolar rede do Databricks workspace.

#### 4.3 Subnets
```hcl
resource "azurerm_subnet" "databricks_public" {
  name                 = "snet-${local.name_prefix}-dbx-public"
  address_prefixes     = ["10.40.1.0/24"]
  delegation {
    name = "databricks-delegation"
    service_delegation {
      name = "Microsoft.Databricks/workspaces"
    }
  }
}

resource "azurerm_subnet" "databricks_private" {
  name                 = "snet-${local.name_prefix}-dbx-private"
  address_prefixes     = ["10.40.2.0/24"]
  delegation {
    name = "databricks-delegation"
    service_delegation {
      name = "Microsoft.Databricks/workspaces"
    }
  }
}
```
**Nomes:** snet-dmv2-dev-dbx-public (10.40.1.0/24), snet-dmv2-dev-dbx-private (10.40.2.0/24)
**Objetivo:** Subnets delegadas para Databricks com isolamento de rede.

#### 4.4 Network Security Group
```hcl
resource "azurerm_network_security_group" "databricks" {
  name                = "nsg-${local.name_prefix}-databricks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}
```
**Nome:** nsg-dmv2-dev-databricks
**Objetivo:** Controlar tráfego de rede para subnets Databricks.

#### 4.5 Storage Account (ADLS Gen2)
```hcl
resource "azurerm_storage_account" "adls" {
  name                            = "st${local.safe_prefix}${random_string.suffix.result}"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  account_kind                    = "StorageV2"
  is_hns_enabled                  = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = local.tags
}
```
**Nome:** stdmv2devvxc02
**Objetivo:** Armazenar dados do Data Lake (containers source e rejeitados).

#### 4.6 Storage Containers
```hcl
resource "azurerm_storage_container" "containers" {
  for_each = local.containers
  name                  = each.key
  storage_account_id    = azurerm_storage_account.adls.id
  container_access_type = "private"
}
```
**Containers:** source, rejeitados
**Objetivo:** Organizar dados por tipo (source para dados brutos, rejeitados para dados inválidos).

#### 4.7 Key Vault
```hcl
resource "azurerm_key_vault" "main" {
  name                       = "kv-${local.safe_prefix}-${random_string.suffix.result}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  tags                       = local.tags
}
```
**Nome:** kv-dmv2dev-vxc02
**Objetivo:** Armazenar segredos (client secrets, connection strings).

#### 4.8 Log Analytics Workspace
```hcl
resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}
```
**Nome:** law-dmv2-dev
**Objetivo:** Coletar logs e métricas para monitoramento.

#### 4.9 Application Insights
```hcl
resource "azurerm_application_insights" "function" {
  name                = "appi-${local.name_prefix}-function"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = local.tags
}
```
**Nome:** appi-dmv2-dev-function
**Objetivo:** Monitorar Azure Function.

#### 4.10 Monitor Action Group
```hcl
resource "azurerm_monitor_action_group" "ops" {
  name                = "ag-${local.name_prefix}-ops"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "dmv2ops"
  tags                = local.tags
  email_receiver {
    name                    = "ops-email"
    email_address           = var.ops_email
    use_common_alert_schema = true
  }
}
```
**Nome:** ag-dmv2-dev-ops
**Objetivo:** Enviar alertas de monitoramento para email.

#### 4.11 Diagnostic Settings
```hcl
resource "azurerm_monitor_diagnostic_setting" "storage" {
  name                       = "diag-${local.name_prefix}-storage"
  target_resource_id         = azurerm_storage_account.adls.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  metric {
    category = "Transaction"
    enabled  = true
  }
  metric {
    category = "Capacity"
    enabled  = true
  }
}
```
**Nome:** diag-dmv2-dev-storage
**Objetivo:** Enviar métricas do Storage Account para Log Analytics.

#### 4.12 Databricks Workspace
```hcl
resource "azurerm_databricks_workspace" "main" {
  name                        = "dbw-${local.name_prefix}"
  resource_group_name         = azurerm_resource_group.main.name
  location                    = azurerm_resource_group.main.location
  sku                         = var.databricks_sku
  managed_resource_group_name = "rg-${local.name_prefix}-databricks-managed"
  tags                        = local.tags
  custom_parameters {
    no_public_ip                                         = var.no_public_ip
    virtual_network_id                                   = azurerm_virtual_network.main.id
    public_subnet_name                                   = azurerm_subnet.databricks_public.name
    private_subnet_name                                  = azurerm_subnet.databricks_private.name
    public_subnet_network_security_group_association_id  = azurerm_subnet_network_security_group_association.public.id
    private_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.private.id
  }
}
```
**Nome:** dbw-dmv2-dev
**SKU:** premium
**Objetivo:** Workspace Databricks para execução de pipelines e notebooks.

### 5. Recursos Event Hub

**Arquivo:** `infra/eventhub.tf`

**Recursos Criados:**
- Event Hub Namespace
- Event Hub (delivery_events)
- Event Hub Capture (para AVRO)

**Objetivo:** Ingerir eventos de delivery em tempo real e capturar para processamento batch.

### 6. Azure Function

**Arquivo:** `infra/function.tf`

**Recursos Criados:**
- App Service Plan
- Function App
- Application Insights

**Objetivo:** Gerar dados fake para simular eventos de delivery.

### 7. Databricks Resources

**Arquivo:** `infra/databricks.tf`

**Recursos Criados:**
- Secret Scope (dmv2-dev)
- Cluster Jobs (opcional)

**Objetivo:** Configurar recursos específicos do Databricks workspace.

---

## Databricks Workspace e Unity Catalog

### 1. Unity Catalog Configuration

**Arquivo:** `infra/unity_catalog.tf`

**Recursos Criados:**

#### 1.1 Catalog
```hcl
resource "databricks_catalog" "delivery" {
  count        = var.enable_unity_catalog && var.databricks_host != "" ? 1 : 0
  name         = "delivery_datamaster"
  comment      = "Delivery DataMaster governed catalog"
  storage_root = "abfss://source@stdmv2devvxc02.dfs.core.windows.net/uc-managed/delivery_datamaster"
  properties = {
    environment = var.environment
    domain      = "delivery"
    owner       = "data_platform_team"
  }
}
```
**Nome:** delivery_datamaster
**Objetivo:** Catálogo principal do Unity Catalog para governança de dados.

#### 1.2 Schemas (Layers)
```hcl
resource "databricks_schema" "layers" {
  for_each = var.enable_unity_catalog && var.databricks_host != "" ? toset(["bronze", "silver", "gold"]) : []
  catalog_name = databricks_catalog.delivery[0].name
  name         = each.key
  comment      = "${each.key} layer for DataMasterV2"
  properties = {
    layer            = each.key
    retention_period = each.key == "bronze" ? "90 days" : each.key == "silver" ? "180 days" : "365 days"
  }
}
```
**Schemas:** bronze, silver, gold
**Objetivo:** Organizar dados por camada de qualidade (Medallion Architecture).

#### 1.3 User Assigned Identity
```hcl
resource "azurerm_user_assigned_identity" "databricks_uc" {
  count               = var.enable_unity_catalog ? 1 : 0
  name                = "dbmanagedidentity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_databricks_workspace.main.managed_resource_group_name
}
```
**Nome:** dbmanagedidentity
**Objetivo:** Identidade gerenciada para Unity Catalog acessar ADLS.

#### 1.4 Databricks Access Connector
```hcl
resource "azurerm_databricks_access_connector" "unity_catalog" {
  count               = var.enable_unity_catalog ? 1 : 0
  name                = "unity-catalog-access-connector"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_databricks_workspace.main.managed_resource_group_name
  identity {
    type = "SystemAssigned"
  }
}
```
**Nome:** unity-catalog-access-connector
**Objetivo:** Conector de acesso para Unity Catalog.

#### 1.5 Role Assignment
```hcl
resource "azurerm_role_assignment" "databricks_uc_storage_blob_contributor" {
  count                = var.enable_unity_catalog ? 1 : 0
  scope                = azurerm_storage_account.adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.unity_catalog[0].identity[0].principal_id
}
```
**Objetivo:** Conceder permissão ao conector para acessar Storage Account.

#### 1.6 Storage Credential
```hcl
resource "databricks_storage_credential" "source" {
  count = var.enable_unity_catalog && var.databricks_host != "" ? 1 : 0
  name  = "cred_dmv2_source_lab"
  azure_managed_identity {
    access_connector_id = azurerm_databricks_access_connector.unity_catalog[0].id
  }
  comment = "Managed Identity credential for DataMasterV2 source ADLS access"
}
```
**Nome:** cred_dmv2_source_lab
**Objetivo:** Credencial de storage para Unity Catalog acessar ADLS.

#### 1.7 External Location
```hcl
resource "databricks_external_location" "source" {
  count           = var.enable_unity_catalog && var.databricks_host != "" ? 1 : 0
  name            = "extloc_dmv2_source_lab"
  url             = "abfss://source@stdmv2devvxc02.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.source[0].name
  comment         = "External location for DataMasterV2 source container"
}
```
**Nome:** extloc_dmv2_source_lab
**Objetivo:** Localização externa para Unity Catalog acessar container source.

#### 1.8 Grants
```hcl
resource "databricks_grants" "source_location" {
  count             = var.enable_unity_catalog && var.databricks_host != "" ? 1 : 0
  external_location = databricks_external_location.source[0].name
  grant {
    principal  = "account users"
    privileges = ["READ_FILES"]
  }
}
```
**Objetivo:** Conceder permissão de leitura para "account users" na localização externa.

### 2. Configuração Manual de Permissões

**Motivo:** Terraform teve conflitos ao tentar gerenciar permissões devido a discrepâncias entre estado atual e desejado.

**Processo Manual:**
1. Acessar: https://accounts.azuredatabricks.net
2. Vá para "Data" → "Unity Catalog"
3. Selecione o catalog "delivery_datamaster"
4. Clique em "Permissions"
5. Adicione/remova permissões conforme necessário

**Grupos Account-Level:**
- data-engineers
- data-scientists
- data-analysts

---

## Pipelines DLT e Lakeflow

### 1. Databricks Bundle Configuration

**Arquivo:** `lakeflow/databricks.yml`

**Bundle Name:** datamasterv2-delivery-lakeflow-v2

**Variables:**
- catalog: delivery_datamaster
- schema: default
- source_path: abfss://source@stdmv2devvxc02.dfs.core.windows.net/eventhub-capture
- azure_tenant_id: 1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d
- azure_client_id: 7da295f3-e9d6-4a72-9f47-8e3bde7fcc92
- azure_subscription_id: 97eb265c-59ce-4122-bbe4-98f0d58d9208
- cost_schema: observability
- cost_secret_scope: dmv2-dev
- cost_secret_key: azure-client-secret

**Target: dev**
- Mode: development
- Workspace: https://adb-7405608830882565.5.azuredatabricks.net/

### 2. DLT Pipeline

**Nome:** dlt-dmv2-delivery-eventhub-dev

**Configuração:**
- Catalog: delivery_datamaster
- Target: default
- Development: true
- Continuous: false
- Photon: true
- Channel: CURRENT
- Cluster: Standard_D4s_v3 (1 worker)

**Configuration:**
- source_path: abfss://source@stdmv2devvxc02.dfs.core.windows.net/eventhub-capture
- catalog_name: delivery_datamaster
- schema_name: default
- dq_rules_path: ${workspace.file_path}/data_quality/rules.py

**Libraries:**
- bronze/bronze_eventhub_capture.py
- silver/silver_delivery_entities.py
- gold/gold_delivery_metrics.py

### 3. Bronze Layer

**Arquivo:** `lakeflow/bronze/bronze_eventhub_capture.py`

**Objetivo:** Ingerir dados brutos do Event Hub Capture para tabelas Bronze.

**Processo:**
1. Lê arquivos AVRO do Event Hub Capture
2. Aplica validações básicas
3. Escreve em tabelas Delta Bronze
4. Aplica regras de qualidade de dados

**Tabelas Bronze:**
- bronze_delivery_batches
- bronze_delivery_events
- bronze_delivery_status

### 4. Silver Layer

**Arquivo:** `lakeflow/silver/silver_delivery_entities.py`

**Objetivo:** Transformar dados Bronze em entidades normalizadas.

**Processo:**
1. Lê tabelas Bronze
2. Aplica transformações de negócio
3. Normaliza entidades (clientes, restaurantes, drivers, pedidos)
4. Aplica regras de qualidade de dados
5. Escreve em tabelas Delta Silver

**Tabelas Silver:**
- silver_clientes
- silver_restaurantes
- silver_drivers
- silver_orders
- silver_order_items

### 5. Gold Layer

**Arquivo:** `lakeflow/gold/gold_delivery_metrics.py`

**Objetivo:** Criar métricas agregadas e KPIs para análise.

**Processo:**
1. Lê tabelas Silver
2. Agrega dados por dimensões (tempo, local, etc.)
3. Calcula KPIs de delivery
4. Cria tabelas otimizadas para consulta

**Tabelas Gold:**
- gold_daily_delivery_kpis
- gold_restaurant_performance
- gold_item_category_metrics

### 6. Data Quality

**Arquivo:** `lakeflow/data_quality/rules.py`

**Objetivo:** Definir regras de qualidade de dados.

**Regras:**
- Validação de schema
- Validação de valores nulos
- Validação de ranges
- Validação de integridade referencial

---

## Governança de Dados

### 1. Notebook de Governança

**Arquivo:** `lakeflow/governance/apply_governance.py`

**Objetivo:** Aplicar governança de dados no Unity Catalog.

**Processo:**

#### 1.1 Criação de Schema Governance
```python
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {gov_schema}")
spark.sql(f"ALTER SCHEMA {gov_schema} SET TAGS ('layer' = 'governance', 'domain' = 'delivery', 'contains_masked_views' = 'true')")
```

**Schema:** delivery_datamaster.governance
**Tags:** layer=governance, domain=delivery, contains_masked_views=true

#### 1.2 Aplicação de Tags

**Tags de Tabelas:**
- silver_clientes: layer=silver, classification=restricted, contains_pii=true, domain=customer
- silver_restaurantes: layer=silver, classification=confidential, contains_pii=true, domain=restaurant
- silver_drivers: layer=silver, classification=restricted, contains_pii=true, domain=driver
- silver_orders: layer=silver, classification=internal, contains_financial=true, domain=order
- silver_order_items: layer=silver, classification=internal, contains_financial=true, domain=order
- gold_daily_delivery_kpis: layer=gold, classification=business, contains_pii=false, domain=analytics
- gold_restaurant_performance: layer=gold, classification=business, contains_pii=false, domain=analytics
- gold_item_category_metrics: layer=gold, classification=business, contains_pii=false, domain=analytics

**Tags de Colunas:**
- silver_clientes: nome=PII, endereco=PII, cpf=PII_HIGH
- silver_restaurantes: endereco=PII, cnpj=SENSITIVE_ID
- silver_drivers: nome=PII, endereco=PII, placa=SENSITIVE_ID
- silver_orders: valor_total=FINANCIAL, client_id=BUSINESS_KEY, driver_id=BUSINESS_KEY
- silver_order_items: preco=FINANCIAL, valor_total_item=FINANCIAL

#### 1.3 Criação de Views Mascaradas

**vw_clientes_analyst:**
```python
spark.sql(f"""
CREATE OR REPLACE VIEW {gov_schema}.`vw_clientes_analyst` AS
SELECT
  client_id,
  concat(substr(nome, 1, 1), '***') AS nome,
  concat('***', substr(cpf, -4)) AS cpf_mascarado,
  tipo_pagamento,
  created_at
FROM {source_schema}.`silver_clientes`
""")
```

**vw_drivers_analyst:**
```python
spark.sql(f"""
CREATE OR REPLACE VIEW {gov_schema}.`vw_drivers_analyst` AS
SELECT
  driver_id,
  concat(substr(nome, 1, 1), '***') AS nome,
  veiculo,
  concat('***-', substr(placa, -4)) AS placa_mascarada,
  created_at
FROM {source_schema}.`silver_drivers`
""")
```

**vw_orders_analytics:**
```python
spark.sql(f"""
CREATE OR REPLACE VIEW {gov_schema}.`vw_orders_analytics` AS
SELECT
  order_id,
  restaurant_id,
  quantidade_total,
  valor_total,
  tipo_pagamento,
  order_date,
  order_year,
  order_month,
  order_day,
  order_hour,
  amount_category
FROM {source_schema}.`silver_orders`
""")
```

**vw_gold_delivery_dashboard:**
```python
spark.sql(f"""
CREATE OR REPLACE VIEW {gov_schema}.`vw_gold_delivery_dashboard` AS
SELECT * FROM {source_schema}.`gold_daily_delivery_kpis`
""")
```

#### 1.4 Permissões Granulares

**Permissões para Tabelas Bronze (Streaming):**
- data-engineers: SELECT, MODIFY
- data-scientists: SELECT
- data-analysts: SELECT

**Permissões para Tabelas Silver (Streaming):**
- data-engineers: SELECT, MODIFY
- data-scientists: SELECT
- data-analysts: SELECT

**Permissões para Tabelas Gold (Materialized Views):**
- data-engineers: SELECT
- data-scientists: SELECT
- data-analysts: SELECT

**Permissões para Views Governance (Mascaradas):**
- Todos os grupos: SELECT

**Grupos Account-Level:**
- data-engineers
- data-scientists
- data-analysts

---

## GitHub Actions e CI/CD

### 1. Workflow de Deploy Dev

**Arquivo:** `.github/workflows/deploy-dev.yml`

**Nome:** Deploy Dev

**Trigger:**
- Push para branch dev
- Workflow dispatch (manual)

**Permissões:**
- contents: read
- id-token: write (para OIDC)

**Variáveis de Ambiente:**
- TF_VERSION: 1.9.8
- AZURE_FUNCTIONAPP_NAME: func-dmv2-dev-generator
- AZURE_RESOURCE_GROUP: rg-dmv2-dev
- TFSTATE_RESOURCE_GROUP: rg-datamasterv2-tfstate-dev
- TFSTATE_LOCATION: brazilsouth
- TFSTATE_STORAGE_ACCOUNT: stdmv2tfstatedev
- TFSTATE_CONTAINER: tfstate
- FUNCTION_PROJECT_PATH: azure_function/GeracaoData
- DATABRICKS_HOST: https://adb-7405608830882565.5.azuredatabricks.net/

### 2. Job 1: Setup Terraform Backend

**Nome:** Setup Terraform Backend

**Objetivo:** Criar backend remoto para o Terraform state.

**Steps:**
1. Azure CLI Login
2. Create Terraform Backend Resource Group
3. Create Terraform Backend Storage Account
4. Create Terraform Backend Container

**Recursos Criados:**
- Resource Group: rg-datamasterv2-tfstate-dev
- Storage Account: stdmv2tfstatedev
- Container: tfstate

### 3. Job 2: Terraform Apply

**Nome:** Terraform Apply

**Depends On:** setup-tf-backend

**Objetivo:** Aplicar infraestrutura Terraform.

**Variáveis de Ambiente:**
- ARM_USE_OIDC: true
- ARM_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
- ARM_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
- ARM_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
- TF_VAR_client_id: ${{ secrets.AZURE_CLIENT_ID }}
- TF_VAR_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
- TF_VAR_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
- TF_VAR_project_name: DataMasterV2
- TF_VAR_environment: dev
- TF_VAR_location: brazilsouth
- TF_VAR_enable_function_app: true
- TF_VAR_function_location: westeurope
- TF_VAR_enable_unity_catalog: true
- TF_VAR_unity_catalog_metastore_id: ""
- TF_VAR_databricks_host: https://adb-7405608830882565.5.azuredatabricks.net/
- TF_VAR_databricks_token: ${{ secrets.DATABRICKS_TOKEN }}
- TF_VAR_function_schedule: "0 */1 * * * *"
- TF_VAR_fake_num_clientes: 1
- TF_VAR_fake_num_restaurantes: 1
- TF_VAR_fake_num_drivers: 1
- TF_VAR_fake_num_items_per_restaurante: 8
- TF_VAR_fake_num_pedidos: 8

**Steps:**
1. Checkout repository
2. Azure CLI Login
3. Setup Terraform
4. Terraform Init
5. Terraform Plan
6. Terraform Apply
7. Export Terraform Outputs

### 4. Job 3: Deploy Azure Function

**Nome:** Publish Azure Function

**Depends On:** terraform

**Objetivo:** Deploy Azure Function para geração de dados fake.

**Steps:**
1. Checkout repository
2. Azure CLI Login
3. Setup Node.js (v20)
4. Install Azure Functions Core Tools
5. Setup Python (v3.11)
6. Validate Python Function Syntax
7. Publish Function App via func CLI
8. Restart Function App
9. Validate Published Function Trigger

**Function App:** func-dmv2-dev-generator
**Project Path:** azure_function/GeracaoData

### 5. Job 4: Deploy Databricks Lakeflow

**Nome:** Deploy Databricks Lakeflow

**Depends On:** terraform

**Objetivo:** Deploy Databricks Bundle com pipelines e jobs.

**Variáveis de Ambiente:**
- DATABRICKS_HOST: https://adb-7405608830882565.5.azuredatabricks.net/
- DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}

**Steps:**
1. Checkout repository
2. Setup Databricks CLI
3. Setup Terraform for Databricks Bundle
4. Validate Databricks Authentication
5. Validate Databricks Bundle
6. Deploy Databricks Bundle
7. Bundle Deploy Summary

**Recursos Deployed:**
- DLT Pipeline: dlt-dmv2-delivery-eventhub-dev
- Job Azure Cost Observability: job-dmv2-azure-cost-observability
- Job Delta Table Maintenance: job-dmv2-delta-table-maintenance
- Job Apply Governance: job-dmv2-apply-governance

---

## Observabilidade e Monitoramento

### 1. Azure Cost Observability

**Arquivo:** `lakeflow/observability/azure_cost_ingestion.py`

**Objetivo:** Ingerir custos do Azure para monitoramento.

**Job:** job-dmv2-azure-cost-observability

**Schedule:** 0 0 8 * * ? (8:00 AM, America/Sao_Paulo)
**Status:** PAUSED

**Parameters:**
- tenant_id: 1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d
- client_id: 7da295f3-e9d6-4a72-9f47-8e3bde7fcc92
- subscription_id: 97eb265c-59ce-4122-bbe4-98f0d58d9208
- catalog: delivery_datamaster
- schema: observability
- secret_scope: dmv2-dev
- secret_key: azure-client-secret
- lookback_days: "30"

**Cluster:** SingleNode (Standard_D4s_v3)

**Processo:**
1. Lê custos do Azure Cost Management API
2. Escreve em tabelas Delta no schema observability
3. Permite análise de custos por serviço, resource group, etc.

### 2. Delta Table Maintenance

**Arquivo:** `lakeflow/maintenance/delta_maintenance.py`

**Objetivo:** Manutenção de tabelas Delta (OPTIMIZE e VACUUM).

**Job:** job-dmv2-delta-table-maintenance

**Parameters:**
- catalog: delivery_datamaster
- schema: default
- retention_hours: "168" (7 dias)

**Cluster:** SingleNode (Standard_D4s_v3)

**Processo:**
1. Executa OPTIMIZE em tabelas Delta
2. Executa VACUUM para remover arquivos antigos
3. Melhora performance de consultas
4. Reduz custo de storage

### 3. Monitoramento Azure

**Recursos:**
- Log Analytics Workspace: law-dmv2-dev
- Application Insights: appi-dmv2-dev-function
- Monitor Action Group: ag-dmv2-dev-ops
- Diagnostic Settings: diag-dmv2-dev-storage

**Métricas Coletadas:**
- Storage Account: Transaction, Capacity
- Azure Function: Requests, Errors, Response Time
- Databricks: Cluster metrics, Pipeline metrics

**Alertas:**
- Email para ops@example.com via Action Group

---

## Scripts de Automação

### 1. Setup GitHub OIDC

**Arquivo:** `scripts/setup-github-oidc.ps1`

**Objetivo:** Configurar autenticação federada entre GitHub Actions e Azure AD.

**Processo:**
1. Valida login do Azure CLI e GitHub CLI
2. Resolve Object ID da App Registration
3. Cria credencial federada se não existir
4. Atribui roles do Azure (Contributor, Storage Blob Data Contributor)
5. Configura segredos do GitHub

**Segredos GitHub Configurados:**
- AZURE_CLIENT_ID
- AZURE_TENANT_ID
- AZURE_SUBSCRIPTION_ID
- DATABRICKS_TOKEN

### 2. Setup Unity Catalog

**Arquivo:** `scripts/setup-unity-catalog.ps1`

**Objetivo:** Criar Azure AD App Registration para autenticação do Databricks provider account-level.

**Processo:**
1. Valida login do Azure CLI
2. Cria Azure AD App Registration
3. Cria Client Secret
4. Cria Service Principal
5. Atribui permissões (Contributor no Resource Group)
6. Imprime credenciais para uso no Terraform

**Credenciais Geradas:**
- Client ID: e02d0bb3-9850-41da-b590-1e9f7a0de7d5
- Client Secret: [REDACTED]
- Tenant ID: 1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d

---

## Resumo da Arquitetura

### Fluxo de Dados

```
Azure Function (Gerador de Dados) → Event Hub → Event Hub Capture (AVRO) → 
DLT Bronze (Ingestão) → DLT Silver (Transformação) → DLT Gold (Agregação) → 
Unity Catalog (Governança) → Views Mascaradas (Proteção de Dados)
```

### Fluxo de Deploy

```
GitHub Actions (Push dev) → Setup Terraform Backend → Terraform Apply → 
Deploy Azure Function → Deploy Databricks Bundle → 
DLT Pipeline + Jobs + Governança
```

### Camadas de Dados

**Bronze (Raw Data):**
- Fonte: Event Hub Capture (AVRO)
- Formato: Delta
- Retenção: 90 dias
- Permissões: data-engineers (SELECT, MODIFY), outros (SELECT)

**Silver (Processed):**
- Fonte: Bronze
- Formato: Delta
- Retenção: 180 dias
- Permissões: data-engineers (SELECT, MODIFY), outros (SELECT)

**Gold (Curated):**
- Fonte: Silver
- Formato: Delta (Materialized Views)
- Retenção: 365 dias
- Permissões: Todos os grupos (SELECT)

**Governance (Mascaradas):**
- Fonte: Silver/Gold
- Formato: Views
- Permissões: Todos os grupos (SELECT)

### Governança de Dados

**Tags:**
- Classificação de dados (restricted, confidential, internal, business)
- Identificação de PII (contains_pii)
- Domínio de negócio (customer, restaurant, driver, order, analytics)

**Views Mascaradas:**
- Proteção de dados sensíveis (nome, cpf, placa)
- Acesso controlado por grupo
- Auditoria via Unity Catalog

**Permissões:**
- Grupos account-level (data-engineers, data-scientists, data-analysts)
- Permissões granulares por camada
- Gerenciamento manual via Account Console

### Monitoramento

**Azure:**
- Log Analytics Workspace
- Application Insights
- Monitor Action Group
- Diagnostic Settings

**Databricks:**
- Cluster metrics
- Pipeline metrics
- Job metrics

**Custos:**
- Azure Cost Management ingestion
- Análise de custos por serviço
- Alertas de custo

---

## Conclusão

O DataMasterV2 é uma arquitetura completa de engenharia de dados que combina:

1. **Infraestrutura como Código (Terraform)** para automação de recursos Azure
2. **Delta Live Tables (DLT)** para pipelines de dados confiáveis
3. **Unity Catalog** para governança de dados centralizada
4. **Lakeflow** para orquestração de pipelines e jobs
5. **GitHub Actions** para CI/CD automatizado
6. **Observabilidade** para monitoramento e alertas
7. **Scripts de Automação** para setup e configuração

A arquitetura segue as melhores práticas de engenharia de dados, incluindo:
- Medallion Architecture (Bronze/Silver/Gold)
- Governança de dados (Tags, Views, Permissões)
- CI/CD automatizado
- Monitoramento e observabilidade
- Segurança (OIDC, RBAC, PII masking)
- Escalabilidade (Delta Lake, Databricks)
- Cost management (Azure Cost Management)

---

**DataMasterV2 - Documentação Completa da Arquitetura**
**Versão:** 1.0
**Data:** 2026-06-21
**Autor:** Cascade AI Assistant
