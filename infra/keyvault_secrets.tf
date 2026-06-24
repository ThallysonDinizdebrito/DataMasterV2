# Azure Key Vault Secrets Management
# Este arquivo gerencia automaticamente os segredos no Azure Key Vault

# Segredo: Azure Client Secret para Azure Cost Management
resource "azurerm_key_vault_secret" "azure_client_secret" {
  count        = var.enable_azure_cost_observability ? 1 : 0
  name         = "azure-client-secret"
  value        = var.azure_client_secret
  key_vault_id = azurerm_key_vault.main.id

  # Não expor o valor nos logs
  lifecycle {
    ignore_changes = [value]
  }
}

# Segredo: Databricks Token (opcional - se precisar armazenar no Key Vault)
resource "azurerm_key_vault_secret" "databricks_token" {
  count        = var.databricks_token != "" && var.store_databricks_token_in_kv ? 1 : 0
  name         = "databricks-token"
  value        = var.databricks_token
  key_vault_id = azurerm_key_vault.main.id

  lifecycle {
    ignore_changes = [value]
  }
}

# Segredo: Event Hub Connection String (quando Event Hub for habilitado)
resource "azurerm_key_vault_secret" "eventhub_connection_string" {
  count        = var.enable_eventhub ? 1 : 0
  name         = "eventhub-connection-string"
  value        = azurerm_eventhub_namespace.main.default_primary_connection_string
  key_vault_id = azurerm_key_vault.main.id

  lifecycle {
    ignore_changes = [value]
  }
}

# Segredo: Storage Account Access Key (para Azure Function)
resource "azurerm_key_vault_secret" "storage_access_key" {
  count        = var.enable_function_app ? 1 : 0
  name         = "storage-access-key"
  value        = azurerm_storage_account.adls.primary_access_key
  key_vault_id = azurerm_key_vault.main.id

  lifecycle {
    ignore_changes = [value]
  }
}
