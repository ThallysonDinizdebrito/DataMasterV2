SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

PROJECT_NAME := DataMasterV2
ENV := dev

.PHONY: help
help:
	@Write-Host "DataMasterV2 commands:"
	@Write-Host "  make validate       - Validate local project files"
	@Write-Host "  make tf-fmt         - Format Terraform files"
	@Write-Host "  make tf-validate    - Validate Terraform"

.PHONY: validate
validate:
	@Write-Host "Validating $(PROJECT_NAME)..."
	@terraform -chdir=infra fmt -check -recursive
	@terraform -chdir=infra validate

.PHONY: tf-fmt
tf-fmt:
	terraform -chdir=infra fmt -recursive

.PHONY: tf-validate
tf-validate:
	terraform -chdir=infra validate
