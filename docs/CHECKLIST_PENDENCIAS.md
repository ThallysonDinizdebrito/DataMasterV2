# Checklist de Pendências - DataMasterV2

## Status Atual: 🟡 Parcialmente Implementado

---

## 🚨 Alta Prioridade

### 1. Event Hub (Não Implementado)
- [ ] Descomentar e configurar `infra/eventhub.tf`
- [ ] Habilitar variável `enable_eventhub` no `dev.tfvars`
- [ ] Testar ingestão de eventos
- [ ] Validar Event Hub Capture no Storage

### 2. Azure Key Vault (Parcial)
- [ ] Configurar permissões Key Vault para service principal
- [ ] Implementar secret scope backed by Key Vault no Databricks
- [ ] Migrar segredos do secret scope legado para Key Vault
- [ ] Validar Azure Function lendo segredos do Key Vault

### 3. Segredos Databricks (Manual)
- [ ] Adicionar `azure-client-secret` no secret scope `dmv2-dev`
- [ ] Validar acesso ao segredo via Databricks

### 4. Azure Cost Observability (Não Validado)
- [ ] Executar job `job-dmv2-azure-cost-observability`
- [ ] Validar ingestão de dados de custo
- [ ] Verificar tabelas de custo no schema `observability`

---

## 🟡 Média Prioridade

### 5. Delta Live Tables (Não Validado)
- [ ] Executar pipeline DLT principal
- [ ] Validar camadas bronze/silver/gold
- [ ] Verificar qualidade de dados
- [ ] Testar atualizações incrementais

### 6. Unity Catalog (Parcial)
- [ ] Configurar metastore assignment via Terraform
- [ ] Implementar governança completa
- [ ] Configurar permissões granulares
- [ ] Validar linhagem de dados

### 7. Azure Function (Não Validado)
- [ ] Testar geração de dados
- [ ] Validar envio para Event Hub (quando habilitado)
- [ ] Verificar logs de execução
- [ ] Testar Managed Identity

### 8. Data Quality (Não Validado)
- [ ] Executar regras de qualidade de dados
- [ ] Configurar alertas para falhas
- [ ] Validar expectativas no DLT

---

## 🟢 Baixa Prioridade

### 9. Grafana (Não Implementado)
- [ ] Descomentar recursos Grafana em `infrastructure.tf`
- [ ] Configurar dashboards
- [ ] Integrar com Azure Monitor
- [ ] Validar visualizações

### 10. Monitoramento e Alertas
- [ ] Configurar alertas no Azure Monitor
- [ ] Configurar alertas no Databricks
- [ ] Implementar health checks
- [ ] Configurar notificações

### 11. Documentação
- [ ] Atualizar documentação com estado atual
- [ ] Adicionar guias de troubleshooting
- [ ] Documentar processos de rollback
- [ ] Criar guias de operação

### 12. Testes
- [ ] Implementar testes unitários
- [ ] Implementar testes de integração
- [ ] Configurar testes automatizados no CI/CD
- [ ] Validar performance

---

## 📊 Resumo

| Componente | Status | Prioridade |
|------------|--------|------------|
| Event Hub | ❌ Não implementado | Alta |
| Key Vault | 🟡 Parcial | Alta |
| Databricks Secrets | 🟡 Manual | Alta |
| Azure Cost Obs | 🟡 Não validado | Alta |
| DLT Pipelines | 🟡 Não validado | Média |
| Unity Catalog | 🟡 Parcial | Média |
| Azure Function | 🟡 Não validado | Média |
| Data Quality | 🟡 Não validado | Média |
| Grafana | ❌ Não implementado | Baixa |
| Monitoramento | 🟡 Parcial | Baixa |

---

## 🎯 Próximos Passos Recomendados

1. **Imediato:** Adicionar segredo manualmente no Databricks
2. **Curto prazo:** Validar Azure Cost Observability
3. **Médio prazo:** Habilitar Event Hub e validar streaming
4. **Longo prazo:** Implementar Key Vault completo e Grafana

---

**DataMasterV2 - Checklist de Pendências**
**Versão:** 1.0
**Data:** 2026-06-24
