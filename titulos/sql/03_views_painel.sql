-- ==============================================================================
-- SISTEMA CORPORATIVO DE GESTÃO DE TÍTULOS MINERÁRIOS (ANM / SIGMINE)
-- Script: 03_views_painel.sql
-- Descrição: Criação de Views Espaciais por Situação e Views Analíticas de
--            Painel de Prazos (RFP, TAH, GU, Alertas Críticos e Urgentes).
-- ==============================================================================

-- 1. Limpeza de views existentes (se houver)
DROP VIEW IF EXISTS vw_painel_alertas_urgentes CASCADE;
DROP VIEW IF EXISTS vw_painel_prazos_consolidado CASCADE;
DROP VIEW IF EXISTS vw_processos_guia_utilizacao CASCADE;
DROP VIEW IF EXISTS vw_processos_taxa_anual_hectare CASCADE;
DROP VIEW IF EXISTS vw_processos_relatorio_pesquisa CASCADE;
DROP VIEW IF EXISTS vw_processos_situacao_espacial CASCADE;

-- ==============================================================================
-- 2. View Espacial: Situação Consolidada dos Processos e Poligonais
--    Agrega os alertas mais severos e status de cada processo para exibição
--    temática no SIG (QGIS)
-- ==============================================================================
CREATE OR REPLACE VIEW vw_processos_situacao_espacial AS
WITH agg_obrigacoes AS (
    SELECT
        processo_id,
        COUNT(*) AS total_obrigacoes,
        COUNT(*) FILTER (WHERE status = 'Pendente') AS total_pendentes,
        COUNT(*) FILTER (WHERE status = 'Pendente' AND nivel_alerta = 'Vencido') AS total_vencidas,
        COUNT(*) FILTER (WHERE status = 'Pendente' AND nivel_alerta = 'Alerta Crítico / Próximo ao Vencimento') AS total_alerta_critico,
        COUNT(*) FILTER (WHERE status = 'Pendente' AND nivel_alerta = 'No Prazo') AS total_no_prazo,
        COUNT(*) FILTER (WHERE status = 'Cumprido') AS total_cumpridas,
        MIN(data_vencimento) FILTER (WHERE status = 'Pendente') AS proxima_data_vencimento,
        SUM(valor_devido) FILTER (WHERE status = 'Pendente' AND tipo_obrigacao = 'Taxa Anual por Hectare') AS valor_tah_pendente
    FROM obrigacao
    GROUP BY processo_id
),
proxima_obrigacao_info AS (
    SELECT DISTINCT ON (processo_id)
        processo_id,
        tipo_obrigacao AS proxima_obrigacao_tipo,
        data_vencimento AS proxima_obrigacao_data,
        dias_para_vencer AS proxima_obrigacao_dias,
        nivel_alerta AS proxima_obrigacao_alerta
    FROM obrigacao
    WHERE status = 'Pendente'
    ORDER BY processo_id, data_vencimento ASC, id ASC
)
SELECT
    p.id AS processo_id,
    p.numero_processo,
    p.ano_processo,
    p.fase,
    p.substancia_mineral,
    p.uso_substancia,
    p.area_ha,
    p.municipio,
    p.uf,
    p.data_requerimento,
    p.data_publicacao_alvara,
    p.prazo_alvara_anos,
    p.data_vencimento_alvara,
    p.data_portaria_lavra,
    p.status_processo,
    -- Dados do Titular
    t.id AS titular_id,
    t.razao_social AS titular_razao_social,
    t.nome_fantasia AS titular_nome_fantasia,
    t.cnpj_cpf AS titular_cnpj_cpf,
    t.email AS titular_email,
    t.telefone AS titular_telefone,
    -- Contadores de Obrigações
    COALESCE(o.total_obrigacoes, 0) AS total_obrigacoes,
    COALESCE(o.total_pendentes, 0) AS total_pendentes,
    COALESCE(o.total_vencidas, 0) AS total_vencidas,
    COALESCE(o.total_alerta_critico, 0) AS total_alerta_critico,
    COALESCE(o.total_no_prazo, 0) AS total_no_prazo,
    COALESCE(o.total_cumpridas, 0) AS total_cumpridas,
    COALESCE(o.valor_tah_pendente, 0.00) AS valor_tah_pendente,
    -- Pior Nível de Alerta (Classificação de Risco Corporativo)
    CASE
        WHEN COALESCE(o.total_vencidas, 0) > 0 THEN 'Vencido'
        WHEN COALESCE(o.total_alerta_critico, 0) > 0 THEN 'Alerta Crítico / Próximo ao Vencimento'
        WHEN COALESCE(o.total_no_prazo, 0) > 0 THEN 'No Prazo'
        WHEN COALESCE(o.total_cumpridas, 0) > 0 AND COALESCE(o.total_pendentes, 0) = 0 THEN 'Cumprido / Regular'
        ELSE 'Sem Obrigações Registradas'
    END AS pior_nivel_alerta,
    -- Próxima Obrigação a Vencer
    poi.proxima_obrigacao_tipo,
    poi.proxima_obrigacao_data,
    poi.proxima_obrigacao_dias,
    poi.proxima_obrigacao_alerta,
    -- Geometria Espacial (SRID 4674)
    p.geom
