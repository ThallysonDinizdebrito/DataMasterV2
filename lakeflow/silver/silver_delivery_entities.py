import dlt
from pyspark.sql import functions as F


@dlt.table(
    name="silver_clientes",
    comment="Cleaned client dimension extracted from delivery generator batches.",
    table_properties={"quality": "silver", "entity": "clientes"}
)
@dlt.expect_or_drop("valid_client_id", "client_id IS NOT NULL")
@dlt.expect_or_drop("valid_cpf", "cpf IS NOT NULL")
def silver_clientes():
    return (
        dlt.read_stream("bronze_delivery_batches")
        .select("batch_id", F.explode_outer("tables.clientes").alias("cliente"))
        .select(
            F.col("batch_id"),
            F.col("cliente.ClientID").cast("string").alias("client_id"),
            F.col("cliente.nome").cast("string").alias("nome"),
            F.col("cliente.endereco").cast("string").alias("endereco"),
            F.col("cliente.CPF").cast("string").alias("cpf"),
            F.col("cliente.tipo_pagamento").cast("string").alias("tipo_pagamento"),
            F.col("cliente.created_at").cast("timestamp").alias("created_at"),
            F.current_timestamp().alias("silver_processed_at")
        )
        .dropDuplicates(["client_id"])
    )


@dlt.table(
    name="silver_restaurantes",
    comment="Cleaned restaurant dimension extracted from delivery generator batches.",
    table_properties={"quality": "silver", "entity": "restaurantes"}
)
@dlt.expect_or_drop("valid_merchant_id", "merchant_id IS NOT NULL")
@dlt.expect_or_drop("valid_cnpj", "cnpj IS NOT NULL")
def silver_restaurantes():
    return (
        dlt.read_stream("bronze_delivery_batches")
        .select("batch_id", F.explode_outer("tables.restaurantes").alias("restaurante"))
        .select(
            F.col("batch_id"),
            F.col("restaurante.MerchantID").cast("string").alias("merchant_id"),
            F.col("restaurante.nome").cast("string").alias("nome"),
            F.col("restaurante.endereco").cast("string").alias("endereco"),
            F.col("restaurante.CNPJ").cast("string").alias("cnpj"),
            F.col("restaurante.created_at").cast("timestamp").alias("created_at"),
            F.current_timestamp().alias("silver_processed_at")
        )
        .dropDuplicates(["merchant_id"])
    )


@dlt.table(
    name="silver_drivers",
    comment="Cleaned driver dimension extracted from delivery generator batches.",
    table_properties={"quality": "silver", "entity": "drivers"}
)
@dlt.expect_or_drop("valid_driver_id", "driver_id IS NOT NULL")
@dlt.expect_or_drop("valid_plate", "placa IS NOT NULL")
def silver_drivers():
    return (
        dlt.read_stream("bronze_delivery_batches")
        .select("batch_id", F.explode_outer("tables.drivers").alias("driver"))
        .select(
            F.col("batch_id"),
            F.col("driver.DriversID").cast("string").alias("driver_id"),
            F.col("driver.nome").cast("string").alias("nome"),
            F.col("driver.endereco").cast("string").alias("endereco"),
            F.col("driver.veiculo").cast("string").alias("veiculo"),
            F.col("driver.placa").cast("string").alias("placa"),
            F.col("driver.created_at").cast("timestamp").alias("created_at"),
            F.current_timestamp().alias("silver_processed_at")
        )
        .dropDuplicates(["driver_id"])
    )


@dlt.table(
    name="silver_items",
    comment="Cleaned menu item dimension extracted from delivery generator batches.",
    table_properties={"quality": "silver", "entity": "items"}
)
@dlt.expect_or_drop("valid_item_id", "item_id IS NOT NULL")
@dlt.expect_or_drop("valid_price", "preco > 0")
def silver_items():
    return (
        dlt.read_stream("bronze_delivery_batches")
        .select("batch_id", F.explode_outer("tables.items").alias("item"))
        .select(
            F.col("batch_id"),
            F.col("item.ItemID").cast("string").alias("item_id"),
            F.col("item.nome").cast("string").alias("nome"),
            F.col("item.categoria").cast("string").alias("categoria"),
            F.col("item.preco").cast("decimal(10,2)").alias("preco"),
            F.col("item.MerchantID").cast("string").alias("merchant_id"),
            F.col("item.created_at").cast("timestamp").alias("created_at"),
            F.current_timestamp().alias("silver_processed_at")
        )
        .dropDuplicates(["item_id"])
    )


@dlt.table(
    name="silver_orders",
    comment="Cleaned order fact extracted from delivery generator batches.",
    table_properties={"quality": "silver", "entity": "orders", "pipelines.autoOptimize.zOrderCols": "order_id,created_at"}
)
@dlt.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
@dlt.expect_or_drop("valid_order_amount", "valor_total > 0")
@dlt.expect_or_drop("valid_total_quantity", "quantidade_total > 0")
def silver_orders():
    return (
        dlt.read_stream("bronze_delivery_batches")
        .select("batch_id", F.explode_outer("tables.orders").alias("order"))
        .select(
            F.col("batch_id"),
            F.col("order.PedidoID").cast("string").alias("order_id"),
            F.col("order.ClientID").cast("string").alias("client_id"),
            F.col("order.MerchantID").cast("string").alias("merchant_id"),
            F.col("order.DriversID").cast("string").alias("driver_id"),
            F.col("order.quantidade_total").cast("int").alias("quantidade_total"),
            F.col("order.valor_total").cast("decimal(10,2)").alias("valor_total"),
            F.col("order.tipo_pagamento").cast("string").alias("tipo_pagamento"),
            F.col("order.created_at").cast("timestamp").alias("created_at"),
            F.col("order.Produtos").alias("produtos"),
            F.year(F.col("order.created_at").cast("timestamp")).alias("order_year"),
            F.month(F.col("order.created_at").cast("timestamp")).alias("order_month"),
            F.dayofmonth(F.col("order.created_at").cast("timestamp")).alias("order_day"),
            F.hour(F.col("order.created_at").cast("timestamp")).alias("order_hour"),
            F.when(F.col("order.valor_total") >= 200, "High")
             .when(F.col("order.valor_total") >= 100, "Medium")
             .otherwise("Low")
             .alias("amount_category"),
            F.current_timestamp().alias("silver_processed_at")
        )
    )


@dlt.table(
    name="silver_order_items",
    comment="Exploded order item fact extracted from nested order products.",
    table_properties={"quality": "silver", "entity": "order_items"}
)
@dlt.expect_or_drop("valid_order_item", "order_id IS NOT NULL AND item_id IS NOT NULL")
@dlt.expect_or_drop("valid_item_quantity", "quantidade > 0")
def silver_order_items():
    return (
        dlt.read_stream("silver_orders")
        .select("batch_id", "order_id", F.explode_outer("produtos").alias("produto"))
        .select(
            F.col("batch_id"),
            F.col("order_id"),
            F.col("produto.ItemID").cast("string").alias("item_id"),
            F.col("produto.nome").cast("string").alias("nome"),
            F.col("produto.categoria").cast("string").alias("categoria"),
            F.col("produto.preco").cast("decimal(10,2)").alias("preco"),
            F.col("produto.quantidade").cast("int").alias("quantidade"),
            F.col("produto.valor_total_item").cast("decimal(10,2)").alias("valor_total_item"),
            F.col("produto.created_at").cast("timestamp").alias("created_at"),
            F.current_timestamp().alias("silver_processed_at")
        )
    )
