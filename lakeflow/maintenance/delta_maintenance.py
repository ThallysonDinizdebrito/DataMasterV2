# Databricks notebook source
from pyspark.sql import functions as F

# COMMAND ----------

dbutils.widgets.text("catalog", "delivery_datamaster")
dbutils.widgets.text("schema", "default")
dbutils.widgets.text("retention_hours", "168")

catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")
retention_hours = int(dbutils.widgets.get("retention_hours"))

maintenance_tables = [
    "silver_orders",
    "silver_order_items",
    "gold_daily_delivery_kpis",
    "gold_restaurant_performance",
    "gold_item_category_metrics",
]

# COMMAND ----------

spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema_name}")

# COMMAND ----------

results = []

for table_name in maintenance_tables:
    full_table_name = f"{catalog}.{schema_name}.{table_name}"

    print(f"Running OPTIMIZE on {full_table_name}")
    spark.sql(f"OPTIMIZE {full_table_name}")

    print(f"Running VACUUM on {full_table_name} with retention {retention_hours} hours")
    spark.sql(f"VACUUM {full_table_name} RETAIN {retention_hours} HOURS")

    results.append((full_table_name, "OPTIMIZE_AND_VACUUM_COMPLETED"))

# COMMAND ----------

result_df = spark.createDataFrame(results, ["table_name", "status"]).withColumn("finished_at", F.current_timestamp())
display(result_df)
