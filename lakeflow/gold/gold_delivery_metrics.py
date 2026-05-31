import dlt
from pyspark.sql import functions as F


@dlt.table(
    name="gold_daily_delivery_kpis",
    comment="Daily delivery KPIs for dashboard and operational monitoring.",
    partition_cols=["metric_date"],
    cluster_by=["metric_date"],
    table_properties={
        "quality": "gold",
        "domain": "delivery_analytics",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
@dlt.expect_or_fail("non_negative_orders", "total_orders >= 0")
@dlt.expect_or_fail("non_negative_revenue", "total_revenue >= 0")
def gold_daily_delivery_kpis():
    orders = dlt.read("silver_orders")

    return (
        orders
        .groupBy(
            F.to_date("created_at").alias("metric_date"),
            F.col("tipo_pagamento")
        )
        .agg(
            F.countDistinct("order_id").alias("total_orders"),
            F.countDistinct("client_id").alias("unique_clients"),
            F.countDistinct("merchant_id").alias("unique_restaurants"),
            F.countDistinct("driver_id").alias("unique_drivers"),
            F.sum("quantidade_total").alias("total_items"),
            F.sum("valor_total").cast("decimal(18,2)").alias("total_revenue"),
            F.avg("valor_total").cast("decimal(18,2)").alias("avg_order_value"),
            F.current_timestamp().alias("gold_processed_at")
        )
    )


@dlt.table(
    name="gold_restaurant_performance",
    comment="Restaurant performance metrics based on generated delivery orders.",
    cluster_by=["restaurant_id"],
    table_properties={
        "quality": "gold",
        "domain": "restaurant_analytics",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
@dlt.expect_or_fail("positive_restaurant_orders", "total_orders > 0")
def gold_restaurant_performance():
    orders = dlt.read("silver_orders")
    restaurants = dlt.read("silver_restaurantes")

    return (
        orders.alias("o")
        .join(restaurants.alias("r"), F.col("o.merchant_id") == F.col("r.merchant_id"), "left")
        .groupBy(
            F.to_date(F.col("o.created_at")).alias("order_date"),
            F.col("o.merchant_id").alias("restaurant_id"),
            F.col("r.nome").alias("restaurant_name")
        )
        .agg(
            F.countDistinct("o.order_id").alias("total_orders"),
            F.countDistinct("o.client_id").alias("unique_clients"),
            F.sum("o.valor_total").cast("decimal(18,2)").alias("total_revenue"),
            F.avg("o.valor_total").cast("decimal(18,2)").alias("avg_order_value"),
            F.current_timestamp().alias("gold_processed_at")
        )
    )


@dlt.table(
    name="gold_item_category_metrics",
    comment="Item category metrics calculated from exploded order items.",
    table_properties={
        "quality": "gold",
        "domain": "menu_analytics",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
@dlt.expect_or_fail("positive_quantity", "total_quantity > 0")
def gold_item_category_metrics():
    order_items = dlt.read("silver_order_items")

    return (
        order_items
        .groupBy("categoria")
        .agg(
            F.countDistinct("order_id").alias("orders_with_category"),
            F.countDistinct("item_id").alias("unique_items"),
            F.sum("quantidade").alias("total_quantity"),
            F.sum("valor_total_item").cast("decimal(18,2)").alias("total_revenue"),
            F.avg("preco").cast("decimal(18,2)").alias("avg_item_price"),
            F.current_timestamp().alias("gold_processed_at")
        )
    )
