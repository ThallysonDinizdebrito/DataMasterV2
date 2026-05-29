import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DecimalType, StringType, StructField, StructType, TimestampType


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--subscription-id", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--secret-scope", required=True)
    parser.add_argument("--secret-key", required=True)
    parser.add_argument("--lookback-days", type=int, default=30)
    return parser.parse_args()


def request_json(url, method="GET", headers=None, payload=None, retries=3):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)

    for key, value in (headers or {}).items():
        request.add_header(key, value)

    if payload is not None:
        request.add_header("Content-Type", "application/json")

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


def get_access_token(tenant_id, client_id, client_secret):
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://management.azure.com/.default",
        "grant_type": "client_credentials",
    }).encode("utf-8")

    request = urllib.request.Request(token_url, data=data, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))

    return payload["access_token"]


def build_cost_query(start_date, end_date):
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
                    "name": "PreTaxCost",
                    "function": "Sum",
                }
            },
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


def parse_rows(response):
    columns = [column["name"] for column in response["properties"]["columns"]]
    rows = []

    for row in response["properties"].get("rows", []):
        item = dict(zip(columns, row))
        usage_date = str(item.get("UsageDate"))
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


def main():
    args = parse_args()
    client_secret = dbutils.secrets.get(scope=args.secret_scope, key=args.secret_key)
    token = get_access_token(args.tenant_id, args.client_id, client_secret)

    end_date = date.today()
    start_date = end_date - timedelta(days=args.lookback_days)
    scope = f"/subscriptions/{args.subscription_id}"
    url = f"https://management.azure.com{scope}/providers/Microsoft.CostManagement/query?api-version=2023-03-01"

    response = request_json(
        url=url,
        method="POST",
        headers={"Authorization": f"Bearer {token}"},
        payload=build_cost_query(start_date.isoformat(), end_date.isoformat()),
    )

    rows = parse_rows(response)
    schema = StructType([
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

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.{args.schema}")

    raw_df = spark.createDataFrame(rows, schema=schema)
    cost_df = (
        raw_df
        .withColumn("usage_date", F.col("usage_date").cast(DateType()))
        .withColumn("pretax_cost", F.col("pretax_cost").cast(DecimalType(18, 6)))
        .withColumn("subscription_id", F.lit(args.subscription_id))
        .withColumn("ingested_at", F.current_timestamp().cast(TimestampType()))
    )

    target_table = f"{args.catalog}.{args.schema}.azure_cost_by_resource_daily"
    cost_df.write.mode("overwrite").format("delta").saveAsTable(target_table)

    summary_df = (
        cost_df
        .groupBy("usage_date", "resource_group", "service_name", "currency")
        .agg(
            F.sum("pretax_cost").cast(DecimalType(18, 6)).alias("total_cost"),
            F.countDistinct("resource_id").alias("resource_count"),
            F.current_timestamp().alias("updated_at"),
        )
    )

    summary_table = f"{args.catalog}.{args.schema}.azure_cost_summary_daily"
    summary_df.write.mode("overwrite").format("delta").saveAsTable(summary_table)

    print(f"Wrote {cost_df.count()} rows to {target_table}")
    print(f"Wrote {summary_df.count()} rows to {summary_table}")


if __name__ == "__main__":
    main()
