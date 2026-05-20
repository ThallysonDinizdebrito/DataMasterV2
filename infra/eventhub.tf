# resource "azurerm_eventhub_namespace" "main" {
#   name                = "evhns-${local.name_prefix}-${random_string.suffix.result}"
#   location            = azurerm_resource_group.main.location
#   resource_group_name = azurerm_resource_group.main.name
#   sku                 = "Standard"
#   capacity            = 1
#   minimum_tls_version = "1.2"
#   tags                = local.tags
# }

# resource "azurerm_eventhub" "delivery_events" {
#   name                = "delivery-events"
#   namespace_name      = azurerm_eventhub_namespace.main.name
#   resource_group_name = azurerm_resource_group.main.name
#   partition_count     = var.eventhub_partition_count
#   message_retention   = var.eventhub_message_retention_days

#   capture_description {
#     enabled             = true
#     encoding            = "Avro"
#     interval_in_seconds = var.eventhub_capture_interval_seconds
#     size_limit_in_bytes = var.eventhub_capture_size_limit_bytes
#     skip_empty_archives = true

#     destination {
#       name                = "EventHubArchive.AzureBlockBlob"
#       archive_name_format = "eventhub-capture/{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}"
#       blob_container_name = azurerm_storage_container.containers["source"].name
#       storage_account_id  = azurerm_storage_account.adls.id
#     }
#   }
# }

# resource "azurerm_monitor_diagnostic_setting" "eventhub_namespace" {
#   name                       = "diag-${local.name_prefix}-eventhub"
#   target_resource_id         = azurerm_eventhub_namespace.main.id
#   log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

#   enabled_log {
#     category = "ArchiveLogs"
#   }

#   enabled_log {
#     category = "OperationalLogs"
#   }

#   enabled_metric {
#     category = "AllMetrics"
#   }
# }
