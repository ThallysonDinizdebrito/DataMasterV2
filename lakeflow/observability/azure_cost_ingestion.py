# Databricks notebook source
# Este notebook consulta a Azure Cost Management API e grava tabelas Delta no Unity Catalog.
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DecimalType, StringType, StructField, StructType

# COMMAND ----------

# Widgets são parâmetros do notebook. O Databricks Job envia esses valores pelo bundle.
dbutils.widgets.text("tenant_id", "1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d")
dbutils.widgets.text("client_id", "7da295f3-e9d6-4a72-9f47-8e3bde7fcc92")
dbutils.widgets.text("subscription_id", "97eb265c-59ce-4122-bbe4-98f0d58d9208")
dbutils.widgets.text("catalog", "delivery_datamaster")
dbutils.widgets.text("schema", "observability")
dbutils.widgets.text("secret_scope", "dmv2-dev")
dbutils.widgets.text("secret_key", "azure-client-secret")
dbutils.widgets.text("lookback_days", "30")

# Leitura dos parâmetros recebidos pelo job.
tenant_id = dbutils.widgets.get("tenant_id")
client_id = dbutils.widgets.get("client_id")
subscription_id = dbutils.widgets.get("subscription_id")
catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")
secret_scope = dbutils.widgets.get("secret_scope")
secret_key = dbutils.widgets.get("secret_key")
lookback_days = int(dbutils.widgets.get("lookback_days"))

# Nomes finais das tabelas que serão criadas ou sobrescritas no Unity Catalog.
cost_detail_table = f"{schema_name}.azure_cost_by_resource_daily"
cost_summary_table = f"{schema_name}.azure_cost_summary_daily"

# COMMAND ----------


def request_json(url, method="GET", headers=None, payload=None, retries=3):
    # Converte o payload Python para JSON quando a chamada HTTP precisa enviar corpo.
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)

    # Adiciona headers como Authorization e Content-Type.
    for key, value in (headers or {}).items():
        request.add_header(key, value)

    if payload is not None:
        request.add_header("Content-Type", "application/json")

    # Tenta novamente em erros transitórios comuns de API.
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {error.code} calling {url}: {details}") from error

    raise RuntimeError(f"Failed calling {url}")

# COMMAND ----------


def get_access_token(tenant_id, client_id, client_secret):
    # Endpoint OAuth 2.0 do Entra ID para gerar token de aplicação.
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    # Client credentials: usa client_id e client_secret do Service Principal.
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://management.azure.com/.default",
        "grant_type": "client_credentials",
    }).encode("utf-8")

    request = urllib.request.Request(token_url, data=data, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            "Falha ao autenticar no Entra ID para consultar custos Azure. "
            "Valide tenant_id, client_id e o valor da secret Databricks "
            f"'{secret_scope}/{secret_key}'. "
            f"HTTP {error.code}: {details}"
        ) from error

    return payload["access_token"]

# COMMAND ----------


def build_cost_query(start_date, end_date):
    # Monta a consulta da Azure Cost Management API.
    # ActualCost retorna custo real já acumulado no período.
    return {
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {
            "from": start_date,
            "to": end_date,
        },
        "dataset": {
            "granularity": "Daily",
            "aggregation": {
                "totalCost": {
                    # PreTaxCost é o custo antes de impostos.
                    "name": "PreTaxCost",
                    "function": "Sum",
                }
            },
            # Agrupamentos que permitem montar dashboard por recurso, serviço e resource group.
            "grouping": [
                {"type": "Dimension", "name": "ResourceId"},
                {"type": "Dimension", "name": "ResourceType"},
                {"type": "Dimension", "name": "ResourceGroupName"},
                {"type": "Dimension", "name": "ServiceName"},
                {"type": "Dimension", "name": "MeterCategory"},
                {"type": "Dimension", "name": "MeterSubcategory"},
            ],
        },
    }

# COMMAND ----------


