import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, DoubleType, StringType, StructField, StructType


# Schema dos itens/produtos enviados pela Azure Function dentro do payload JSON.
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

# Schema completo do payload JSON gravado no Body do evento capturado pelo Event Hub.
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
    table_properties={
        "quality": "bronze",
        "source_system": "eventhub_capture",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
def bronze_eventhub_capture_raw():
    # Caminho ADLS onde o Event Hub Capture grava os arquivos AVRO.
    source_path = spark.conf.get("source_path")

    # Auto Loader lê continuamente os arquivos AVRO novos sem precisar controlar manualmente quais arquivos já foram processados.
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "avro")
        .load(source_path)
        .select(
            # Metadados originais do Event Hub Capture para rastreabilidade do evento.
            F.col("SequenceNumber").alias("sequence_number"),
            F.col("Offset").alias("eventhub_offset"),
            F.col("EnqueuedTimeUtc").cast("timestamp").alias("enqueued_time_utc"),
            F.col("SystemProperties").alias("system_properties"),
            F.col("Properties").alias("event_properties"),
            # Body contém o JSON enviado pela Azure Function.
            F.col("Body").cast("binary").cast("string").alias("body_json"),
            # Metadados do arquivo ajudam em auditoria, troubleshooting e reprocessamento.
            F.col("_metadata.file_path").alias("source_file"),
            F.col("_metadata.file_modification_time").alias("source_file_modification_time"),
            # Data/hora de ingestão no Bronze, independente da data original do evento.
            F.current_timestamp().alias("bronze_ingestion_time"),
            F.current_date().alias("ingestion_date")
        )
    )


@dlt.table(
    name="bronze_delivery_batches",
    comment="Parsed delivery generator batches from Event Hub Capture payload body.",
    table_properties={
        "quality": "bronze",
        "source_system": "azure_function_fake_generator",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
@dlt.expect("valid_json_payload", "batch_id IS NOT NULL")
def bronze_delivery_batches():
    # Lê a tabela Bronze raw como stream e interpreta o JSON do Body usando o schema definido acima.
    return (
        dlt.read_stream("bronze_eventhub_capture_raw")
        .withColumn("payload", F.from_json(F.col("body_json"), payload_schema))
        .select(
            # Mantém metadados do Event Hub e do arquivo para lineage.
            F.col("sequence_number"),
            F.col("eventhub_offset"),
            F.col("enqueued_time_utc"),
            F.col("source_file"),
            F.col("source_file_modification_time"),
            F.col("bronze_ingestion_time"),
            F.col("ingestion_date"),
            # Campos de controle gerados pela Function para identificar lote, origem e versão do contrato.
            F.col("payload.batch_id").alias("batch_id"),
            F.col("payload.ingestion_ts").cast("timestamp").alias("source_ingestion_ts"),
            # Data lógica do evento, útil para filtros e otimização mesmo sem particionamento físico.
            F.to_date(F.col("payload.ingestion_ts").cast("timestamp")).alias("event_date"),
            F.col("payload.source_system").alias("source_system"),
            F.col("payload.schema_version").alias("schema_version"),
            # Estrutura nested com clientes, restaurantes, drivers, items e orders que será explodida na Silver.
            F.col("payload.tables").alias("tables"),
            F.col("body_json")
        )
    )
