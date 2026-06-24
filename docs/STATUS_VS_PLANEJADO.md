# Comparação entre Planejamento Inicial e Estado Atual do Projeto

Este documento compara a visão planejada para o projeto DataMasterV2 com o estado atual implementado.

A ideia original era criar um projeto de engenharia de dados de alto nível juntando os pontos fortes de dois projetos anteriores:

```text
F1rstDatamaster
semana-databricks-2-0
```

O objetivo era manter o fluxo end-to-end do primeiro projeto e trazer a maturidade Databricks/Lakehouse do segundo.

## 1. Resumo executivo

O projeto atual já evoluiu bastante em relação à ideia inicial.

Hoje já existem:

```text
Infraestrutura Azure via Terraform
Azure Function geradora de dados
Event Hub/Event Hub Capture
ADLS Gen2
Databricks Bundle
Pipeline DLT/Lakeflow Bronze, Silver e Gold
GitHub Actions com deploy automatizado
Start automático da pipeline DLT via Action
Secrets no GitHub Actions
Documentação operacional
```

A maior diferença em relação ao planejamento inicial é que algumas práticas mais avançadas de segurança e governança ainda não foram implementadas completamente, principalmente:

```text
Unity Catalog com External Location
Key Vault como fonte central de segredos
VNet injection no Databricks
RBAC completo por grupos
Observabilidade com alertas reais
AI Functions na camada Gold
```

## 2. Comparação por fase planejada

## Fase 1 — Identidade e segurança

### Planejado

```text
Service Principal único com permissões mínimas.
Key Vault centralizando todos os segredos.
SP separado para automação Databricks.
Grafana com Managed Identity.
Nenhuma credencial em arquivo ou variável exposta.
```

### Estado atual

```text
GitHub Actions usa Service Principal Azure via secrets.
Secrets principais estão no GitHub Secrets.
DATABRICKS_TOKEN está no GitHub Secrets.
STORAGE_ACCOUNT_KEY está no GitHub Secrets.
A pipeline Databricks acessa ADLS via Storage Account Key injetada no bundle.
```

### Status

```text
Parcialmente implementado.
```

### O que mudou

A solução final para destravar o Databricks foi usar:

```text
BUNDLE_VAR_storage_account_key
```

alimentado pelo GitHub Secret:

```text
STORAGE_ACCOUNT_KEY
```

Isso resolveu o erro:

```text
Invalid configuration value detected for fs.azure.account.key
```

### O que ainda falta

```text
Criar Key Vault.
Mover secrets sensíveis para Key Vault.
Criar External Location no Unity Catalog.
Remover dependência de Storage Account Key na pipeline.
Usar Service Principal/Managed Identity para acesso ao ADLS.
Revisar permissões mínimas do Service Principal do GitHub Actions.
```

## Fase 2 — Infraestrutura via Terraform em duas fases com Makefile

### Planejado

```text
Terraform modularizado por responsabilidade.
Deploy em duas fases.
Fase 1: Azure base e Databricks workspace.
Fase 2: recursos internos Databricks.
Tfstate remoto no Azure Blob Storage.
Makefile para padronizar comandos.
```

### Estado atual

```text
Terraform já existe em arquivos separados.
Existe backend remoto para tfstate.
GitHub Actions prepara backend remoto automaticamente.
GitHub Actions executa Terraform.
Existe Makefile com comandos básicos.
Databricks Bundle é executado após Terraform no workflow.
```

### Status

```text
Parcialmente implementado.
```

### O que mudou

O deploy em duas fases foi tratado principalmente no GitHub Actions:

```text
setup-tf-backend
terraform
function
databricks
```

Na prática, a Action já separa a ordem de execução.

### O que ainda falta

```text
Formalizar melhor as duas fases no Makefile.
Separar claramente Terraform Azure e Terraform Databricks se necessário.
Criar comandos make infra-up, make databricks-up, make deploy-dev.
Revisar se algum recurso Databricks ainda depende de workspace recém-criado no mesmo apply.
```

## Fase 3 — Rede segura

### Planejado

```text
VNet dedicada.
Subnets pública e privada para Databricks.
no_public_ip = true.
NSG controlando tráfego.
Private Endpoints desabilitados por padrão via feature flag.
```

### Estado atual

