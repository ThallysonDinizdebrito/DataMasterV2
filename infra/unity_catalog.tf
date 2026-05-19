resource "databricks_metastore_assignment" "main" {
  count                = var.enable_unity_catalog && var.databricks_host != "" && var.unity_catalog_metastore_id != "" ? 1 : 0
  workspace_id         = azurerm_databricks_workspace.main.workspace_id
  metastore_id         = var.unity_catalog_metastore_id
  default_catalog_name = "delivery_datamaster"
}

resource "databricks_catalog" "delivery" {
  count      = var.enable_unity_catalog && var.databricks_host != "" ? 1 : 0
  name       = "delivery_datamaster"
  comment    = "Delivery DataMaster governed catalog"
  depends_on = [databricks_metastore_assignment.main]

  properties = {
    environment = var.environment
    domain      = "delivery"
    owner       = "data_platform_team"
  }
}

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