def parse_rows(response):
    # A API retorna colunas e linhas separadas; aqui reconstruímos cada linha como dict.
    columns = [column["name"] for column in response["properties"]["columns"]]
    rows = []

    for row in response["properties"].get("rows", []):
        item = dict(zip(columns, row))
        usage_date = str(item.get("UsageDate"))

        # UsageDate vem como yyyyMMdd. Convertemos para yyyy-MM-dd para facilitar cast no Spark.
        rows.append({
            "usage_date": f"{usage_date[0:4]}-{usage_date[4:6]}-{usage_date[6:8]}",
            "pretax_cost": str(item.get("PreTaxCost", "0")),
            "resource_id": item.get("ResourceId"),
            "resource_type": item.get("ResourceType"),
            "resource_group": item.get("ResourceGroupName"),
            "service_name": item.get("ServiceName"),
            "meter_category": item.get("MeterCategory"),
            "meter_subcategory": item.get("MeterSubcategory"),
            "currency": item.get("Currency"),
        })

    return rows

# COMMAND ----------

# Recupera o client secret do Service Principal dentro do Databricks Secret Scope.
client_secret = dbutils.secrets.get(scope=secret_scope, key=secret_key)

# Gera um token Bearer para chamar a Azure Management API.
access_token = get_access_token(tenant_id, client_id, client_secret)

# Define a janela de custo: de hoje menos lookback_days até hoje.
end_date = date.today()
start_date = end_date - timedelta(days=lookback_days)

# Endpoint de consulta de custos no escopo da subscription.
cost_url = (
    f"https://management.azure.com/subscriptions/{subscription_id}"
    "/providers/Microsoft.CostManagement/query?api-version=2023-03-01"
)

# Chama a Azure Cost Management API com o token e o payload de agrupamento.
cost_response = request_json(
    url=cost_url,
    method="POST",
    headers={"Authorization": f"Bearer {access_token}"},
    payload=build_cost_query(start_date.isoformat(), end_date.isoformat()),
)

# COMMAND ----------

# Transforma a resposta JSON da API em lista de registros.
cost_rows = parse_rows(cost_response)

# Schema inicial em string para evitar erro de inferência quando algum campo vier nulo.
cost_schema = StructType([
    StructField("usage_date", StringType()),
    StructField("pretax_cost", StringType()),
    StructField("resource_id", StringType()),
    StructField("resource_type", StringType()),
    StructField("resource_group", StringType()),
    StructField("service_name", StringType()),
    StructField("meter_category", StringType()),
    StructField("meter_subcategory", StringType()),
    StructField("currency", StringType()),
])

# Cria DataFrame Spark a partir dos registros retornados pela API.
raw_cost_df = spark.createDataFrame(cost_rows, schema=cost_schema)

# Aplica tipagem final e adiciona metadados de auditoria.
cost_df = (
    raw_cost_df
    .withColumn("usage_date", F.col("usage_date").cast(DateType()))
    .withColumn("pretax_cost", F.col("pretax_cost").cast(DecimalType(18, 6)))
    .withColumn("subscription_id", F.lit(subscription_id))
    .withColumn("ingested_at", F.current_timestamp())
)

# Exibe a tabela detalhada no notebook para facilitar validação visual.
display(cost_df)

# COMMAND ----------

# Seleciona explicitamente o catálogo Unity Catalog antes de criar schema e tabelas.
spark.sql(f"USE CATALOG {catalog}")

# Garante que o schema de observabilidade exista dentro do catálogo selecionado.
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

# Grava a tabela detalhada de custo por recurso.
(
    cost_df.write
    .mode("overwrite")
    .format("delta")
    .saveAsTable(cost_detail_table)
)

# COMMAND ----------

# Agrega os custos para uma tabela resumo mais simples de usar em dashboard.
cost_summary_df = (
    cost_df
    .groupBy("usage_date", "resource_group", "service_name", "currency")
    .agg(
        F.sum("pretax_cost").cast(DecimalType(18, 6)).alias("total_cost"),
        F.countDistinct("resource_id").alias("resource_count"),
        F.current_timestamp().alias("updated_at"),
    )
)

# Grava a tabela resumida por dia, resource group e serviço.
(
    cost_summary_df.write
    .mode("overwrite")
    .format("delta")
    .saveAsTable(cost_summary_table)
)

# Exibe o resumo ordenado por data mais recente e maior custo.
display(cost_summary_df.orderBy(F.col("usage_date").desc(), F.col("total_cost").desc()))

# COMMAND ----------

# Contagens finais para log do job.
cost_rows_count = cost_df.count()
summary_rows_count = cost_summary_df.count()

print(f"Rows written to {cost_detail_table}: {cost_rows_count}")
print(f"Rows written to {cost_summary_table}: {summary_rows_count}")
