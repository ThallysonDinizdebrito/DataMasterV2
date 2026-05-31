import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, DoubleType, StringType, StructField, StructType


item_schema = StructType([
    StructField("ItemID", StringType()),
    StructField("nome", StringType()),
    StructField("categoria", StringType()),
    StructField("preco", DoubleType()),
    StructField("MerchantID", StringType()),
    StructField("quantidade", DoubleType()),
    StructField("valor_total_item", DoubleType()),
    StructField("created_at", StringType())
])

payload_schema = StructType([
    StructField("batch_id", StringType()),
    StructField("ingestion_ts", StringType()),
    StructField("source_system", StringType()),
    StructField("schema_version", StringType()),
    StructField("tables", StructType([
        StructField("clientes", ArrayType(StructType([
            StructField("ClientID", StringType()),
            StructField("nome", StringType()),
            StructField("endereco", StringType()),
            StructField("CPF", StringType()),
            StructField("tipo_pagamento", StringType()),
            StructField("created_at", StringType())
        ]))),
        StructField("restaurantes", ArrayType(StructType([
            StructField("MerchantID", StringType()),
            StructField("nome", StringType()),
            StructField("endereco", StringType()),
            StructField("CNPJ", StringType()),
            StructField("created_at", StringType())
        ]))),
        StructField("items", ArrayType(item_schema)),
        StructField("drivers", ArrayType(StructType([
            StructField("DriversID", StringType()),
            StructField("nome", StringType()),
            StructField("endereco", StringType()),
            StructField("veiculo", StringType()),
            StructField("placa", StringType()),
            StructField("created_at", StringType())
        ]))),
        StructField("orders", ArrayType(StructType([
            StructField("PedidoID", StringType()),
            StructField("ClientID", StringType()),
            StructField("MerchantID", StringType()),
            StructField("DriversID", StringType()),
            StructField("Produtos", ArrayType(item_schema)),
            StructField("quantidade_total", DoubleType()),
            StructField("valor_total", DoubleType()),
            StructField("tipo_pagamento", StringType()),
            StructField("created_at", StringType())
        ])))
    ]))
])


@dlt.table(
    name="bronze_eventhub_capture_raw",
    comment="Raw AVRO records captured by Azure Event Hub Capture from delivery fake data generator.",
    partition_cols=["ingestion_date"],
    table_properties={
        "quality": "bronze",
        "source_system": "eventhub_capture",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
def bronze_eventhub_capture_raw():
    source_path = spark.conf.get("source_path")

    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "avro")
        .load(source_path)
        .select(
            F.col("SequenceNumber").alias("sequence_number"),
            F.col("Offset").alias("eventhub_offset"),
            F.col("EnqueuedTimeUtc").cast("timestamp").alias("enqueued_time_utc"),
            F.col("SystemProperties").alias("system_properties"),
            F.col("Properties").alias("event_properties"),
            F.col("Body").cast("binary").cast("string").alias("body_json"),
            F.col("_metadata.file_path").alias("source_file"),
            F.col("_metadata.file_modification_time").alias("source_file_modification_time"),
            F.current_timestamp().alias("bronze_ingestion_time"),
            F.current_date().alias("ingestion_date")
        )
    )


@dlt.table(
    name="bronze_delivery_batches",
    comment="Parsed delivery generator batches from Event Hub Capture payload body.",
    partition_cols=["event_date"],
    table_properties={
        "quality": "bronze",
        "source_system": "azure_function_fake_generator",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
@dlt.expect("valid_json_payload", "batch_id IS NOT NULL")
def bronze_delivery_batches():
    return (
        dlt.read_stream("bronze_eventhub_capture_raw")
        .withColumn("payload", F.from_json(F.col("body_json"), payload_schema))
        .select(
            F.col("sequence_number"),
            F.col("eventhub_offset"),
            F.col("enqueued_time_utc"),
            F.col("source_file"),
            F.col("source_file_modification_time"),
            F.col("bronze_ingestion_time"),
            F.col("ingestion_date"),
            F.col("payload.batch_id").alias("batch_id"),
            F.col("payload.ingestion_ts").cast("timestamp").alias("source_ingestion_ts"),
            F.to_date(F.col("payload.ingestion_ts").cast("timestamp")).alias("event_date"),
            F.col("payload.source_system").alias("source_system"),
            F.col("payload.schema_version").alias("schema_version"),
            F.col("payload.tables").alias("tables"),
            F.col("body_json")
        )
    )
