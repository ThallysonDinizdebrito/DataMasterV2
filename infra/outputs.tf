output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value = azurerm_storage_account.adls.name
}

output "source_container_name" {
  value = azurerm_storage_container.containers["source"].name
}

output "rejected_container_name" {
  value = azurerm_storage_container.containers["rejeitados"].name
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "function_app_name" {
  value = var.enable_function_app ? azurerm_linux_function_app.generator[0].name : null
}

output "eventhub_namespace_name" {
  value = azurerm_eventhub_namespace.main.name
}

output "eventhub_name" {
  value = azurerm_eventhub.delivery_events.name
}

output "eventhub_capture_path" {
  value = "source/eventhub-capture/{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}"
}

output "databricks_workspace_name" {
  value = azurerm_databricks_workspace.main.name
}

output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.main.workspace_url
}

output "grafana_name" {
  value = azurerm_dashboard_grafana.main.name
}

output "grafana_endpoint" {
  value = azurerm_dashboard_grafana.main.endpoint
}
