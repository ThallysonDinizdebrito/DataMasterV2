locals {
  normalized_project = lower(replace(var.project_name, "_", "-"))
  name_prefix        = "dmv2-${var.environment}"
  safe_prefix        = lower(replace(local.name_prefix, "-", ""))

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Domain      = "Delivery"
  }

  containers = toset([
    "source",
    "rejeitados"
  ])
}