```text
Databricks workspace existe.
Infraestrutura Azure está provisionada.
Não foi confirmada implementação completa de VNet injection com no_public_ip.
Private Endpoints ainda não são parte central do fluxo atual.
```

### Status

```text
Pendente ou parcialmente implementado.
```

### O que ainda falta

```text
Validar se o Databricks está com VNet injection.
Adicionar ou consolidar subnets pública/privada.
Configurar no_public_ip = true.
Adicionar feature flag para Private Endpoints.
Documentar desenho de rede.
```

## Fase 4 — Geração de dados melhorada com Azure Function

### Planejado

```text
Azure Function em Python com Faker.
Volumes parametrizados por variável de ambiente.
Relacionamentos reais entre entidades.
Arquivos separados por entidade.
Pastas no Blob por tipo de dado.
Encoding UTF-8 correto.
```

### Estado atual

```text
Azure Function existe.
A Action publica a Azure Function.
O projeto usa domínio delivery.
Os dados chegam ao Event Hub/Event Hub Capture.
A pipeline DLT lê os arquivos capturados no ADLS.
```

### Status

```text
Parcialmente implementado.
```

### O que mudou

A ingestão atual não está baseada apenas em JSON direto no Blob.
O fluxo operacional passou a usar:

```text
Azure Function → Event Hub → Event Hub Capture → ADLS → DLT
```

Isso é uma evolução positiva, porque simula melhor uma ingestão near real-time/event-driven.

### O que ainda falta

```text
Validar se todos os IDs têm relacionamento real.
Parametrizar volume por variável de ambiente.
Organizar payloads para facilitar joins Silver.
Adicionar logs estruturados na Function.
Adicionar validações de schema do payload.
```

## Fase 5 — Pipeline Bronze, Silver e Gold com Delta Live Tables

### Planejado

```text
Bronze lendo JSON/arquivos com Auto Loader.
Silver limpando e enriquecendo dados.
Gold com métricas de negócio.
Constraints e tratamento de dados inválidos.
Materialized Views para consumo analítico.
```

### Estado atual

```text
Databricks Bundle existe em lakeflow/databricks.yml.
Pipeline DLT/Lakeflow foi criada.
Bronze, Silver e Gold existem em arquivos separados.
Bronze lê Event Hub Capture em formato AVRO via Auto Loader.
Silver processa entidades de delivery.
Gold gera métricas de negócio.
Pipeline foi executada manualmente com sucesso.
Pipeline foi executada automaticamente via GitHub Actions.
```

### Status

```text
Implementado em boa parte.
```

### O que mudou

A Bronze não lê JSON direto.
Ela lê AVRO capturado pelo Event Hub Capture:

```text
abfss://source@stdmv2devvxc02.dfs.core.windows.net/eventhub-capture
```

Essa mudança deixou o projeto mais forte, pois adicionou Event Hub na arquitetura.

### O que ainda falta

```text
Adicionar expectativas/constraints mais completas.
Enviar registros rejeitados para área/container rejeitados.
Criar mais métricas Gold.
Adicionar validações pós-deploy na Action.
Adicionar testes de qualidade de dados.
```

## Fase 6 — Unity Catalog com governança real

### Planejado

```text
Catálogo delivery_datamaster.
Schemas bronze, silver e gold.
Grupos data_engineers, data_scientists e data_analysts.
External Location para ADLS.
Grants por perfil.
Retenção por camada.
```

### Estado atual

```text
Pipeline usa catálogo Databricks configurado no bundle.
Schema default está sendo usado no alvo atual.
Unity Catalog é requisito para DLT serverless.
Ainda não há governança completa por catálogo/schemas dedicados e grupos.
Acesso ao ADLS ainda usa Storage Account Key.
```

### Status

```text
Parcialmente implementado.
```

### O que ainda falta

```text
Criar catálogo dedicado delivery_datamaster.
Criar schemas bronze, silver e gold.
Alterar pipeline para gravar nos schemas corretos.
Criar grupos e grants.
Criar Storage Credential.
Criar External Location.
Remover Storage Account Key do bundle.
Definir retenção por camada.
```

## Fase 7 — AI Functions na camada Gold

### Planejado

```text
Tabela Gold com ai_query().
Classificação automática de pedidos.
Classificação de status final.
Classificação de padrões de pagamento.
SQL puro sem API externa.
```

