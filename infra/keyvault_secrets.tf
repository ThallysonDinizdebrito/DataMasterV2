# Azure Key Vault Secrets Management
# Este arquivo gerencia automaticamente os segredos no Azure Key Vault
# NOTA: Por enquanto, os segredos são gerenciados manualmente no Databricks Secret Scope
# Este arquivo está preparado para uso futuro quando Key Vault for totalmente integrado

# Segredo de teste para validação da Azure Function
# NOTA: Criado manualmente no portal Azure devido a falta de permissão do Terraform
# resource "azurerm_key_vault_secret" "test_secret" {
#   name         = "test-secret"
#   value        = "test-keyvault-integration-12345"
#   key_vault_id = azurerm_key_vault.main.id
#
#   content_type = "text/plain"
# }

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
