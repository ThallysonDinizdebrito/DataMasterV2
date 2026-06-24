# Grupos account-level criados manualmente no Account Console
# data-engineers, data-scientists, data-analysts

# Secret scope backed by Azure Key Vault
resource "databricks_secret_scope" "keyvault" {
  count = var.databricks_host != "" && var.enable_azure_cost_observability ? 1 : 0
  name  = "kv-backed"

  keyvault_metadata {
    resource_id = azurerm_key_vault.main.id
    dns_suffix  = "vault.azure.net"
  }
}

# Secret scope legado (opcional, para compatibilidade)
resource "databricks_secret_scope" "main" {
  count = var.databricks_host != "" ? 1 : 0
  name  = "kv-${local.name_prefix}"
}

resource "databricks_cluster" "jobs" {
  count                   = var.databricks_host != "" && var.enable_databricks_jobs_cluster ? 1 : 0
  cluster_name            = "dbc-${local.name_prefix}-jobs"
  spark_version           = "15.4.x-photon-scala2.12"
  node_type_id            = "Standard_DS3_v2"
  autotermination_minutes = 10
  data_security_mode      = "SINGLE_USER"

  autoscale {
    min_workers = 1
    max_workers = 2
  }

  custom_tags = local.tags
}

resource "databricks_sql_endpoint" "main" {
  count                     = var.databricks_host == "" ? 0 : 1
  name                      = "sql-${local.name_prefix}"
  cluster_size              = "2X-Small"
  warehouse_type            = "PRO"
  min_num_clusters          = 1
  max_num_clusters          = 2
  auto_stop_mins            = 10
  enable_photon             = true
  enable_serverless_compute = true
}