### Estado atual

```text
Ainda não implementado.
```

### Status

```text
Pendente.
```

### O que ainda falta

```text
Verificar disponibilidade de AI Functions no workspace.
Verificar SQL Warehouse compatível.
Criar tabela ou view Gold com ai_query().
Adicionar exemplo de classificação de pedidos.
Adicionar documentação e validação.
```

## Fase 8 — Observabilidade completa

### Planejado

```text
Log Analytics centralizado.
Application Insights para Azure Function.
Action Group com alerta por e-mail.
Grafana com dashboard de infraestrutura.
Grafana com dashboard de negócio.
Métricas de pipeline e dados.
```

### Estado atual

```text
Projeto possui preocupação com observabilidade.
GitHub Actions publica recursos e valida etapas.
Ainda não foi consolidado um pacote completo de dashboards e alertas.
```

### Status

```text
Parcialmente implementado ou pendente de validação.
```

### O que ainda falta

```text
Validar Log Analytics e Application Insights.
Criar alertas Azure Monitor.
Criar Action Group.
Criar dashboard Grafana de infraestrutura.
Criar dashboard Grafana de negócio baseado na Gold.
Adicionar monitoramento do status da pipeline DLT.
```

## 3. Mudanças importantes que aconteceram durante a implementação

## 3.1. De Blob direto para Event Hub Capture

### Planejado originalmente

```text
Azure Function → Blob/ADLS JSON → DLT
```

### Estado atual

```text
Azure Function → Event Hub → Event Hub Capture → ADLS AVRO → DLT
```

### Impacto

Essa mudança deixou o projeto mais sofisticado.

Pontos positivos:

```text
Simula arquitetura orientada a eventos.
Permite ingestão streaming/near real-time.
Aproxima o projeto de cenários corporativos reais.
Mostra domínio de Event Hub e Event Hub Capture.
```

## 3.2. Correção da autenticação ADLS no DLT

### Problema encontrado

O uso de Databricks Secret diretamente no Spark config falhou:

```yaml
{{secrets/dmv2-dev/storage-account-key}}
```

Erro:

```text
Invalid configuration value detected for fs.azure.account.key
```

### Solução atual

Foi adotada variável de bundle:

```yaml
${var.storage_account_key}
```

Alimentada por:

```text
BUNDLE_VAR_storage_account_key
```

No GitHub Actions:

```yaml
BUNDLE_VAR_storage_account_key: ${{ secrets.STORAGE_ACCOUNT_KEY }}
```

### Impacto

A pipeline passou a conseguir acessar o ADLS e executar corretamente.

## 3.3. GitHub Actions passou a iniciar a pipeline DLT

### Antes

A Action fazia apenas deploy.

### Agora

A Action faz deploy e start:

```bash
databricks bundle deploy -t dev
databricks bundle run delivery_eventhub_medallion_v2 -t dev
```

### Impacto

O processo ficou end-to-end automatizado.

## 3.4. Documentação operacional foi adicionada

### Documentos criados/atualizados

```text
docs/REPLICACAO.md
docs/GITHUB_ACTIONS_SETUP.md
docs/STATUS_VS_PLANEJADO.md
```

### Impacto

O projeto ficou mais replicável e mais fácil de apresentar.

## 4. Tabela geral de status

| Área | Status atual | Observação |
|---|---|---|
| Terraform Azure | Parcial/funcional | Infra roda via Action, mas ainda pode ser mais modular. |
| Backend remoto Terraform | Implementado | Action prepara backend remoto. |
| Azure Function | Implementado/parcial | Publicada via Action, mas pode melhorar geração e relacionamentos. |
| Event Hub/Event Hub Capture | Implementado | Fluxo atual usa captura em ADLS. |
| ADLS Gen2 | Implementado | Usado como origem da pipeline DLT. |
| Databricks Bundle | Implementado | Bundle faz deploy da pipeline. |
| DLT Bronze/Silver/Gold | Implementado | Pipeline executou com sucesso. |
| GitHub Actions deploy | Implementado | Terraform, Function e Databricks rodam via Action. |
| Start automático DLT | Implementado | `databricks bundle run` adicionado. |
| GitHub Secrets | Implementado | Azure, Databricks e Storage Key cadastrados. |
| Key Vault | Pendente | Ainda não centraliza segredos. |
| Unity Catalog completo | Parcial | Falta catálogo/schemas/grants/external location. |
| VNet injection | Pendente/validar | Falta confirmar ou implementar desenho seguro. |
| Grafana dashboards | Pendente/validar | Ainda precisa consolidar dashboards finais. |
| Alertas | Pendente | Falta Action Group e regras. |
| AI Functions | Pendente | Ainda não implementado na Gold. |
| Testes e qualidade | Pendente/parcial | Falta testes e validações pós-deploy. |

