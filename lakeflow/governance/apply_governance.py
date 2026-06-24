# Databricks notebook source
from pyspark.sql import functions as F

# COMMAND ----------

dbutils.widgets.text("catalog", "delivery_datamaster")
dbutils.widgets.text("schema", "default")
dbutils.widgets.text("governance_schema", "governance")
dbutils.widgets.text("data_engineer_group", "data-engineers")
dbutils.widgets.text("data_analyst_group", "data-analysts")
dbutils.widgets.text("data_scientist_group", "data-scientists")

catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")
governance_schema = dbutils.widgets.get("governance_schema")
data_engineer_group = dbutils.widgets.get("data_engineer_group")
data_analyst_group = dbutils.widgets.get("data_analyst_group")
data_scientist_group = dbutils.widgets.get("data_scientist_group")

source_schema = f"`{catalog}`.`{schema_name}`"
gov_schema = f"`{catalog}`.`{governance_schema}`"

print(f"catalog = {catalog}")
print(f"source_schema = {schema_name}")
print(f"governance_schema = {governance_schema}")

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {gov_schema}")
spark.sql(f"ALTER SCHEMA {gov_schema} SET TAGS ('layer' = 'governance', 'domain' = 'delivery', 'contains_masked_views' = 'true')")

# COMMAND ----------

table_tags = {
    "silver_clientes": {"layer": "silver", "classification": "restricted", "contains_pii": "true", "domain": "customer"},
    "silver_restaurantes": {"layer": "silver", "classification": "confidential", "contains_pii": "true", "domain": "restaurant"},
    "silver_drivers": {"layer": "silver", "classification": "restricted", "contains_pii": "true", "domain": "driver"},
    "silver_orders": {"layer": "silver", "classification": "internal", "contains_financial": "true", "domain": "order"},
    "silver_order_items": {"layer": "silver", "classification": "internal", "contains_financial": "true", "domain": "order"},
    "gold_daily_delivery_kpis": {"layer": "gold", "classification": "business", "contains_pii": "false", "domain": "analytics"},
    "gold_restaurant_performance": {"layer": "gold", "classification": "business", "contains_pii": "false", "domain": "analytics"},
    "gold_item_category_metrics": {"layer": "gold", "classification": "business", "contains_pii": "false", "domain": "analytics"},
}

column_tags = {
    "silver_clientes": {"nome": "PII", "endereco": "PII", "cpf": "PII_HIGH"},
    "silver_restaurantes": {"endereco": "PII", "cnpj": "SENSITIVE_ID"},
    "silver_drivers": {"nome": "PII", "endereco": "PII", "placa": "SENSITIVE_ID"},
    "silver_orders": {"valor_total": "FINANCIAL", "client_id": "BUSINESS_KEY", "driver_id": "BUSINESS_KEY"},
    "silver_order_items": {"preco": "FINANCIAL", "valor_total_item": "FINANCIAL"},
}

for table_name, tags in table_tags.items():
    tag_sql = ", ".join([f"'{k}' = '{v}'" for k, v in tags.items()])
    spark.sql(f"ALTER TABLE {source_schema}.`{table_name}` SET TAGS ({tag_sql})")

for table_name, cols in column_tags.items():
    for column_name, classification in cols.items():
        spark.sql(f"ALTER TABLE {source_schema}.`{table_name}` ALTER COLUMN `{column_name}` SET TAGS ('classification' = '{classification}')")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {gov_schema}.`vw_clientes_analyst` AS
SELECT
  client_id,
  concat(substr(nome, 1, 1), '***') AS nome,
  concat('***', substr(cpf, -4)) AS cpf_mascarado,
  tipo_pagamento,
  created_at
FROM {source_schema}.`silver_clientes`
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {gov_schema}.`vw_drivers_analyst` AS
SELECT
  driver_id,
  concat(substr(nome, 1, 1), '***') AS nome,
  veiculo,
  concat('***-', substr(placa, -4)) AS placa_mascarada,
  created_at
FROM {source_schema}.`silver_drivers`
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {gov_schema}.`vw_orders_analytics` AS
SELECT
  order_id,
  restaurant_id,
  quantidade_total,
  valor_total,
  tipo_pagamento,
  order_date,
  order_year,
  order_month,
  order_day,
  order_hour,
  amount_category
