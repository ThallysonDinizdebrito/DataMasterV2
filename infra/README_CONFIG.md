# Configuração do DataMasterV2 para Unity Catalog

## Passos para Configurar

### 1. Criar Usuário Organizacional e Obter Account Admin (Obrigatório para Unity Catalog)

O Unity Catalog exige grupos no nível de conta (account-level) para concessão de permissões. Contas pessoais Microsoft (outlook.com, gmail.com) não são suportadas.

**Passo 1: Criar usuário organizacional via Azure CLI**
```bash
az ad user create --display-name "Admin User" --user-principal-name admin@seudominio.onmicrosoft.com --password "SuaSenhaSegura123!"
```

**Passo 2: Atribuir permissão de Global Admin via Azure Portal**
1. Acesse: https://portal.azure.com
2. Vá para "Microsoft Entra ID" → "Users"
3. Clique no usuário criado
4. Clique em "Funções atribuídas" (Roles assigned)
5. Clique em "Adicionar atribuição"
6. Selecione "Global Administrator"
7. Clique em "Salvar"

**Passo 3: Acessar Databricks Account Console**
1. Faça logout do Azure Portal
2. Login com o novo usuário: admin@seudominio.onmicrosoft.com
3. Acesse: https://accounts.azuredatabricks.net
4. Agora você tem acesso como account admin

**Passo 4: Criar grupos account-level**
No Databricks Account Console:
1. Vá para "User Management" → "Groups"
2. Crie os grupos: data-engineers, data-scientists, data-analysts
3. Adicione usuários aos grupos conforme necessário

### 2. Copie o arquivo de exemplo:
```bash
cd C:\Users\Thall\infra\DataMasterV2\infra
copy dev.tfvars.example dev.tfvars
```

### 3. Edite o dev.tfvars com seus valores reais:
   - `unity_catalog_metastore_id`: Seu ID do metastore do Unity Catalog
   - `databricks_token`: Seu PAT token do Databricks
   - `databricks_host`: Já está preenchido com seu workspace URL

### 4. Obtenha seu Metastore ID:
```bash
databricks unity-catalog metastores list --profile dbw-dmv2-dev
```

### 5. Obtenha seu PAT Token:
   - Acesse: https://adb-7405608830882565.5.azuredatabricks.net/?o=953205e1-ba48-45aa-a0bf-77ae9a7a5240#/settings/personal-access-tokens
   - Crie um novo token com permissões adequadas

## Passos para Aplicar

1. **Inicialize o Terraform:**
```bash
cd C:\Users\Thall\infra\DataMasterV2\infra
terraform init
```

2. **Planeje as mudanças:**
```bash
terraform plan -var-file="dev.tfvars"
```

3. **Aplique as mudanças:**
```bash
terraform apply -var-file="dev.tfvars"
```

## O que foi alterado

1. **Grupos Databricks:** Grupos account-level criados manualmente via Databricks Account Console (data-engineers, data-scientists, data-analysts)
2. **Permissões Unity Catalog:** Configuradas manualmente no Account Console para evitar conflitos com Terraform
3. **Notebook apply_governance.py:** Apenas cria schemas, tags e views - não concede mais permissões
4. **Account Admin:** Criado usuário organizacional admin@thallysoncamila2017outlook.onmicrosoft.com com permissão Global Admin

## Configuração Unity Catalog

### Grupos account-level criados:
- data-engineers
- data-scientists
- data-analysts

### Permissões configuradas manualmente:
As permissões do Unity Catalog são gerenciadas manualmente via Account Console para evitar conflitos com Terraform. Para modificar permissões:

1. Acesse: https://accounts.azuredatabricks.net
2. Vá para "Data" → "Unity Catalog"
3. Selecione o catalog "delivery_datamaster"
4. Clique em "Permissions"
5. Adicione/remova permissões conforme necessário

### Por que manual?
O Terraform teve conflitos ao tentar gerenciar permissões devido a discrepâncias entre o estado atual e o desejado. A configuração manual evita esses conflitos e permite controle direto das permissões.
