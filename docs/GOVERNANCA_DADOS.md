# Governança de Dados - DataMasterV2

## Objetivo

Esta implementação adiciona uma camada inicial de governança para o projeto Databricks Lakehouse.

Ela cobre:

- classificação de dados sensíveis;
- tags no Unity Catalog;
- views mascaradas para consumo seguro;
- grants por perfil profissional;
- centralização das regras de Data Quality usadas pelo DLT;
- job manual para aplicar governança.

## Catálogo e schemas

Ambiente atual:

```text
catalog: delivery_datamaster
schema principal: default
schema governado: governance
```

As tabelas Bronze, Silver e Gold continuam em:

```text
delivery_datamaster.default
```

As views seguras ficam em:

```text
delivery_datamaster.governance
```

## Perfis de acesso

### Engenheiro de Dados

Grupo esperado:

```text
data_engineers
```

Acesso:

- leitura nas tabelas do schema principal;
- permissão de modificação no schema principal;
- leitura nas views governadas.

Uso esperado:

- manutenção de pipelines;
- troubleshooting;
- evolução de tabelas;
- análise técnica.

### Analista de Dados

Grupo esperado:

```text
data_analysts
```

Acesso:

- somente views mascaradas no schema `governance`;
- sem acesso direto às tabelas Silver com PII.

Uso esperado:

- dashboards;
- relatórios;
- análises de negócio.

### Cientista de Dados

Grupo esperado:

```text
data_scientists
```

Acesso:

- tabelas de pedidos e itens;
- views mascaradas de clientes;
- sem CPF/endereço completos.

Uso esperado:

- modelagem;
- análise comportamental;
- features com menor exposição de PII.

## Dados classificados como sensíveis

### PII alta

- `silver_clientes.cpf`

### PII

- `silver_clientes.nome`
- `silver_clientes.endereco`
- `silver_drivers.nome`
- `silver_drivers.endereco`
- `silver_restaurantes.endereco`

### Identificadores sensíveis

- `silver_restaurantes.cnpj`
- `silver_drivers.placa`

### Financeiro

- `silver_orders.valor_total`
- `silver_order_items.preco`
- `silver_order_items.valor_total_item`

## Views mascaradas criadas

### `governance.vw_clientes_analyst`

Mascara:

- nome;
- CPF.

Exemplo:

```text
Julia Andrade -> J***
95791273771 -> ***3771
```

### `governance.vw_drivers_analyst`

Mascara:

- nome;
- placa.

### `governance.vw_orders_analytics`

Expõe dados analíticos de pedidos sem dados diretos de pessoa.

### `governance.vw_gold_delivery_dashboard`

Expõe KPIs Gold para dashboards.

## Tags no Unity Catalog

O notebook `lakeflow/governance/apply_governance.py` aplica tags em tabelas e colunas.

Exemplos:

```text
classification = restricted
contains_pii = true
layer = silver
domain = customer
```

Essas tags ajudam:

- descoberta de dados;
- auditoria;
- LGPD;
- documentação;
- controle por domínio.

## Data Quality centralizado

As regras DLT foram movidas para:

```text
lakeflow/data_quality/rules.py
```

As tabelas Silver e Gold usam essas regras via:

```python
@dlt.expect_all_or_drop(...)
@dlt.expect_all_or_fail(...)
```

Benefício:

- regra fica fora do código principal da tabela;
- manutenção fica mais simples;
- governança de qualidade fica explícita.

## Job de governança

Foi criado o job manual:

```text
job-dmv2-apply-governance
```

Ele executa:

```text
lakeflow/governance/apply_governance.py
```

O job:

- cria schema `governance`;
- aplica tags;
- cria views mascaradas;
- aplica grants por grupo.

## Como executar

Depois do deploy do bundle:

```powershell
databricks bundle run apply_governance -t dev --profile dbw-dmv2-dev
```

## Pré-requisito importante

Os grupos precisam existir no Databricks Account/Workspace:

```text
data_engineers
data_analysts
data_scientists
```

Se os nomes forem diferentes, altere os parâmetros no `databricks.yml`.

## Próximos passos recomendados

- criar grupos reais no Databricks;
- validar permissões com usuários de teste;
- adicionar auditoria via `system.access.audit`;
- criar dashboard de qualidade DLT;
- definir política formal de retenção por camada;
- expandir FinOps por job/pipeline/cluster.
