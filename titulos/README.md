# Sistema Corporativo de Gestão de Títulos Minerários (ANM / SIGMINE)
**QGIS + PostGIS para Controle Regulatório, Prazos Legais e Alertas**

Sistema corporativo de gestão territorial e regulatória desenvolvido para mineradoras que atuam no Brasil, permitindo o controle rigoroso dos processos minerários perante a **Agência Nacional de Mineração (ANM)**, com conformidade ao **Código de Mineração (Decreto-Lei nº 227/1967)** e regulamentações vigentes.

---

## 1. Arquitetura e Estrutura do Projeto

```text
gestao_titulos_anm/
├── sql/
│   ├── 01_schema_postgis.sql        # Modelagem relacional e espacial (titular, processo, evento, obrigacao, GIST e dados fictícios)
│   ├── 02_triggers_prazos.sql       # Triggers e funções PL/pgSQL para cálculo automático de vencimentos e alertas
│   └── 03_views_painel.sql          # Views espaciais por situação e painel de prazos (RFP, TAH, GU e Alertas Urgentes)
├── scripts/
│   └── build_qgis_project.py        # Script automatizado para construção e validação do projeto QGIS (.qgs)
├── qgis/
│   └── gestao_titulos_anm.qgs       # Projeto QGIS configurado com estilos, relações 1:N, formulários e validações
└── README.md                        # Documentação completa de implantação, regras e uso
```

---

## 2. Modelagem Relacional e Espacial

### 2.1. Entidades Principais
1. **`titular`**:
   - Cadastro cadastral dos detentores de direitos minerários (estilo SIGMINE).
   - Campos: `id`, `cnpj_cpf` (único), `razao_social`, `nome_fantasia`, `tipo_pessoa` (PF/PJ), `email`, `telefone`, `endereco`, `cidade`, `uf`.
2. **`processo`**:
   - Processos minerários na ANM vinculados ao titular (`1:N`).
   - Campos: `numero_processo` (ex.: `830.112/2021`), `ano_processo`, `titular_id`, `fase` (*Requerimento de Pesquisa*, *Autorização de Pesquisa*, *Direito de Requerer Lavra*, *Requerimento de Lavra*, *Concessão de Lavra*, *Licenciamento*), `substancia_mineral`, `uso_substancia`, `area_ha`, `municipio`, `uf`, `data_requerimento`, `data_publicacao_alvara`, `prazo_alvara_anos`, `data_vencimento_alvara`, `status_processo`.
   - **Geometria Espacial**: `geom GEOMETRY(MultiPolygon, 4674)` em **SIRGAS 2000 (EPSG:4674)**, padrão cartográfico oficial do Brasil e da ANM, com índice espacial `GIST`.
3. **`evento`**:
   - Histórico administrativo e marcos regulatórios do processo (`1:N`).
   - Tipos de eventos: *Publicação de Alvará no DOU*, *Pagamento de TAH*, *Protocolo de RFP*, *Emissão de Guia de Utilização*, *Notificação / Exigência ANM*, etc.
4. **`obrigacao`**:
   - Prazos legais do Código de Mineração vinculados ao processo (`1:N`).
   - Tipos de obrigações:
     - **Relatório de Pesquisa (RFP)**: Prazo legal do Alvará de Pesquisa (Art. 22 do Código de Mineração).
     - **Taxa Anual por Hectare (TAH)**: Pagamento anual obrigatório (Art. 20, II do Código de Mineração).
     - **Guia de Utilização (GU)**: Título autorizativo de extração prévia com vigência e prestação de contas.
     - **Relatório Anual de Lavra (RAL)**: Declaração anual até 15 de março.
     - **Cumprimento de Exigência**: Prazos de notificações da ANM (geralmente 60 dias).

---

## 3. Automação por Triggers PL/pgSQL

O banco conta com triggers inteligentes que asseguram consistência em tempo real:

