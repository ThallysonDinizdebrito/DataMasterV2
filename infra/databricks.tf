resource "databricks_group" "data_engineers" {
  count        = var.databricks_host == "" ? 0 : 1
  display_name = "data-engineers"
}

resource "databricks_service_principal" "github_actions" {
  count          = var.databricks_host == "" || var.client_id == null ? 0 : 1
  application_id = var.client_id
  display_name   = "sp-datamasterv2-github-actions"
}

resource "databricks_entitlements" "github_actions" {
  count                = var.databricks_host == "" || var.client_id == null ? 0 : 1
  service_principal_id = databricks_service_principal.github_actions[0].id
  workspace_access     = true
}

resource "databricks_group" "data_scientists" {
  count        = var.databricks_host == "" ? 0 : 1
  display_name = "data-scientists"
}

resource "databricks_group" "data_analysts" {
  count        = var.databricks_host == "" ? 0 : 1
  display_name = "data-analysts"
}

resource "databricks_secret_scope" "main" {
  count = var.databricks_host == "" ? 0 : 1
  name  = "kv-${local.name_prefix}"
}

resource "databricks_cluster" "jobs" {
  count                   = var.databricks_host == "" ? 0 : 1
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
