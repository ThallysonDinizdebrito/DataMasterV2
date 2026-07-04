# Guia Didático do Projeto DataMasterV2

## Índice
1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Conceitos Fundamentais](#conceitos-fundamentais)
3. [Streaming e Event Hub](#streaming-e-event-hub)
4. [Delta Live Tables (DLT)](#delta-live-tables-dlt)
5. [Azure Key Vault e Gestão de Segredos](#azure-key-vault-e-gestão-de-segredos)
6. [Arquitetura do Projeto](#arquitetura-do-projeto)
7. [Fluxo de Dados do Início ao Fim](#fluxo-de-dados-do-início-ao-fim)
8. [Tecnologias e Ferramentas](#tecnologias-e-ferramentas)
9. [Conclusão](#conclusão)

---

## Visão Geral do Projeto

**DataMasterV2** é uma plataforma de dados moderna que processa dados de delivery em tempo real, desde a geração de dados até a análise e governança.

**O que o projeto faz:**
- Gera dados simulados de delivery (pedidos, restaurantes, clientes, motoristas)
- Processa esses dados em tempo real usando streaming
- Armazena os dados em camadas (bronze, silver, gold)
- Aplica qualidade de dados e governança
- Fornece análises e métricas de delivery

**Analogia simples:**
Imagine um aplicativo de delivery como iFood ou Rappi. O DataMasterV2 simula como esse aplicativo gera, processa e analisa todos os dados que fluem pelo sistema.

---

## Conceitos Fundamentais

### O que é Dados em Tempo Real?

**Dados em tempo real** são dados que são gerados e processados instantaneamente, conforme acontecem.

**Exemplo do dia a dia:**
- Quando você faz um pedido no iFood, o pedido aparece no restaurante em segundos
- Quando o motorista aceita o pedido, você recebe a notificação imediatamente
- Quando o pedido é entregue, o status muda em tempo real

**Por que isso importa?**
- Decisões podem ser tomadas instantaneamente
- Os usuários têm uma experiência melhor
- Problemas podem ser detectados e corrigidos rapidamente

### O que é Arquitetura de Dados?

**Arquitetura de dados** é como organizamos e estruturamos o fluxo de dados em um sistema.

**Analogia:**
Pense na arquitetura de uma casa:
- Fundação: onde tudo começa
- Paredes: estrutura que suporta tudo
- Telhado: proteção final

Na arquitetura de dados:
- Fonte de dados: onde os dados são gerados
- Processamento: como os dados são transformados
- Armazenamento: onde os dados ficam guardados
- Consumo: como os dados são usados

---

## Streaming e Event Hub

### O que é Streaming?

**Streaming** é o processamento contínuo de dados conforme eles são gerados, sem esperar que tudo seja coletado antes de processar.

**Analogia:**
- **Batch (processamento em lote):** Como assistir um filme em DVD - você precisa ter o filme inteiro antes de assistir
- **Streaming:** Como assistir Netflix - o filme é transmit pedaço por pedaço enquanto você assiste

**No contexto do DataMasterV2:**
- Dados de pedidos são gerados continuamente
- Cada pedido é processado assim que é criado
- Não esperamos acumular 1000 pedidos para processar

### O que é Azure Event Hub?

**Azure Event Hub** é um serviço de ingestão de eventos em tempo real da Microsoft.

**O que ele faz:**
- Recebe milhões de eventos por segundo
- Armazena eventos temporariamente
- Distribui eventos para consumidores
- É altamente escalável

**Analogia:**
Pense no Event Hub como uma estação de correios super moderna:
- Milhões de cartas (eventos) chegam a cada segundo
- A estação organiza e distribui as cartas
- Diferentes carteiros (consumidores) pegam as cartas para entregar

**Vantagens do Event Hub:**
1. **Alta Escalabilidade:** Pode processar milhões de eventos por segundo
2. **Baixa Latência:** Processa eventos quase instantaneamente
3. **Durabilidade:** Garante que eventos não sejam perdidos
4. **Integração:** Funciona bem com outros serviços Azure
5. **Custo Eficiente:** Você paga pelo que usa

### Por que usar Streaming no DataMasterV2?

**Cenário do projeto:**
- Pedidos de delivery são criados continuamente
- Restaurantes precisam receber pedidos em tempo real
- Motoristas precisam saber onde entregar
- Clientes precisam acompanhar o pedido

**Benefícios:**
1. **Experiência do Usuário:** Clientes veem atualizações em tempo real
2. **Decisões Rápidas:** Restaurantes podem ajustar estoque instantaneamente
3. **Detecção de Problemas:** Pedidos atrasados são identificados rapidamente
4. **Análise em Tempo Real:** Métricas podem ser calculadas instantaneamente

### O que você precisa saber sobre Streaming

**Conceitos importantes:**

1. **Evento:** Uma unidade de dados (ex: um pedido)
2. **Produtor:** Quem gera os eventos (ex: Azure Function)
3. **Consumidor:** Quem processa os eventos (ex: Databricks)
4. **Partição:** Divisão de eventos para paralelismo
5. **Offset:** Posição de leitura no stream

**Desafios do Streaming:**
- Ordem dos eventos pode não ser garantida
- Eventos podem chegar duplicados
- Sistema precisa lidar com falhas
- Latência vs throughput trade-off

### Escalabilidade em Streaming

**O que é escalabilidade?**
Capacidade de lidar com mais dados sem perder performance.

**Como o Event Hub escala:**
- **Horizontal:** Adiciona mais partições
- **Vertical:** Aumenta capacidade de cada partição
- **Auto-scaling:** Ajusta automaticamente conforme demanda

**Analogia:**
- **Horizontal:** Adicionar mais caixas em um supermercado
- **Vertical:** Fazer cada caixa trabalhar mais rápido
- **Auto-scaling:** O supermercado abre mais caixas quando há fila

---

## Delta Live Tables (DLT)

### O que é Delta Live Tables?

**Delta Live Tables (DLT)** é uma framework da Databricks para pipelines de dados declarativos.

**O que significa "declarativo"?**
Você diz **O QUE** quer, não **COMO** fazer.

**Analogia:**
- **Imperativo (tradicional):** "Vá até a cozinha, pegue o pão, coloque na torradeira, espere 2 minutos, retire o pão"
- **Declarativo (DLT):** "Quero torrada"

**No DLT:**
- Você define as tabelas e transformações
- O Databricks cuida da execução, otimização e monitoramento
- Você não precisa gerenciar clusters ou orquestração

### Vantagens do DLT

1. **Simplicidade:** Menos código para escrever
2. **Manutenção:** Otimizações automáticas
3. **Monitoramento:** Interface de observabilidade integrada
4. **Qualidade de Dados:** Regras de qualidade embutidas
5. **Versionamento:** Controle de versões automático

### O que você precisa saber sobre DLT

**Conceitos importantes:**

1. **Pipeline:** Conjunto de tabelas e transformações
2. **Tabela:** Dados estruturados (bronze, silver, gold)
3. **Transformação:** Lógica para processar dados
4. **Expectativa:** Regra de qualidade de dados
5. **Update:** Processo de atualização de dados

**Camadas de Dados (Medallion Architecture):**

**Bronze (Raw):**
- Dados brutos, como chegaram
- Sem transformações
- Alta granularidade

**Silver (Cleaned):**
- Dados limpos e padronizados
- Transformações aplicadas
- Qualidade verificada

**Gold (Aggregated):**
- Dados agregados e otimizados
- Prontos para análise
- Performance otimizada

### Como o DLT funciona no DataMasterV2

**Pipeline de Dados:**
1. **Bronze:** Recebe dados do Event Hub (bruto)
2. **Silver:** Limpa e padroniza dados
3. **Gold:** Agrega dados para análise

**Exemplo prático:**
- **Bronze:** Pedido com dados brutos do Event Hub
- **Silver:** Pedido com endereço padronizado, status validado
- **Gold:** Métricas de pedidos por região, tempo médio de entrega

---

## Azure Key Vault e Gestão de Segredos

### O que é Azure Key Vault?

**Azure Key Vault** é um serviço da Microsoft para gerenciar segredos, chaves e certificados de forma segura.

**O que ele guarda:**
- Senhas e chaves API (segredos)
- Chaves de criptografia (keys)
- Certificados digitais (certificates)

**Analogia:**
Pense no Key Vault como um cofre digital super seguro:
- Apenas pessoas autorizadas podem abrir
- Tudo é criptografado
- Há registro de quem acessou o quê
- Pode ser acessado de qualquer lugar, de forma segura

### Por que usar Key Vault?

**Problemas de armazenar segredos em código:**
1. **Segurança:** Qualquer um com acesso ao código pode ver os segredos
2. **Rotação:** Difícil atualizar segredos regularmente
3. **Compliance:** Viola normas de segurança
4. **Version Control:** Segredos ficam no histórico do Git

**Vantagens do Key Vault:**
1. **Segurança:** Segredos criptografados e isolados
2. **Rotação:** Fácil atualizar segredos
3. **Auditoria:** Registro de acessos
4. **Integração:** Funciona com outros serviços Azure
5. **Managed Identity:** Sem necessidade de credenciais estáticas

### O que é Managed Identity?

**Managed Identity** é uma identidade gerenciada pelo Azure para recursos.

**O que ela faz:**
- Elimina necessidade de credenciais estáticas
- Gerencia automaticamente rotação de credenciais
- Simplifica autenticação entre serviços Azure

**Analogia:**
- **Sem Managed Identity:** Você precisa carregar chaves físicas para cada porta
- **Com Managed Identity:** Seu rosto é sua chave, funciona em todas as portas automaticamente

**No DataMasterV2:**
- Azure Function usa Managed Identity para acessar Key Vault
- Não há senhas hardcoded no código
- A identidade é gerenciada pelo Azure

### Como o Key Vault é usado no DataMasterV2

**Segredos gerenciados:**
- Azure Client Secret (para Azure Cost Management)
- Databricks Token (opcional)
- Storage Account Keys (opcional)

**Integração:**
- Terraform cria/atualiza segredos no Key Vault
- Azure Function lê segredos usando Managed Identity
- Databricks pode ler segredos via Secret Scope backed by Key Vault

**Nota atual:**
No momento, o projeto usa Databricks Secret Scope legado, mas está preparado para migração futura para Key Vault.

---

## Arquitetura do Projeto

### Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Function                            │
│              (Gerador de Dados Fake)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Azure Event Hub                           │
│              (Ingestão de Eventos em Tempo Real)            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Event Hub Capture (Storage)                     │
│              (Armazenamento Temporário)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Databricks                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Delta Live Tables (Pipeline)                        │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │
│  │  │ Bronze  │→ │ Silver  │→ │  Gold   │            │   │
│  │  └─────────┘  └─────────┘  └─────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Unity Catalog (Governança)                      │
│              (Catálogo de Dados)                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Power BI / Análises                             │
│              (Consumo dos Dados)                             │
└─────────────────────────────────────────────────────────────┘
```

### Componentes da Arquitetura

**1. Azure Function (Gerador de Dados)**
- Gera dados simulados de delivery
- Envia eventos para Event Hub
- Usa Managed Identity para autenticação

**2. Azure Event Hub**
- Recebe eventos em tempo real
- Distribui para consumidores
- Capture para armazenamento

**3. Azure Storage (ADLS Gen2)**
- Armazena dados brutos (Event Hub Capture)
- Armazena dados processados (Delta Lake)
- Armazena dados governados (Unity Catalog)

**4. Databricks**
- Processa dados usando Delta Live Tables
- Aplica qualidade de dados
- Executa pipelines de dados

**5. Unity Catalog**
- Governança de dados
- Controle de acesso
- Linhagem de dados

**6. Azure Key Vault**
- Gerencia segredos
- Criptografia de dados
- Auditoria de acessos

---

## Fluxo de Dados do Início ao Fim

### Passo 1: Geração de Dados

**O que acontece:**
- Azure Function gera dados simulados de delivery
- Dados incluem: pedidos, restaurantes, clientes, motoristas
- Cada evento é enviado para Event Hub

**Exemplo de evento:**
```json
{
  "pedido_id": "12345",
  "cliente_id": "cliente_1",
  "restaurante_id": "restaurante_1",
  "motorista_id": "motorista_1",
  "status": "pendente",
  "valor": 50.00,
  "timestamp": "2026-06-24T10:00:00Z"
}
```

### Passo 2: Ingestão no Event Hub

**O que acontece:**
- Event Hub recebe o evento
- Evento é armazenado em uma partição
- Evento fica disponível para consumo

**Características:**
- Alta throughput (milhões de eventos/segundo)
- Baixa latência (milissegundos)
- Durabilidade (eventos não são perdidos)

### Passo 3: Captura no Storage

**O que acontece:**
- Event Hub Capture grava eventos no Storage
- Eventos são salvos em formato AVRO
- Dados brutos são preservados

**Por que isso é importante:**
- Backup dos dados brutos
- Possibilidade de reprocessamento
- Auditoria completa

### Passo 4: Processamento no Databricks (Bronze)

**O que acontece:**
- DLT lê dados do Event Hub Capture
- Dados são carregados na camada Bronze
- Nenhuma transformação é aplicada

**Características da Bronze:**
- Dados brutos
- Alta granularidade
- Schema flexível

### Passo 5: Limpeza e Padronização (Silver)

**O que acontece:**
- DLT aplica transformações
- Dados são limpos e padronizados
- Qualidade de dados é verificada

**Exemplo de transformações:**
- Padronização de endereços
- Validação de status
- Remoção de duplicatas
- Enriquecimento de dados

### Passo 6: Agregação e Otimização (Gold)

**O que acontece:**
- DLT agrega dados para análise
- Dados são otimizados para consulta
- Métricas são calculadas

**Exemplo de agregações:**
- Pedidos por região
- Tempo médio de entrega
- Receita por restaurante
- Avaliação média por motorista

### Passo 7: Governança (Unity Catalog)

**O que acontece:**
- Dados são catalogados no Unity Catalog
- Permissões são aplicadas
- Linhagem é registrada

**Benefícios:**
- Descoberta fácil de dados
- Controle de acesso granular
- Auditoria de acessos

### Passo 8: Consumo (Análises)

**O que acontece:**
- Analistas acessam dados via Power BI
- Dashboards são atualizados em tempo real
- Decisões são tomadas baseadas em dados

**Exemplos de análises:**
- Monitoramento de pedidos em tempo real
- Análise de tendências de delivery
- Otimização de rotas
- Gestão de capacidade

---

## Tecnologias e Ferramentas

### Azure

**Azure Function**
- Serverless compute
- Gera dados simulados
- Integração com Event Hub

**Azure Event Hub**
- Ingestão de eventos em tempo real
- Alta escalabilidade
- Integração com Storage

**Azure Storage (ADLS Gen2)**
- Armazenamento de dados
- Delta Lake
- Hierarquia de dados

**Azure Key Vault**
- Gestão de segredos
- Criptografia
- Managed Identity

**Azure Monitor**
- Monitoramento de recursos
- Logs e métricas
- Alertas

### Databricks

**Delta Lake**
- Formato de dados
- ACID transactions
- Time Travel

**Delta Live Tables**
- Pipeline declarativo
- Qualidade de dados
- Monitoramento

**Unity Catalog**
- Governança de dados
- Catálogo centralizado
- Controle de acesso

### DevOps

**Terraform**
- Infrastructure as Code
- Automação de infraestrutura
- Gerenciamento de estado

**GitHub Actions**
- CI/CD
- Automação de deploy
- Integração com Azure

**GitHub OIDC**
- Autenticação federada
- Sem segredos estáticos
- Segurança aprimorada

---

## Conclusão

### Resumo do Projeto

**DataMasterV2** é uma plataforma moderna de dados que:
- Processa dados de delivery em tempo real
- Usa streaming e batch para diferentes necessidades
- Aplica governança e qualidade de dados
- É altamente escalável e segura

### Conceitos Chave Aprendidos

1. **Streaming:** Processamento contínuo de dados em tempo real
2. **Event Hub:** Serviço de ingestão de eventos altamente escalável
3. **DLT:** Framework declarativo para pipelines de dados
4. **Key Vault:** Gestão segura de segredos
5. **Managed Identity:** Autenticação sem credenciais estáticas
6. **Unity Catalog:** Governança de dados centralizada

### Próximos Passos

**Para aprender mais:**
- Experimente gerar dados e ver o fluxo
- Explore o Databricks Workspace
- Acompanhe os logs do Event Hub
- Analise os dados no Power BI

**Para aprofundar:**
- Estude Delta Lake e ACID transactions
- Aprenda sobre qualidade de dados
- Explore governança e compliance
- Entenda sobre segurança em dados

---

**DataMasterV2 - Guia Didático**
**Versão:** 1.0
**Data:** 2026-06-24
