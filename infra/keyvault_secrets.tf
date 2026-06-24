# Azure Key Vault Secrets Management
# Este arquivo gerencia automaticamente os segredos no Azure Key Vault
# NOTA: Por enquanto, os segredos são gerenciados manualmente no Databricks Secret Scope
# Este arquivo está preparado para uso futuro quando Key Vault for totalmente integrado

# Segredo: Storage Account Access Key (para Azure Function - opcional)
# resource "azurerm_key_vault_secret" "storage_access_key" {
#   count        = var.enable_function_app ? 1 : 0
#   name         = "storage-access-key"
#   value        = azurerm_storage_account.adls.primary_access_key
#   key_vault_id = azurerm_key_vault.main.id
#
#   lifecycle {
#     ignore_changes = [value]
#   }
# }
