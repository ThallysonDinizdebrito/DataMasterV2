# Manual de Replicação - DataMasterV2

Este documento registra todos os comandos e decisões usados para criar o projeto DataMasterV2 do zero.

## 1. Pré-requisitos verificados

```powershell
git --version
az --version
gh --version
databricks --version
terraform version
python --version
node --version
npm --version
func --version
make --version
```

## 2. Informações do ambiente

- Tenant ID: `1d1e1d50-bb96-44f7-81ad-10c6e41d1e6d`
- Subscription ID: `97eb265c-59ce-4122-bbe4-98f0d58d9208`
- Região: `brazilsouth`
- Projeto: `DataMasterV2`
- Repositório: `ThallysonDinizdebrito/DataMasterV2`
- Branch de deploy: `dev`

## 3. Bootstrap local

```powershell
New-Item -ItemType Directory -Force -Path C:\Users\Thall\infra\DataMasterV2
```

Diretórios principais criados:

```text
infra/
azure_function/
masterdatabricks/
grafana/
.github/workflows/
scripts/
docs/
```

## 4. Repositório Git

```powershell
git init
git checkout -b dev
```
