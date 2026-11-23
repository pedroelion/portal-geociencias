-- ==============================================================================
-- SISTEMA CORPORATIVO DE GESTÃO DE TÍTULOS MINERÁRIOS (ANM / SIGMINE)
-- Script: 01_schema_postgis.sql
-- Descrição: Criação das tabelas centrais (titular, processo, evento, obrigacao),
--            extensão PostGIS, integridade referencial 1:N, índices espaciais GIST
--            e inserção de dados fictícios realistas do setor mineral brasileiro.
-- ==============================================================================

-- 1. Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Limpeza prévia controlada (se necessário para recriação limpa)
DROP TABLE IF EXISTS obrigacao CASCADE;
DROP TABLE IF EXISTS evento CASCADE;
DROP TABLE IF EXISTS processo CASCADE;
DROP TABLE IF EXISTS titular CASCADE;

-- ==============================================================================
-- 3. Tabela: TITULAR (Pessoas Jurídicas / Físicas detentoras de direitos minerários)
-- ==============================================================================
CREATE TABLE titular (
    id SERIAL PRIMARY KEY,
    cnpj_cpf VARCHAR(20) NOT NULL UNIQUE,
    razao_social VARCHAR(200) NOT NULL,
    nome_fantasia VARCHAR(150),
    tipo_pessoa VARCHAR(2) NOT NULL DEFAULT 'PJ' CHECK (tipo_pessoa IN ('PF', 'PJ')),
    email VARCHAR(100) NOT NULL,
    telefone VARCHAR(30),
    endereco VARCHAR(250),
    cidade VARCHAR(100) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE titular IS 'Cadastro corporativo de titulares minerários (estilo SIGMINE/ANM)';
COMMENT ON COLUMN titular.cnpj_cpf IS 'Documento cadastral único do titular minerário';

-- ==============================================================================
-- 4. Tabela: PROCESSO (Processos Minerários na ANM vinculados ao Titular)
-- ==============================================================================
CREATE TABLE processo (
    id SERIAL PRIMARY KEY,
    numero_processo VARCHAR(30) NOT NULL UNIQUE,
    ano_processo INT NOT NULL CHECK (ano_processo >= 1934 AND ano_processo <= 2100),
    titular_id INT NOT NULL REFERENCES titular(id) ON DELETE RESTRICT,
    fase VARCHAR(60) NOT NULL CHECK (fase IN (
        'Requerimento de Pesquisa',
        'Autorização de Pesquisa',
        'Direito de Requerer Lavra',
        'Requerimento de Lavra',
        'Concessão de Lavra',
        'Licenciamento'
    )),
    substancia_mineral VARCHAR(100) NOT NULL,
    uso_substancia VARCHAR(100) DEFAULT 'Uso Industrial',
    area_ha NUMERIC(12, 4) NOT NULL CHECK (area_ha > 0),
    municipio VARCHAR(100) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    data_requerimento DATE NOT NULL,
    data_publicacao_alvara DATE,
    prazo_alvara_anos INT DEFAULT 3 CHECK (prazo_alvara_anos > 0),
    data_vencimento_alvara DATE,
    data_portaria_lavra DATE,
    status_processo VARCHAR(50) NOT NULL DEFAULT 'Ativo' CHECK (status_processo IN (
        'Ativo',
        'Arquivado',
        'Renunciado',
        'Caducado',
        'Em Disponibilidade'
    )),
    geom GEOMETRY(MultiPolygon, 4674), -- SIRGAS 2000 (Padrão Oficial Cartográfico do Brasil e ANM)
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE processo IS 'Processos minerários na ANM com polígonos espaciais em SIRGAS 2000 (EPSG:4674)';
COMMENT ON COLUMN processo.numero_processo IS 'Número de processo no formato oficial ANM (ex.: 800.123/2021)';
COMMENT ON COLUMN processo.geom IS 'Polígono ou multipolígono demarcatório da poligonal do processo minerário';

-- Índices essenciais para desempenho de consultas e operações espaciais
CREATE INDEX idx_processo_geom ON processo USING GIST (geom);
CREATE INDEX idx_processo_numero ON processo (numero_processo);
CREATE INDEX idx_processo_titular ON processo (titular_id);
CREATE INDEX idx_processo_fase ON processo (fase);
CREATE INDEX idx_processo_uf ON processo (uf);

-- ==============================================================================
-- 5. Tabela: EVENTO (Histórico de Eventos Administrativos/Legais - Relação 1:N)
-- ==============================================================================
CREATE TABLE evento (
    id SERIAL PRIMARY KEY,
    processo_id INT NOT NULL REFERENCES processo(id) ON DELETE CASCADE,
    tipo_evento VARCHAR(100) NOT NULL CHECK (tipo_evento IN (
        'Requerimento Protocolado',
        'Publicação de Alvará de Pesquisa no DOU',
        'Prorrogação de Alvará de Pesquisa',
        'Protocolo de Relatório Final de Pesquisa',
        'Aprovação de Relatório de Pesquisa',
        'Pagamento de TAH',
        'Requerimento de Guia de Utilização',
        'Emissão de Guia de Utilização',
        'Protocolo de Requerimento de Lavra',
        'Publicação de Portaria de Lavra',
        'Vistoria Técnica da ANM',
        'Notificação / Exigência ANM',
        'Outro Evento Relevante'
    )),
    data_evento DATE NOT NULL,
    descricao TEXT,
    documento_sei VARCHAR(50),
    responsavel VARCHAR(100),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE evento IS 'Histórico cronológico de eventos e marcos regulatórios de cada processo minerário';

CREATE INDEX idx_evento_processo ON evento (processo_id);
CREATE INDEX idx_evento_data ON evento (data_evento);
CREATE INDEX idx_evento_tipo ON evento (tipo_evento);

-- ==============================================================================
-- 6. Tabela: OBRIGACAO (Prazos Legais do Código de Mineração - Relação 1:N)
-- ==============================================================================
CREATE TABLE obrigacao (
    id SERIAL PRIMARY KEY,
    processo_id INT NOT NULL REFERENCES processo(id) ON DELETE CASCADE,
    tipo_obrigacao VARCHAR(80) NOT NULL CHECK (tipo_obrigacao IN (
        'Relatório de Pesquisa',
        'Taxa Anual por Hectare',
        'Guia de Utilização',
        'Relatório Anual de Lavra - RAL',
        'Cumprimento de Exigência'
    )),
    descricao TEXT,
    ano_exercicio INT,
    data_referencia DATE NOT NULL,
    data_vencimento DATE NOT NULL,
    data_cumprimento DATE,
    status VARCHAR(30) NOT NULL DEFAULT 'Pendente' CHECK (status IN (
        'Pendente',
        'Cumprido',
        'Dispensado',
        'Cancelado'
    )),
    dias_para_vencer INT,
    nivel_alerta VARCHAR(50) NOT NULL DEFAULT 'No Prazo' CHECK (nivel_alerta IN (
        'No Prazo',
        'Alerta Crítico / Próximo ao Vencimento',
        'Vencido',
        'Cumprido'
    )),
    valor_devido NUMERIC(12, 2) DEFAULT 0.00,
    numero_guia_documento VARCHAR(50),
    observacoes TEXT,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE obrigacao IS 'Prazos legais do Código de Mineração (RFP, TAH, GU, RAL) com controle de vencimento e alertas';

CREATE INDEX idx_obrigacao_processo ON obrigacao (processo_id);
CREATE INDEX idx_obrigacao_tipo ON obrigacao (tipo_obrigacao);
CREATE INDEX idx_obrigacao_vencimento ON obrigacao (data_vencimento);
CREATE INDEX idx_obrigacao_status ON obrigacao (status);
CREATE INDEX idx_obrigacao_alerta ON obrigacao (nivel_alerta);

-- ==============================================================================
-- 7. Inserção de Dados Fictícios Realistas (Titulares, Processos, Polígonos)
-- ==============================================================================

-- 7.1. Titulares da Mineração
INSERT INTO titular (id, cnpj_cpf, razao_social, nome_fantasia, tipo_pessoa, email, telefone, endereco, cidade, uf) VALUES
(1, '12.345.678/0001-90', 'Mineração Vale do Ouro S.A.', 'Vale do Ouro Mineração', 'PJ', 'contato@valedoouro.com.br', '(31) 3290-1000', 'Av. Afonso Pena, 3500 - Savassi', 'Belo Horizonte', 'MG'),
(2, '98.765.432/0001-10', 'Serra da Esperança Recursos Minerais Ltda.', 'Serra da Esperança', 'PJ', 'juridico@serraesperanca.com.br', '(62) 3215-4000', 'Rua 15, Quadra E-10 - Setor Oeste', 'Goiânia', 'GO'),
(3, '45.678.901/0001-23', 'Carajás Geosoluções & Mineração S.A.', 'Carajás GeoMinas', 'PJ', 'regulatório@carajasgeominas.com.br', '(94) 3356-8800', 'Rodovia PA-275, Km 12', 'Parauapebas', 'PA'),
(4, '33.222.111/0001-44', 'Bahia Rochas & Minérios Industriais Ltda.', 'Bahia Minérios', 'PJ', 'operacoes@bahiaminerios.com.br', '(77) 3454-1234', 'Av. Santana, 450 - Centro', 'Caetité', 'BA');

SELECT setval('titular_id_seq', (SELECT MAX(id) FROM titular));

-- 7.2. Processos Minerários com Geometrias Poligonais Válidas (SIRGAS 2000 / EPSG:4674)
-- Polígonos reais nos polos minerais de MG (Quadrilátero Ferrífero), GO (Crixás), PA (Carajás) e BA (Caetité)
INSERT INTO processo (id, numero_processo, ano_processo, titular_id, fase, substancia_mineral, uso_substancia, area_ha, municipio, uf, data_requerimento, data_publicacao_alvara, prazo_alvara_anos, data_vencimento_alvara, data_portaria_lavra, status_processo, geom) VALUES
(
    1,
    '830.112/2021',
    2021,
    1,
    'Autorização de Pesquisa',
    'Minério de Ferro',
    'Metalurgia / Siderurgia',
    985.5000,
    'Congonhas',
    'MG',
    '2021-03-10',
    '2022-04-15',
    3,
    '2025-04-15',
    NULL,
    'Ativo',
    ST_Multi(ST_GeomFromText('POLYGON((-43.8900 -20.4800, -43.8500 -20.4800, -43.8500 -20.5200, -43.8900 -20.5200, -43.8900 -20.4800))', 4674))
),
(
    2,
    '831.405/2019',
    2019,
    1,
    'Direito de Requerer Lavra',
    'Minério de Ferro',
    'Siderurgia',
    1450.2500,
    'Mariana',
    'MG',
    '2019-06-20',
    '2020-08-10',
    3,
    '2023-08-10',
    NULL,
    'Ativo',
    ST_Multi(ST_GeomFromText('POLYGON((-43.4500 -20.3500, -43.4000 -20.3500, -43.4000 -20.4000, -43.4500 -20.4000, -43.4500 -20.3500))', 4674))
),
(
    3,
    '860.220/2023',
    2023,
    2,
    'Autorização de Pesquisa',
    'Ouro',
    'Ourivesaria / Reserva de Valor',
    480.7500,
    'Crixás',
    'GO',
    '2023-02-14',
    '2023-11-20',
    3,
    '2026-11-20',
    NULL,
    'Ativo',
    ST_Multi(ST_GeomFromText('POLYGON((-49.9900 -14.5200, -49.9500 -14.5200, -49.9500 -14.5600, -49.9900 -14.5600, -49.9900 -14.5200))', 4674))
),
(
    4,
    '850.880/2020',
    2020,
    3,
    'Concessão de Lavra',
    'Cobre',
    'Fios e Condutores Elétricos',
    1920.0000,
    'Parauapebas',
    'PA',
    '2018-05-10',
    '2019-03-01',
    3,
    '2022-03-01',
    '2024-02-18',
    'Ativo',
    ST_Multi(ST_GeomFromText('POLYGON((-49.9200 -6.0500, -49.8600 -6.0500, -49.8600 -6.1100, -49.9200 -6.1100, -49.9200 -6.0500))', 4674))
),
(
    5,
    '851.304/2022',
    2022,
    3,
    'Autorização de Pesquisa',
    'Manganês',
    'Ligas de Aço / Baterias',
    750.3000,
    'Canaã dos Carajás',
    'PA',
    '2022-08-11',
    '2023-05-10',
    3,
    '2026-05-10',
    NULL,
    'Ativo',
    ST_Multi(ST_GeomFromText('POLYGON((-49.8200 -6.4800, -49.7700 -6.4800, -49.7700 -6.5300, -49.8200 -6.5300, -49.8200 -6.4800))', 4674))
),
(
    6,
    '870.015/2022',
    2022,
    4,
    'Autorização de Pesquisa',
    'Grafita',
    'Indústria de Refratários e Baterias',
    620.1000,
    'Caetité',
    'BA',
    '2022-01-18',
    '2022-10-05',
    3,
    '2025-10-05',
    NULL,
    'Ativo',
    ST_Multi(ST_GeomFromText('POLYGON((-42.5200 -14.0500, -42.4700 -14.0500, -42.4700 -14.1000, -42.5200 -14.1000, -42.5200 -14.0500))', 4674))
),
(
    7,
    '832.901/2024',
    2024,
    1,
    'Requerimento de Pesquisa',
    'Lítio',
    'Baterias de Íons de Lítio',
    1150.0000,
    'Nova Lima',
    'MG',
    '2024-04-10',
    NULL,
    3,
    NULL,
    NULL,
    'Ativo',
    ST_Multi(ST_GeomFromText('POLYGON((-43.8800 -19.9800, -43.8300 -19.9800, -43.8300 -20.0300, -43.8800 -20.0300, -43.8800 -19.9800))', 4674))
),
(
    8,
    '861.554/2021',
    2021,
    2,
    'Requerimento de Lavra',
    'Calcário',
    'Corretivo Agrícola / Cimento',
    830.4000,
    'Niquelândia',
    'GO',
    '2021-09-05',
    '2022-03-25',
    3,
    '2025-03-25',
    NULL,
    'Ativo',
    ST_Multi(ST_GeomFromText('POLYGON((-48.4800 -14.4000, -48.4300 -14.4000, -48.4300 -14.4500, -48.4800 -14.4500, -48.4800 -14.4000))', 4674))
);

SELECT setval('processo_id_seq', (SELECT MAX(id) FROM processo));

-- 7.3. Eventos Históricos dos Processos
INSERT INTO evento (processo_id, tipo_evento, data_evento, descricao, documento_sei, responsavel) VALUES
(1, 'Requerimento Protocolado', '2021-03-10', 'Protocolo inicial do requerimento de pesquisa mineral para ferro', 'SEI-02100.001234/2021', 'Dr. Marcos Silveira - Geologia'),
(1, 'Publicação de Alvará de Pesquisa no DOU', '2022-04-15', 'Publicado Alvará de Pesquisa nº 4501/2022 com vigência de 3 anos', 'DOU Seção 1 nº 72/2022', 'ANM - Gerência Regional MG'),
(1, 'Pagamento de TAH', '2023-01-25', 'Pagamento da 1ª anuidade da Taxa Anual por Hectare quitado tempestivamente', 'GRU-998877665544', 'Financeiro Corporativo'),
(1, 'Emissão de Guia de Utilização', '2024-03-10', 'Autorizada extração prévia de até 50.000 ton de minério para testes metalúrgicos', 'GU-ANM-MG-045/2024', 'Superintendência ANM/MG'),

(2, 'Publicação de Alvará de Pesquisa no DOU', '2020-08-10', 'Alvará de Pesquisa nº 2210/2020 publicado', 'DOU Seção 1 nº 150/2020', 'ANM/MG'),
(2, 'Protocolo de Relatório Final de Pesquisa', '2023-08-01', 'Apresentado Relatório Final de Pesquisa Positivo com cubagem e teor', 'SEI-02100.009876/2023', 'Geominas Consultoria'),
(2, 'Aprovação de Relatório de Pesquisa', '2023-12-15', 'Relatório Final aprovado pela ANM, outorgando Direito de Requerer Lavra', 'Parecer Técnico nº 450/2023', 'ANM Sede Brasília'),

(3, 'Requerimento Protocolado', '2023-02-14', 'Protocolo de pesquisa de ouro na Faixa Crixás', 'SEI-02300.000456/2023', 'Eng. Rogério Duarte'),
(3, 'Publicação de Alvará de Pesquisa no DOU', '2023-11-20', 'Alvará de Pesquisa nº 8870/2023 publicado', 'DOU nº 220/2023', 'ANM/GO'),

(4, 'Publicação de Alvará de Pesquisa no DOU', '2019-03-01', 'Alvará publicado em 2019 para cobre em Carajás', 'DOU nº 41/2019', 'ANM/PA'),
(4, 'Protocolo de Requerimento de Lavra', '2022-06-15', 'Protocolado Plano de Aproveitamento Econômico (PAE)', 'SEI-02400.003322/2022', 'Diretoria de Engenharia Mineral'),
(4, 'Publicação de Portaria de Lavra', '2024-02-18', 'Publicada Portaria MME nº 302/2024 outorgando a Concessão de Lavra', 'DOU nº 35/2024', 'Ministério de Minas e Energia'),

(5, 'Publicação de Alvará de Pesquisa no DOU', '2023-05-10', 'Alvará de Pesquisa nº 5410/2023 para manganês', 'DOU nº 88/2023', 'ANM/PA'),
(5, 'Requerimento de Guia de Utilização', '2024-06-12', 'Solicitada Guia de Utilização para teste piloto de usina', 'SEI-02400.008811/2024', 'Gerência Técnica PA'),

(6, 'Publicação de Alvará de Pesquisa no DOU', '2022-10-05', 'Alvará de Pesquisa nº 9100/2022 para grafita', 'DOU nº 190/2022', 'ANM/BA');

-- 7.4. Obrigações e Prazos Legais Fictícios
-- Os alertas e dias_para_vencer serão recalculados e mantidos consistentes pelos triggers
INSERT INTO obrigacao (processo_id, tipo_obrigacao, descricao, ano_exercicio, data_referencia, data_vencimento, data_cumprimento, status, valor_devido, numero_guia_documento, observacoes) VALUES
-- Processo 1 (Congonhas/MG - Alvará publicado em 15/04/2022, vencimento RFP em 15/04/2025)
(1, 'Relatório de Pesquisa', 'Apresentação do Relatório Final de Pesquisa (RFP) - Art. 22 do Código de Mineração', 2025, '2022-04-15', '2025-04-15', NULL, 'Pendente', 0.00, 'SEI-02100.001234/2021', 'Equipe de geologia finalizando modelamento geológico 3D e cálculo de reservas'),
(1, 'Taxa Anual por Hectare', 'TAH correspondente ao exercício 2024 (R$ 4,71/ha * 985,50 ha)', 2024, '2024-01-01', '2024-07-31', '2024-07-20', 'Cumprido', 4641.71, 'GRU-001-2024', 'Pago tempestivamente no Banco do Brasil'),
(1, 'Taxa Anual por Hectare', 'TAH correspondente ao exercício 2025', 2025, '2025-01-01', '2025-07-31', NULL, 'Pendente', 4641.71, NULL, 'Aguardando abertura de emissão de boleto no SIGMINE'),
(1, 'Guia de Utilização', 'Vigência e prestação de contas da Guia de Utilização GU-ANM-MG-045/2024', 2024, '2024-03-10', '2025-03-10', NULL, 'Pendente', 2500.00, 'GU-ANM-MG-045/2024', 'Monitoramento mensal dos volumes extraídos e recolhimento de CFEM'),

-- Processo 2 (Mariana/MG - RFP já cumprido, em fase de Direito de Requerer Lavra)
(2, 'Relatório de Pesquisa', 'Relatório Final de Pesquisa entregue e aprovado com mérito', 2023, '2020-08-10', '2023-08-10', '2023-08-01', 'Cumprido', 0.00, 'SEI-02100.009876/2023', 'Aprovado pelo Parecer Técnico nº 450/2023'),
(2, 'Cumprimento de Exigência', 'Apresentação de certidão de conformidade ambiental municipal para lavra', 2024, '2024-10-01', '2024-12-15', '2024-12-10', 'Cumprido', 0.00, 'OFICIO-ANM-552/2024', 'Certidão da Prefeitura de Mariana anexada ao processo SEI'),

-- Processo 3 (Crixás/GO - Ouro, Alvará em 20/11/2023)
(3, 'Relatório de Pesquisa', 'Relatório Final de Pesquisa (vigência até 20/11/2026)', 2026, '2023-11-20', '2026-11-20', NULL, 'Pendente', 0.00, NULL, 'Fase de sondagem rotativa e amostragem de testemunho'),
(3, 'Taxa Anual por Hectare', 'TAH Exercício 2024 (1º ano de vigência)', 2024, '2023-11-20', '2024-01-31', '2024-01-29', 'Cumprido', 2264.33, 'GRU-GO-2024-01', 'Pago com desconto dentro do prazo'),
(3, 'Taxa Anual por Hectare', 'TAH Exercício 2025', 2025, '2024-11-20', '2025-01-31', NULL, 'Pendente', 2264.33, NULL, 'Boleto gerado, agendado no departamento financeiro'),

-- Processo 4 (Parauapebas/PA - Cobre, Concessão de Lavra, RAL e Obrigações)
(4, 'Relatório Anual de Lavra - RAL', 'Declaração obrigatória do RAL referente ao ano-base anterior (Art. 51 do Código de Mineração)', 2024, '2024-01-01', '2024-03-15', '2024-03-12', 'Cumprido', 0.00, 'RAL-2024-ANM', 'Transmitido via sistema RAL Web'),
(4, 'Relatório Anual de Lavra - RAL', 'Declaração do RAL exercício 2025 (ano-base 2024)', 2025, '2025-01-01', '2025-03-15', NULL, 'Pendente', 0.00, NULL, 'Dados de produção e balanço mineral em consolidação'),

-- Processo 5 (Canaã dos Carajás/PA - Manganês, Alvará em 10/05/2023)
(5, 'Relatório de Pesquisa', 'Relatório Final de Pesquisa para manganês', 2026, '2023-05-10', '2026-05-10', NULL, 'Pendente', 0.00, NULL, 'Campanha de prospecção geofísica em andamento'),
(5, 'Taxa Anual por Hectare', 'TAH Exercício 2024', 2024, '2023-05-10', '2024-07-31', '2024-07-28', 'Cumprido', 3533.91, 'GRU-PA-005', 'Quitado'),
(5, 'Taxa Anual por Hectare', 'TAH Exercício 2025', 2025, '2024-05-10', '2025-07-31', NULL, 'Pendente', 3533.91, NULL, 'Pendente de emissão'),

-- Processo 6 (Caetité/BA - Grafita, Alvará em 05/10/2022)
(6, 'Relatório de Pesquisa', 'Relatório Final de Pesquisa - Grafita', 2025, '2022-10-05', '2025-10-05', NULL, 'Pendente', 0.00, NULL, 'Trincheiras e análises granulométricas em laboratório'),
(6, 'Taxa Anual por Hectare', 'TAH Exercício 2024', 2024, '2023-10-05', '2024-01-31', '2024-01-30', 'Cumprido', 2920.67, 'GRU-BA-2024', 'Comprovante anexado'),
(6, 'Taxa Anual por Hectare', 'TAH Exercício 2025', 2025, '2024-10-05', '2025-01-31', NULL, 'Pendente', 2920.67, NULL, 'Aguardando financeiro');

-- Casos de teste específicos simulando prazos em ALERTA CRÍTICO e VENCIDOS em relação à data atual:
-- Inserimos obrigações com vencimentos dinâmicos para garantir que tenhamos cenários de alerta no teste
INSERT INTO obrigacao (processo_id, tipo_obrigacao, descricao, ano_exercicio, data_referencia, data_vencimento, data_cumprimento, status, valor_devido, observacoes) VALUES
-- Obrigação VENCIDA há 15 dias:
(6, 'Cumprimento de Exigência', 'Exigência de complementação de estudo espeleológico na poligonal', 2024, CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE - INTERVAL '15 days', NULL, 'Pendente', 0.00, 'Exigência expedida pela ANM com prazo improrrogável expirado - Ação Urgente'),
-- Obrigação em ALERTA CRÍTICO (vence em 8 dias):
(5, 'Guia de Utilização', 'Renovação de Guia de Utilização com laudo de lavra experimental', 2024, CURRENT_DATE - INTERVAL '355 days', CURRENT_DATE + INTERVAL '8 days', NULL, 'Pendente', 3200.00, 'Vencimento em menos de 10 dias - Prioridade Máxima'),
-- Obrigação em ALERTA CRÍTICO (vence em 22 dias):
(3, 'Cumprimento de Exigência', 'Esclarecimento sobre sobreposição com faixa de servidão de linha de transmissão', 2024, CURRENT_DATE - INTERVAL '38 days', CURRENT_DATE + INTERVAL '22 days', NULL, 'Pendente', 0.00, 'Notificação nº 88/2024 - Prazo de 60 dias em contagem'),
-- Obrigação NO PRAZO (vence em 120 dias):
(1, 'Cumprimento de Exigência', 'Apresentação de memorial descritivo retificado conforme novo vértice do marco geodésico', 2025, CURRENT_DATE - INTERVAL '10 days', CURRENT_DATE + INTERVAL '120 days', NULL, 'Pendente', 0.00, 'Dentro do prazo regular de atendimento');
