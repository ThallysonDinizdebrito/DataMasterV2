resource "azurerm_service_plan" "function" {
  count = var.enable_function_app ? 1 : 0

  name                = "asp-${local.name_prefix}-function"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.function_location
  os_type             = "Linux"
  sku_name            = "Y1"
  tags                = local.tags
}

resource "azurerm_linux_function_app" "generator" {
  count = var.enable_function_app ? 1 : 0

  name                       = "func-${local.name_prefix}-generator"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = var.function_location
  service_plan_id            = azurerm_service_plan.function[0].id
  storage_account_name       = azurerm_storage_account.adls.name
  storage_account_access_key = azurerm_storage_account.adls.primary_access_key
  tags                       = local.tags

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.11"
    }

    application_insights_connection_string = azurerm_application_insights.function.connection_string
    application_insights_key               = azurerm_application_insights.function.instrumentation_key
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME           = "python"
    STORAGE_ACCOUNT_URL                = azurerm_storage_account.adls.primary_blob_endpoint
    SOURCE_CONTAINER                   = "source"
    REJECTED_CONTAINER                 = "rejeitados"
    # EVENTHUB_NAMESPACE                 = azurerm_eventhub_namespace.main.name
    # EVENTHUB_NAME                      = azurerm_eventhub.delivery_events.name
    # EVENTHUB_FULLY_QUALIFIED_NAMESPACE = "${azurerm_eventhub_namespace.main.name}.servicebus.windows.net"
    FUNCTION_SCHEDULE                  = var.function_schedule
    NUM_CLIENTES                       = tostring(var.fake_num_clientes)
    NUM_RESTAURANTES                   = tostring(var.fake_num_restaurantes)
    NUM_DRIVERS                        = tostring(var.fake_num_drivers)
    NUM_ITEMS_PER_RESTAURANTE          = tostring(var.fake_num_items_per_restaurante)
    NUM_PEDIDOS                        = tostring(var.fake_num_pedidos)
  }

  lifecycle {
    ignore_changes = [
      tags["hidden-link: /app-insights-resource-id"]
    ]
  }
}

resource "azurerm_role_assignment" "function_storage_contributor" {
  count = var.enable_function_app ? 1 : 0

  scope                = azurerm_storage_account.adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.generator[0].identity[0].principal_id
}

resource "azurerm_role_assignment" "function_keyvault_secrets_user" {
  count = var.enable_function_app ? 1 : 0

  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_linux_function_app.generator[0].identity[0].principal_id
}

# resource "azurerm_role_assignment" "function_eventhub_sender" {
#   count = var.enable_function_app ? 1 : 0

#   scope                = azurerm_eventhub_namespace.main.id
#   role_definition_name = "Azure Event Hubs Data Sender"
#   principal_id         = azurerm_linux_function_app.generator[0].identity[0].principal_id
# }