1. **`trg_calcular_vencimento_obrigacao` (`fn_calcular_vencimento_automatica_obrigacao`)**:
   - Calcula automaticamente a data de vencimento se não informada:
     - **Relatório de Pesquisa**: `data_referencia + 3 anos`.
     - **Taxa Anual por Hectare (TAH)**:
       - Alvará publicado no 1º semestre: vencimento em **31 de julho**.
       - Alvará publicado no 2º semestre: vencimento em **31 de janeiro** do ano subsequente.
       - Cálculo financeiro automático: `area_ha * R$ 4,71/ha`.
     - **Guia de Utilização**: `data_referencia + 1 ano`.
     - **RAL**: `15 de março` do ano do exercício.
     - **Cumprimento de Exigência**: `data_referencia + 60 dias`.

2. **`trg_recalcular_alerta_obrigacao` (`fn_recalcular_alerta_obrigacao`)**:
   - Atualiza `dias_para_vencer` e `nivel_alerta` dinamicamente:
     - **Vencido**: `dias_para_vencer < 0` e status Pendente.
     - **Alerta Crítico / Próximo ao Vencimento**: `0 <= dias_para_vencer <= 30` dias.
     - **No Prazo**: `dias_para_vencer > 30` dias.
     - **Cumprido**: Quando preenchida `data_cumprimento` ou status quitado.

3. **`trg_gerar_obrigacoes_evento` (`fn_gerar_obrigacoes_por_evento`)**:
   - Disparado ao registrar novos eventos:
     - Publicação de Alvará -> Cria automaticamente obrigações de RFP e TAH, e atualiza datas no processo.
     - Emissão de Guia de Utilização -> Cria obrigação de vigência da GU.
     - Pagamento de TAH / Protocolo de RFP -> Dá baixa automática na obrigação pendente correspondente.

4. **`fn_atualizar_todos_alertas()`**:
   - Procedimento em lote para recálculo diário de todos os alertas.

---

## 4. Views Espaciais e Painel de Prazos

- **`vw_processos_situacao_espacial`**: Camada espacial consolidada com polígonos, dados do titular, totalizador de obrigações e classificação pelo **pior nível de alerta** (usada para mapa temático de risco regulatório no QGIS).
- **`vw_processos_relatorio_pesquisa`**: View espacial focada nos processos com obrigação de Relatório Final de Pesquisa.
- **`vw_processos_taxa_anual_hectare`**: View espacial com valores devidos e prazos de pagamento da TAH.
- **`vw_processos_guia_utilizacao`**: View espacial para monitoramento de vigência de Guias de Utilização.
- **`vw_painel_prazos_consolidado`**: Resumo executivo com contadores de obrigações pendentes, vencidas, em alerta crítico, no prazo, cumpridas e índice percentual de conformidade legal.
- **`vw_painel_alertas_urgentes`**: Lista priorizada dos processos que requerem intervenção imediata (vencidos ou com vencimento nos próximos 30 dias), com telefones e e-mails de contato do titular.

---

## 5. Projeto QGIS Corporativo (`gestao_titulos_anm.qgs`)

O projeto QGIS gerado pelo script `build_qgis_project.py` possui:

### 5.1. Relações 1:N Integradas
- **`rel_titular_processo`**: Titular (1) -> Processos Minerários (N).
- **`rel_processo_evento`**: Processo (1) -> Histórico de Eventos Regulatórios (N).
- **`rel_processo_obrigacao`**: Processo (1) -> Prazos e Obrigações Legais (N).

### 5.2. Formulários em Abas com Validações
Ao abrir a tabela de atributos ou formulário de feição do `processo`:
- **Aba 1 (Dados Cadastrais ANM)**: Número do processo, fase, substância mineral, área (ha), município, UF.
- **Aba 2 (Marcos Regulatórios)**: Datas de requerimento, alvará, vigência e status.
- **Aba 3 (Histórico de Eventos)**: Subformulário embutido via `RelationEditor` exibindo todos os eventos vinculados.
- **Aba 4 (Prazos e Obrigações Legais)**: Subformulário embutido via `RelationEditor` exibindo todas as obrigações e alertas.

