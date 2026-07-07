# Grupos account-level criados manualmente no Account Console
# data-engineers, data-scientists, data-analysts

# Secret scope legado (Databricks-managed)
resource "databricks_secret_scope" "main" {
  count = var.databricks_host != "" ? 1 : 0
  name  = "kv-${local.name_prefix}"
}
