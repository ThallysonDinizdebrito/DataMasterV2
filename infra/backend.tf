terraform {
  backend "azurerm" {
    resource_group_name  = "rg-datamasterv2-tfstate-dev"
    storage_account_name = "stdmv2tfstatedev"
    container_name       = "tfstate"
    key                  = "datamasterv2-dev.tfstate"
  }
}