FROM processo p
INNER JOIN titular t ON p.titular_id = t.id
LEFT JOIN agg_obrigacoes o ON p.id = o.processo_id
LEFT JOIN proxima_obrigacao_info poi ON p.id = poi.processo_id;

COMMENT ON VIEW vw_processos_situacao_espacial IS 'Camada espacial consolidada com geometria poligonal, titular e pior nível de alerta regulatório';

-- ==============================================================================
-- 3. View Espacial: Painel Específico - Relatório Final de Pesquisa (RFP)
-- ==============================================================================
CREATE OR REPLACE VIEW vw_processos_relatorio_pesquisa AS
SELECT
    o.id AS obrigacao_id,
    p.id AS processo_id,
    p.numero_processo,
    p.fase,
    p.substancia_mineral,
    p.area_ha,
    p.municipio,
    p.uf,
    t.razao_social AS titular_razao_social,
    t.email AS titular_email,
    p.data_publicacao_alvara,
    o.data_vencimento AS data_vencimento_rfp,
    o.data_cumprimento AS data_cumprimento_rfp,
    o.status AS status_rfp,
    o.dias_para_vencer AS dias_para_vencer_rfp,
    o.nivel_alerta AS nivel_alerta_rfp,
    o.descricao AS descricao_obrigacao,
    o.observacoes,
    p.geom
FROM obrigacao o
INNER JOIN processo p ON o.processo_id = p.id
INNER JOIN titular t ON p.titular_id = t.id
WHERE o.tipo_obrigacao = 'Relatório de Pesquisa';

COMMENT ON VIEW vw_processos_relatorio_pesquisa IS 'View espacial com poligonais dos processos acompanhando o prazo do Relatório Final de Pesquisa (Art. 22 do CM)';

-- ==============================================================================
-- 4. View Espacial: Painel Específico - Taxa Anual por Hectare (TAH)
-- ==============================================================================
CREATE OR REPLACE VIEW vw_processos_taxa_anual_hectare AS
SELECT
    o.id AS obrigacao_id,
    p.id AS processo_id,
    p.numero_processo,
    p.fase,
    p.substancia_mineral,
    p.area_ha,
    p.municipio,
    p.uf,
    t.razao_social AS titular_razao_social,
    o.ano_exercicio,
    o.valor_devido AS valor_tah,
    o.data_vencimento AS data_vencimento_tah,
    o.data_cumprimento AS data_pagamento_tah,
    o.status AS status_tah,
    o.dias_para_vencer AS dias_para_vencer_tah,
    o.nivel_alerta AS nivel_alerta_tah,
    o.numero_guia_documento AS comprovante_gru,
    o.observacoes,
    p.geom
FROM obrigacao o
INNER JOIN processo p ON o.processo_id = p.id
INNER JOIN titular t ON p.titular_id = t.id
WHERE o.tipo_obrigacao = 'Taxa Anual por Hectare';

COMMENT ON VIEW vw_processos_taxa_anual_hectare IS 'View espacial para controle de pagamentos da Taxa Anual por Hectare (TAH) com status e alerta';

