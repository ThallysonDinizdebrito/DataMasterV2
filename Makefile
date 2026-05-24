SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

PROJECT_NAME := DataMasterV2
ENV := dev
REPO := ThallysonDinizdebrito/DataMasterV2
WORKFLOW := Deploy Dev
LAKEFLOW_DIR := lakeflow
INFRA_DIR := infra
FUNCTION_PROJECT_PATH := azure_function/GeracaoData
PIPELINE_RESOURCE := delivery_eventhub_medallion_v2

.PHONY: help
help:
	@Write-Host "DataMasterV2 commands:"
	@Write-Host ""
	@Write-Host "Validation:"
	@Write-Host "  make validate              - Validate Terraform, Function syntax and Databricks bundle"
	@Write-Host "  make function-check        - Validate Azure Function Python syntax"
	@Write-Host ""
	@Write-Host "Terraform:"
	@Write-Host "  make tf-init               - Initialize Terraform"
	@Write-Host "  make tf-fmt                - Format Terraform files"
	@Write-Host "  make tf-validate           - Validate Terraform"
	@Write-Host "  make tf-plan               - Create Terraform plan"
	@Write-Host "  make tf-apply              - Apply Terraform changes"
	@Write-Host ""
	@Write-Host "Databricks:"
	@Write-Host "  make databricks-auth       - Validate Databricks authentication"
	@Write-Host "  make databricks-validate   - Validate Databricks bundle"
	@Write-Host "  make databricks-deploy     - Deploy Databricks bundle"
	@Write-Host "  make databricks-summary    - Show Databricks bundle summary"
	@Write-Host "  make databricks-run        - Start DLT pipeline from bundle"
	@Write-Host ""
	@Write-Host "GitHub Actions:"
	@Write-Host "  make secrets-list          - List GitHub Actions secrets"
	@Write-Host "  make action-run            - Trigger Deploy Dev workflow"
	@Write-Host "  make action-status         - List recent Deploy Dev workflow runs"
	@Write-Host ""
	@Write-Host "Local deploy:"
	@Write-Host "  make deploy-dev            - Run Terraform apply and Databricks deploy/run locally"

.PHONY: validate
validate: tf-fmt-check tf-validate function-check databricks-validate
	@Write-Host "Validating $(PROJECT_NAME)..."

.PHONY: tf-init
tf-init:
	terraform -chdir=$(INFRA_DIR) init

.PHONY: tf-fmt
tf-fmt:
	terraform -chdir=$(INFRA_DIR) fmt -recursive

.PHONY: tf-fmt-check
tf-fmt-check:
	terraform -chdir=$(INFRA_DIR) fmt -check -recursive

.PHONY: tf-validate
tf-validate:
	terraform -chdir=$(INFRA_DIR) validate

.PHONY: tf-plan
tf-plan:
	terraform -chdir=$(INFRA_DIR) plan -out=tfplan

.PHONY: tf-apply
tf-apply:
	terraform -chdir=$(INFRA_DIR) apply -auto-approve

.PHONY: function-check
function-check:
	python -m py_compile $(FUNCTION_PROJECT_PATH)/gerarFakeData/__init__.py

.PHONY: databricks-auth
databricks-auth:
	databricks current-user me

.PHONY: databricks-validate
databricks-validate:
	databricks bundle validate -t $(ENV) --config-file $(LAKEFLOW_DIR)/databricks.yml

.PHONY: databricks-deploy
databricks-deploy:
	databricks bundle deploy -t $(ENV) --config-file $(LAKEFLOW_DIR)/databricks.yml

.PHONY: databricks-summary
databricks-summary:
	databricks bundle summary -t $(ENV) --config-file $(LAKEFLOW_DIR)/databricks.yml

.PHONY: databricks-run
databricks-run:
	databricks bundle run $(PIPELINE_RESOURCE) -t $(ENV) --config-file $(LAKEFLOW_DIR)/databricks.yml

.PHONY: secrets-list
secrets-list:
	gh secret list --repo $(REPO)

.PHONY: action-run
action-run:
	gh workflow run "$(WORKFLOW)" --repo $(REPO) --ref $(ENV)

.PHONY: action-status
action-status:
	gh run list --repo $(REPO) --workflow "$(WORKFLOW)" --limit 5

.PHONY: deploy-dev
deploy-dev: tf-init tf-plan tf-apply databricks-validate databricks-deploy databricks-summary databricks-run
