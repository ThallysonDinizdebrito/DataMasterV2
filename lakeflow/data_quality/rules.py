CLIENT_RULES = {
    "valid_client_id": "client_id IS NOT NULL",
    "valid_client_id_format": "client_id RLIKE '^C[0-9]+$'",
    "valid_cpf": "cpf RLIKE '^[0-9]{11}$'",
    "valid_client_payment_type": "tipo_pagamento IN ('PIX', 'CARTÃO CREDITO', 'CARTÃO DEBITO', 'VOUCHER')",
    "valid_client_created_at": "created_at IS NOT NULL",
}

RESTAURANT_RULES = {
    "valid_merchant_id": "merchant_id IS NOT NULL",
    "valid_merchant_id_format": "merchant_id RLIKE '^R[0-9]+$'",
    "valid_cnpj": "cnpj RLIKE '^[0-9]{14}$'",
    "valid_restaurant_name": "nome IS NOT NULL",
    "valid_restaurant_created_at": "created_at IS NOT NULL",
}

DRIVER_RULES = {
    "valid_driver_id": "driver_id IS NOT NULL",
    "valid_driver_id_format": "driver_id RLIKE '^D[0-9]+$'",
    "valid_vehicle_type": "veiculo IN ('moto', 'carro', 'bicicleta')",
    "valid_plate": "placa RLIKE '^[A-Z]{3}-[0-9]{4}$'",
    "valid_driver_created_at": "created_at IS NOT NULL",
}

ITEM_RULES = {
    "valid_item_id": "item_id IS NOT NULL",
    "valid_item_id_format": "item_id RLIKE '^I[0-9]+$'",
    "valid_item_name": "nome IS NOT NULL",
    "valid_item_category": "categoria IN ('Hamburguer', 'Pizza', 'Comida Japonesa', 'Sobremesa', 'Bebida')",
    "valid_price": "preco > 0",
    "valid_item_merchant_id": "merchant_id RLIKE '^R[0-9]+$'",
    "valid_item_created_at": "created_at IS NOT NULL",
}

ORDER_RULES = {
    "valid_order_id": "order_id IS NOT NULL",
    "valid_order_id_format": "order_id RLIKE '^P[0-9]+$'",
    "valid_order_client_id": "client_id RLIKE '^C[0-9]+$'",
    "valid_order_merchant_id": "merchant_id RLIKE '^R[0-9]+$'",
    "valid_order_driver_id": "driver_id RLIKE '^D[0-9]+$'",
    "valid_order_amount": "valor_total > 0",
    "valid_total_quantity": "quantidade_total > 0",
    "valid_order_payment_type": "tipo_pagamento IN ('PIX', 'CARTÃO CREDITO', 'CARTÃO DEBITO', 'VOUCHER')",
    "valid_order_created_at": "created_at IS NOT NULL",
    "valid_order_date": "order_date IS NOT NULL",
}

ORDER_ITEM_RULES = {
    "valid_order_item": "order_id IS NOT NULL AND item_id IS NOT NULL",
    "valid_order_item_ids_format": "order_id RLIKE '^P[0-9]+$' AND item_id RLIKE '^I[0-9]+$'",
    "valid_order_item_category": "categoria IN ('Hamburguer', 'Pizza', 'Comida Japonesa', 'Sobremesa', 'Bebida')",
    "valid_order_item_price": "preco > 0",
    "valid_item_quantity": "quantidade > 0",
    "valid_order_item_total": "valor_total_item > 0",
    "valid_order_item_created_at": "created_at IS NOT NULL",
}

