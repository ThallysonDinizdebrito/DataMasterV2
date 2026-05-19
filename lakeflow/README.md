# DataMasterV2 Lakeflow

Pipeline Databricks Lakeflow/DLT para processar dados fake de delivery capturados pelo Azure Event Hub Capture.

## Fonte

```text
abfss://source@stdmv2devvxc02.dfs.core.windows.net/eventhub-capture
```

A origem contém arquivos AVRO gerados automaticamente pelo Event Hub Capture.

## Arquitetura

```text
Event Hub Capture AVRO
  -> bronze_eventhub_capture_raw
  -> bronze_delivery_batches
  -> silver_clientes
  -> silver_restaurantes
  -> silver_drivers
  -> silver_items
  -> silver_orders
  -> silver_order_items
  -> gold_daily_delivery_kpis
  -> gold_restaurant_performance
  -> gold_item_category_metrics
```

## Deploy local

```powershell
databricks bundle validate -t dev

databricks bundle deploy -t dev
```

## Deploy via GitHub Actions

O workflow `.github/workflows/deploy-dev.yml` executa o deploy do bundle após o Terraform.

## Pré-requisitos

O Service Principal usado no GitHub Actions precisa ter acesso ao Databricks Workspace e permissão para criar/atualizar pipelines Lakeflow/DLT.