FROM {source_schema}.`silver_orders`
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {gov_schema}.`vw_gold_delivery_dashboard` AS
SELECT * FROM {source_schema}.`gold_daily_delivery_kpis`
""")

# COMMAND ----------
# Configurar permissões granulares por camada e views

# Listar tabelas e aplicar permissões dinamicamente
bronze_tables = spark.sql(f"SHOW TABLES FROM {source_schema}").filter(F.col("tableName").like("bronze_%")).select("tableName").rdd.flatMap(lambda x: x).collect()
silver_tables = spark.sql(f"SHOW TABLES FROM {source_schema}").filter(F.col("tableName").like("silver_%")).select("tableName").rdd.flatMap(lambda x: x).collect()
gold_tables = spark.sql(f"SHOW TABLES FROM {source_schema}").filter(F.col("tableName").like("gold_%")).select("tableName").rdd.flatMap(lambda x: x).collect()

# Permissões para tabelas Bronze (raw data) - streaming tables usam MODIFY em vez de INSERT/UPDATE/DELETE
for table in bronze_tables:
    spark.sql(f"GRANT SELECT, MODIFY ON TABLE {source_schema}.`{table}` TO `{data_engineer_group}`")
    spark.sql(f"GRANT SELECT ON TABLE {source_schema}.`{table}` TO `{data_scientist_group}`")
    spark.sql(f"GRANT SELECT ON TABLE {source_schema}.`{table}` TO `{data_analyst_group}`")

# Permissões para tabelas Silver (processed) - streaming tables usam MODIFY em vez de INSERT/UPDATE/DELETE/CREATE
for table in silver_tables:
    spark.sql(f"GRANT SELECT, MODIFY ON TABLE {source_schema}.`{table}` TO `{data_engineer_group}`")
    spark.sql(f"GRANT SELECT ON TABLE {source_schema}.`{table}` TO `{data_scientist_group}`")
    spark.sql(f"GRANT SELECT ON TABLE {source_schema}.`{table}` TO `{data_analyst_group}`")

# Permissões para tabelas Gold (curated) - materialized views não suportam CREATE VIEW
for table in gold_tables:
    spark.sql(f"GRANT SELECT ON TABLE {source_schema}.`{table}` TO `{data_engineer_group}`")
    spark.sql(f"GRANT SELECT ON TABLE {source_schema}.`{table}` TO `{data_scientist_group}`")
    spark.sql(f"GRANT SELECT ON TABLE {source_schema}.`{table}` TO `{data_analyst_group}`")

# Permissões para Views Governance (mascaradas - todos podem ler)
spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_clientes_analyst TO `{data_engineer_group}`")
spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_clientes_analyst TO `{data_scientist_group}`")
spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_clientes_analyst TO `{data_analyst_group}`")

spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_drivers_analyst TO `{data_engineer_group}`")
spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_drivers_analyst TO `{data_scientist_group}`")
spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_drivers_analyst TO `{data_analyst_group}`")

spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_orders_analytics TO `{data_engineer_group}`")
spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_orders_analytics TO `{data_scientist_group}`")
spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_orders_analytics TO `{data_analyst_group}`")

spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_gold_delivery_dashboard TO `{data_engineer_group}`")
spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_gold_delivery_dashboard TO `{data_scientist_group}`")
spark.sql(f"GRANT SELECT ON VIEW {gov_schema}.vw_gold_delivery_dashboard TO `{data_analyst_group}`")

# COMMAND ----------

results = [
    ("schema", f"{catalog}.{governance_schema}", "CREATED_OR_UPDATED"),
    ("tags", f"{catalog}.{schema_name}", "APPLIED"),
    ("views", f"{catalog}.{governance_schema}", "CREATED_OR_REPLACED"),
    ("grants", "data_engineers/data_analysts/data_scientists", "APPLIED"),
]

display(spark.createDataFrame(results, ["object_type", "object_name", "status"]).withColumn("finished_at", F.current_timestamp()))

