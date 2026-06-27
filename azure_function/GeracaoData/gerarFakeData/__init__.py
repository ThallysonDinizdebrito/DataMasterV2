import json
import logging
import os
import random
import string
from datetime import datetime, timezone

import azure.functions as func
from azure.eventhub import EventData
from azure.eventhub import EventHubProducerClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from faker import Faker

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def gerar_id(prefixo, tamanho=6):
    return prefixo + ''.join(random.choices(string.digits, k=tamanho))


def gerar_cnpj():
    return ''.join(random.choices(string.digits, k=14))


def gerar_cpf():
    return ''.join(random.choices(string.digits, k=11))


def gerar_placa():
    letras = ''.join(random.choices(string.ascii_uppercase, k=3))
    numeros = ''.join(random.choices(string.digits, k=4))
    return f"{letras}-{numeros}"


def agora():
    return datetime.now(timezone.utc).isoformat()


def get_int_setting(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def get_secret_from_keyvault(secret_name):
    """Lê um segredo do Azure Key Vault usando Managed Identity"""
    key_vault_uri = os.getenv("KEY_VAULT_URI")
    if not key_vault_uri:
        raise ValueError("KEY_VAULT_URI não está definido nas configurações da Function")

    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)

    try:
        secret = secret_client.get_secret(secret_name)
        return secret.value
    except Exception as e:
        raise ValueError(f"Erro ao ler segredo {secret_name} do Key Vault: {str(e)}")


def gerar_payload():
    fake = Faker("pt_BR")
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    ingestion_ts = agora()

    num_clientes = get_int_setting("NUM_CLIENTES", 1)
    num_restaurantes = get_int_setting("NUM_RESTAURANTES", 1)
    num_drivers = get_int_setting("NUM_DRIVERS", 1)
    num_items_per_restaurante = get_int_setting("NUM_ITEMS_PER_RESTAURANTE", 8)
    num_pedidos = get_int_setting("NUM_PEDIDOS", 8)

    entregadores = []
    for _ in range(num_drivers):
        entregadores.append({
            "DriversID": gerar_id("D"),
            "nome": fake.name(),
            "endereco": fake.address(),
            "veiculo": random.choice(["moto", "carro", "bicicleta"]),
            "placa": gerar_placa(),
            "created_at": agora()
        })

    restaurantes = []
    for _ in range(num_restaurantes):
        restaurantes.append({
            "MerchantID": gerar_id("R"),
            "nome": fake.company(),
            "endereco": fake.address(),
            "CNPJ": gerar_cnpj(),
            "created_at": agora()
        })

    clientes = []
    for _ in range(num_clientes):
        clientes.append({
            "ClientID": gerar_id("C"),
            "nome": fake.name(),
            "endereco": fake.address(),
            "CPF": gerar_cpf(),
            "tipo_pagamento": random.choice(["PIX", "CARTÃO CREDITO", "CARTÃO DEBITO", "VOUCHER"]),
            "created_at": agora()
        })

    categorias = ["Hamburguer", "Pizza", "Comida Japonesa", "Sobremesa", "Bebida"]
    produtos = []
    for restaurante in restaurantes:
        for _ in range(num_items_per_restaurante):
            produtos.append({
                "ItemID": gerar_id("I"),
                "nome": fake.word(),
                "categoria": random.choice(categorias),
                "preco": round(random.uniform(10, 120), 2),
                "MerchantID": restaurante["MerchantID"],
                "created_at": agora()
            })

    pedidos = []
    for _ in range(num_pedidos):
        cliente = random.choice(clientes)
        restaurante = random.choice(restaurantes)
        entregador = random.choice(entregadores)
        produtos_restaurante = [p for p in produtos if p["MerchantID"] == restaurante["MerchantID"]]
        quantidade_itens = min(len(produtos_restaurante), random.randint(2, 4))
        itens_escolhidos = random.sample(produtos_restaurante, k=quantidade_itens)

        itens_detalhados = []
        valor_total = 0
        quantidade_total = 0

        for item in itens_escolhidos:
            qtd = random.randint(1, 3)
            valor_item = item["preco"] * qtd
            itens_detalhados.append({
                "ItemID": item["ItemID"],
                "nome": item["nome"],
                "categoria": item["categoria"],
                "preco": item["preco"],
                "MerchantID": item["MerchantID"],
                "quantidade": qtd,
                "valor_total_item": round(valor_item, 2),
                "created_at": agora()
            })
            valor_total += valor_item
            quantidade_total += qtd

        pedidos.append({
            "PedidoID": gerar_id("P"),
            "ClientID": cliente["ClientID"],
            "MerchantID": restaurante["MerchantID"],
            "DriversID": entregador["DriversID"],
            "Produtos": itens_detalhados,
            "quantidade_total": quantidade_total,
            "valor_total": round(valor_total, 2),
            "tipo_pagamento": cliente["tipo_pagamento"],
            "created_at": agora()
        })

    return {
        "batch_id": batch_id,
        "ingestion_ts": ingestion_ts,
        "source_system": "azure_function_fake_generator",
        "schema_version": "1.0",
        "tables": {
            "clientes": clientes,
            "restaurantes": restaurantes,
            "items": produtos,
            "drivers": entregadores,
            "orders": pedidos
        }
    }


def enviar_eventhub(payload):
    eventhub_name = os.getenv("EVENTHUB_NAME")
    fully_qualified_namespace = os.getenv("EVENTHUB_FULLY_QUALIFIED_NAMESPACE")

    # Se Event Hub não estiver configurado, apenas loga o payload
    if not eventhub_name or not fully_qualified_namespace:
        logger.info(f"Event Hub não configurado. Payload gerado (batch_id: {payload['batch_id']}):")
        logger.info(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    # Se EVENTHUB_CONNECTION_STRING não estiver definido, usa Managed Identity
    connection_string = os.getenv("EVENTHUB_CONNECTION_STRING")
    if connection_string:
        producer = EventHubProducerClient.from_connection_string(
            conn_str=connection_string,
            eventhub_name=eventhub_name
        )
    else:
        credential = DefaultAzureCredential()
        producer = EventHubProducerClient(
            fully_qualified_namespace=fully_qualified_namespace,
            eventhub_name=eventhub_name,
            credential=credential
        )

    try:
        with producer:
            event_data_batch = producer.create_batch()
            event = EventData(json.dumps(payload, ensure_ascii=False))
            event.properties = {
                "event_type": "delivery_fake_batch",
                "schema_version": payload["schema_version"],
                "batch_id": payload["batch_id"]
            }
            event_data_batch.add(event)
            producer.send_batch(event_data_batch)
    finally:
        credential.close()


def main(mytimer: func.TimerRequest) -> None:
    try:
        payload = gerar_payload()
        enviar_eventhub(payload)
        logger.info(f"Batch {payload['batch_id']} processado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao processar batch: {str(e)}")
        raise