### 5.3. Regras de Validação (Constraints)
- `numero_processo`: Expressão regular obrigatória `^\d{3,6}\.\d{3}/\d{4}$` (ex.: `830.112/2021`).
- `area_ha`: Restrição `"area_ha" > 0`.
- `ano_processo`: Restrição `"ano_processo" >= 1934 AND "ano_processo" <= 2100`.

### 5.4. Simbologia Temática
- **Vermelho (`#D90429`)**: Processo com obrigação vencida (Ação Imediata).
- **Laranja (`#F77F00`)**: Processo com obrigação em Alerta Crítico (vence em ≤ 30 dias).
- **Verde (`#06D6A0`)**: Processo com obrigações regulares no prazo (> 30 dias).
- **Azul (`#118AB2`)**: Processo com todas as obrigações cumpridas / regular.

---

## 6. Credenciais do Banco de Dados

| Parâmetro | Valor Padrão Local / VM |
| :--- | :--- |
| **Host** | `localhost` ou `2804:18:704b:b23:a00:27ff:fe6b:96d0` |
| **Porta** | `5432` |
| **Banco de Dados** | `gestao_titulos_minerarios` |
| **Usuário** | `pedro` (ou `postgres`) |
| **Senha** | `123` |
| **SRID / CRS** | `4674` (SIRGAS 2000) |

---

## 7. Como Executar e Testar na Máquina Virtual

### 7.1. Aplicar os scripts SQL no PostgreSQL
```bash
# Conectar no PostgreSQL e executar a criação do banco e tabelas:
sudo -u postgres psql -c "CREATE DATABASE gestao_titulos_minerarios;"
sudo -u postgres psql -c "CREATE USER pedro WITH SUPERUSER PASSWORD '123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE gestao_titulos_minerarios TO pedro;"

# Aplicar os scripts do sistema:
PGPASSWORD=123 psql -h localhost -U pedro -d gestao_titulos_minerarios -f /home/pedro/gestao_titulos_anm/sql/01_schema_postgis.sql
PGPASSWORD=123 psql -h localhost -U pedro -d gestao_titulos_minerarios -f /home/pedro/gestao_titulos_anm/sql/02_triggers_prazos.sql
PGPASSWORD=123 psql -h localhost -U pedro -d gestao_titulos_minerarios -f /home/pedro/gestao_titulos_anm/sql/03_views_painel.sql
```

### 7.2. Gerar o projeto QGIS
```bash
python3 /home/pedro/gestao_titulos_anm/scripts/build_qgis_project.py /home/pedro/gestao_titulos_anm/qgis/gestao_titulos_anm.qgs
```

### 7.3. Testar consultas no terminal
```bash
# Consultar o Painel Consolidado de Prazos:
PGPASSWORD=123 psql -h localhost -U pedro -d gestao_titulos_minerarios -c "SELECT * FROM vw_painel_prazos_consolidado;"

# Consultar os Alertas Urgentes:
PGPASSWORD=123 psql -h localhost -U pedro -d gestao_titulos_minerarios -c "SELECT numero_processo, titular, tipo_obrigacao, data_vencimento, dias_para_vencer, nivel_alerta FROM vw_painel_alertas_urgentes;"

# Testar Trigger inserindo um novo evento de alvará:
PGPASSWORD=123 psql -h localhost -U pedro -d gestao_titulos_minerarios -c "
INSERT INTO evento (processo_id, tipo_evento, data_evento, descricao, documento_sei, responsavel)
VALUES (7, 'Publicação de Alvará de Pesquisa no DOU', CURRENT_DATE, 'Alvará de Pesquisa nº 999/2026 outorgado', 'SEI-02100.009999/2026', 'ANM Sede');
"

# Verificar obrigações de RFP e TAH geradas automaticamente pelo Trigger:
PGPASSWORD=123 psql -h localhost -U pedro -d gestao_titulos_minerarios -c "
SELECT tipo_obrigacao, data_vencimento, dias_para_vencer, nivel_alerta, valor_devido
FROM obrigacao WHERE processo_id = 7;
"
```