## 5. Onde estamos agora

O projeto está no fim da primeira grande etapa:

```text
MVP end-to-end automatizado
```

O MVP atual já consegue:

```text
Criar/atualizar infraestrutura.
Publicar Azure Function.
Publicar Databricks Bundle.
Injetar credenciais necessárias.
Executar pipeline DLT.
Gerar tabelas Bronze, Silver e Gold.
Ser acionado pelo GitHub Actions.
```

## 6. Próxima etapa recomendada

A próxima etapa deve ser transformar o MVP funcional em uma versão mais profissional e governada.

Ordem recomendada:

```text
1. Consolidar commit final do estado atual. OK 
2. Validar contagens e qualidade das tabelas Bronze/Silver/Gold.
3. Criar validação pós-run no GitHub Actions. (criar um action com validação apos rum)
4. Implementar Unity Catalog com catálogo, schemas e grants. OK
5. Migrar acesso ADLS de Storage Account Key para External Location. OK
6. Melhorar Azure Function com dados mais ricos e parametrizados.
7. Criar dashboards Grafana de negócio e infraestrutura.
8. Adicionar alertas.
9. Adicionar AI Functions na camada Gold.
10. Revisar rede segura com VNet injection/no public IP.
```

## 7. Conclusão

Comparado com o planejamento original, o projeto avançou muito na parte operacional e end-to-end.

O maior ganho implementado foi:

```text
GitHub Actions agora executa deploy completo e inicia a pipeline DLT automaticamente.
```

O maior desvio técnico foi:

```text
Uso temporário de Storage Account Key via GitHub Secret em vez de Unity Catalog External Location.
```

Esse desvio é aceitável para o MVP porque destravou a execução e validou o fluxo.

Para chegar no projeto top de linha planejado, os próximos focos devem ser:

```text
Unity Catalog completo
External Location
Key Vault
Observabilidade com alertas
AI Functions
Rede segura
```

## 8. Próximo incremento - Observabilidade de custos no Databricks

Foi adicionada a base para uma frente de FinOps dentro do Databricks.

Objetivo:

```text
Azure Cost Management API
  -> Databricks job
  -> Unity Catalog
  -> Tabelas Delta de custo
  -> Dashboard de acompanhamento
```

Arquivos adicionados/alterados:

```text
lakeflow/observability/azure_cost_ingestion.py
lakeflow/databricks.yml
```

Job Databricks criado no bundle:

```text
azure_cost_observability
```

Tabelas planejadas:

```text
delivery_datamaster.observability.azure_cost_by_resource_daily
delivery_datamaster.observability.azure_cost_summary_daily
```

O job busca os últimos 30 dias de custo real na Azure Cost Management API, agrupado por:

```text
data
resource_id
resource_type
resource_group
service_name
meter_category
meter_subcategory
currency
```

O schedule foi criado como `PAUSED` para evitar custo automático. A execução pode ser feita manualmente pelo Databricks ou via:

```powershell
databricks bundle run azure_cost_observability -t dev
```

Pré-requisitos para funcionar:

```text
1. O Service Principal precisa ter permissão Cost Management Reader ou Reader na subscription.
2. O client secret do Service Principal precisa existir em um Databricks Secret Scope.
3. Secret scope esperado: dmv2-dev
4. Secret key esperada: azure-client-secret
```

Comando de exemplo para criar o secret no Databricks:

```powershell
databricks secrets put-secret dmv2-dev azure-client-secret --profile dbw-dmv2-dev
```

Depois de executar o job, o dashboard pode usar as tabelas de observabilidade para acompanhar:

```text
custo diário total
custo por resource group
custo por tipo de recurso
custo por serviço Azure
ranking dos recursos mais caros
variação de custo nos últimos 7/30 dias
```
