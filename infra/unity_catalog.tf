# Metastore já está configurado no workspace, não precisa de assignment
# resource "databricks_metastore_assignment" "main" {
#   count                = var.enable_unity_catalog && var.databricks_host != "" && var.unity_catalog_metastore_id != "" ? 1 : 0
#   workspace_id         = azurerm_databricks_workspace.main.workspace_id
#   metastore_id         = var.unity_catalog_metastore_id
#   default_catalog_name = "delivery_datamaster"
# }

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

resource "azurerm_user_assigned_identity" "databricks_uc" {
  count               = var.enable_unity_catalog ? 1 : 0
  name                = "dbmanagedidentity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_databricks_workspace.main.managed_resource_group_name
  tags = merge(local.tags, {
    application              = "databricks"
    databricks-environment   = "true"
  })
}

resource "azurerm_databricks_access_connector" "unity_catalog" {
  count               = var.enable_unity_catalog ? 1 : 0
  name                = "unity-catalog-access-connector"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_databricks_workspace.main.managed_resource_group_name
  tags = merge(local.tags, {
    application              = "databricks"
    databricks-environment   = "true"
  })

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_role_assignment" "databricks_uc_storage_blob_contributor" {
  count                = var.enable_unity_catalog ? 1 : 0
  scope                = azurerm_storage_account.adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.unity_catalog[0].identity[0].principal_id
}

resource "databricks_storage_credential" "source" {
  count = var.enable_unity_catalog && var.databricks_host != "" ? 1 : 0
  name  = "cred_dmv2_source_lab"

  azure_managed_identity {
    access_connector_id = azurerm_databricks_access_connector.unity_catalog[0].id
  }

  comment = "Managed Identity credential for DataMasterV2 source ADLS access"

  lifecycle {
    ignore_changes = [comment]
  }
}

resource "databricks_external_location" "source" {
  count           = var.enable_unity_catalog && var.databricks_host != "" ? 1 : 0
  name            = "extloc_dmv2_source_lab"
  url             = "abfss://source@stdmv2devvxc02.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.source[0].name
  comment         = "External location for DataMasterV2 source container"
}

resource "databricks_grants" "source_location" {
  count             = var.enable_unity_catalog && var.databricks_host != "" ? 1 : 0
  external_location = databricks_external_location.source[0].name

  grant {
    principal  = "account users"
    privileges = ["READ_FILES"]
  }
}

# Permissões configuradas manualmente no Unity Catalog via Account Console
# Grupos account-level criados: data-engineers, data-scientists, data-analysts
# Permissões gerenciadas manualmente para evitar conflitos com Terraform
