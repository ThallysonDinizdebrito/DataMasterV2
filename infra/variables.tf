variable "project_name" {
  description = "Project name used for tagging and naming."
  type        = string
  default     = "DataMasterV2"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be dev or prod."
  }
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "brazilsouth"
}

variable "subscription_id" {
  description = "Azure subscription ID."
  type        = string
}

variable "tenant_id" {
  description = "Azure tenant ID."
  type        = string
}

variable "client_id" {
  description = "Azure service principal client ID."
  type        = string
  sensitive   = true
  default     = null
}

variable "client_secret" {
  description = "Azure service principal client secret."
  type        = string
  sensitive   = true
  default     = null
}

variable "databricks_host" {
  description = "Databricks workspace host. Filled after workspace creation."
  type        = string
  default     = ""
}

variable "databricks_sku" {
  description = "Databricks workspace SKU."
  type        = string
  default     = "premium"
}

variable "no_public_ip" {
  description = "Disable public IP on Databricks cluster nodes."
  type        = bool
  default     = true
}

variable "enable_private_endpoints" {
  description = "Enable private endpoints for Databricks. Disabled by default to control cost."
  type        = bool
  default     = false
}

variable "enable_unity_catalog" {
  description = "Enable Unity Catalog resources after metastore is available."
  type        = bool
  default     = false
}

variable "unity_catalog_metastore_id" {
  description = "Unity Catalog metastore ID. Required when enable_unity_catalog is true."
  type        = string
  default     = ""
}

variable "ops_email" {
  description = "Operations email for Azure Monitor action group."
  type        = string
  default     = "ops@example.com"
}

variable "function_schedule" {
  description = "Azure Function timer schedule."
  type        = string
  default     = "0 */1 * * * *"
}

variable "enable_function_app" {
  description = "Enable Azure Function infrastructure. Requires App Service quota in the selected region."
  type        = bool
  default     = false
}

variable "function_location" {
  description = "Azure region used only for the Function App when the main region has App Service quota restrictions."
  type        = string
  default     = "westeurope"
}

# variable "eventhub_partition_count" {
#   description = "Number of partitions for the main delivery events Event Hub."
#   type        = number
#   default     = 2
# }

# variable "eventhub_message_retention_days" {
#   description = "Message retention in days for the main delivery events Event Hub."
#   type        = number
#   default     = 1
# }

# variable "eventhub_capture_interval_seconds" {
#   description = "Event Hub Capture interval in seconds."
#   type        = number
#   default     = 60
# }

# variable "eventhub_capture_size_limit_bytes" {
#   description = "Event Hub Capture file size limit in bytes."
#   type        = number
#   default     = 10485760
# }

variable "fake_num_clientes" {
  type    = number
  default = 1
}

variable "fake_num_restaurantes" {
  type    = number
  default = 1
}

variable "fake_num_drivers" {
  type    = number
  default = 1
}

variable "fake_num_items_per_restaurante" {
  type    = number
  default = 8
}

variable "fake_num_pedidos" {
  type    = number
  default = 8
}