-- ==============================================================================
-- 5. View Espacial: Painel Específico - Guia de Utilização (GU)
-- ==============================================================================
CREATE OR REPLACE VIEW vw_processos_guia_utilizacao AS
SELECT
    o.id AS obrigacao_id,
    p.id AS processo_id,
    p.numero_processo,
    p.fase,
    p.substancia_mineral,
    p.area_ha,
    p.municipio,
    p.uf,
    t.razao_social AS titular_razao_social,
    o.numero_guia_documento AS numero_guia_anm,
    o.data_referencia AS data_emissao_gu,
    o.data_vencimento AS data_vencimento_gu,
    o.data_cumprimento AS data_prestacao_contas,
    o.status AS status_gu,
    o.dias_para_vencer AS dias_para_vencer_gu,
    o.nivel_alerta AS nivel_alerta_gu,
    o.descricao,
    o.observacoes,
    p.geom
FROM obrigacao o
INNER JOIN processo p ON o.processo_id = p.id
INNER JOIN titular t ON p.titular_id = t.id
WHERE o.tipo_obrigacao = 'Guia de Utilização';

COMMENT ON VIEW vw_processos_guia_utilizacao IS 'View espacial para monitoramento da vigência e prestação de contas de Guias de Utilização';

-- ==============================================================================
-- 6. View Analítica: Painel de Prazos Consolidado por Tipo de Obrigação
-- ==============================================================================
CREATE OR REPLACE VIEW vw_painel_prazos_consolidado AS
SELECT
    tipo_obrigacao,
    COUNT(*) AS total_obrigacoes,
    COUNT(*) FILTER (WHERE status = 'Pendente') AS pendentes,
    COUNT(*) FILTER (WHERE status = 'Pendente' AND nivel_alerta = 'Vencido') AS vencidas,
    COUNT(*) FILTER (WHERE status = 'Pendente' AND nivel_alerta = 'Alerta Crítico / Próximo ao Vencimento') AS alerta_critico,
    COUNT(*) FILTER (WHERE status = 'Pendente' AND nivel_alerta = 'No Prazo') AS no_prazo,
    COUNT(*) FILTER (WHERE status = 'Cumprido') AS cumpridas,
    COUNT(*) FILTER (WHERE status IN ('Dispensado', 'Cancelado')) AS dispensadas_ou_canceladas,
    COALESCE(SUM(valor_devido) FILTER (WHERE status = 'Pendente'), 0.00) AS valor_total_pendente,
    ROUND(
        (COUNT(*) FILTER (WHERE status = 'Cumprido')::NUMERIC / NULLIF(COUNT(*), 0)) * 100,
        1
    ) AS conformidade_percentual
FROM obrigacao
GROUP BY tipo_obrigacao
ORDER BY total_obrigacoes DESC;

COMMENT ON VIEW vw_painel_prazos_consolidado IS 'Painel executivo com métricas consolidadas de conformidade por tipo de obrigação minerária';

-- ==============================================================================
-- 7. View de Ação Imediata: Alertas Urgentes (Vencidos ou a Menos de 30 Dias)
-- ==============================================================================
CREATE OR REPLACE VIEW vw_painel_alertas_urgentes AS
SELECT
    o.id AS obrigacao_id,
    p.id AS processo_id,
    p.numero_processo,
    p.fase,
    p.substancia_mineral,
    p.municipio,
    p.uf,
    t.razao_social AS titular,
    t.telefone AS titular_telefone,
    t.email AS titular_email,
    o.tipo_obrigacao,
    o.data_vencimento,
    o.dias_para_vencer,
    o.nivel_alerta,
    o.valor_devido,
    o.numero_guia_documento,
    o.descricao,
    o.observacoes
FROM obrigacao o
INNER JOIN processo p ON o.processo_id = p.id
INNER JOIN titular t ON p.titular_id = t.id
WHERE o.status = 'Pendente'
  AND o.nivel_alerta IN ('Vencido', 'Alerta Crítico / Próximo ao Vencimento')
ORDER BY o.dias_para_vencer ASC;

COMMENT ON VIEW vw_painel_alertas_urgentes IS 'Lista de prioridade máxima para a equipe regulatória e jurídica da mineradora';
