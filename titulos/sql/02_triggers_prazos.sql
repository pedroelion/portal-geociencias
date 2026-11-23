-- ==============================================================================
-- SISTEMA CORPORATIVO DE GESTÃO DE TÍTULOS MINERÁRIOS (ANM / SIGMINE)
-- Script: 02_triggers_prazos.sql
-- Descrição: Funções e triggers PL/pgSQL para cálculo automático de vencimentos,
--            recalculo dinâmico de status e níveis de alerta de prazos legais
--            (RFP, TAH, GU, RAL, Exigências) e sincronização por eventos.
-- ==============================================================================

-- ==============================================================================
-- 1. Função: Cálculo Automático da Data de Vencimento
--    (Regras do Código de Mineração / Resoluções ANM)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_calcular_vencimento_automatica_obrigacao()
RETURNS TRIGGER AS $$
DECLARE
    v_mes INT;
    v_ano INT;
    v_area NUMERIC(12,4);
BEGIN
    -- Se a data de vencimento não foi informada manualmente, calcula conforme regra legal
    IF NEW.data_vencimento IS NULL THEN
        IF NEW.data_referencia IS NULL THEN
            NEW.data_referencia := CURRENT_DATE;
        END IF;

        v_mes := EXTRACT(MONTH FROM NEW.data_referencia)::INT;
        v_ano := EXTRACT(YEAR FROM NEW.data_referencia)::INT;

        CASE NEW.tipo_obrigacao
            -- 1. Relatório Final de Pesquisa (RFP): 3 anos após o alvará
            WHEN 'Relatório de Pesquisa' THEN
                NEW.data_vencimento := (NEW.data_referencia + INTERVAL '3 years')::DATE;

            -- 2. Taxa Anual por Hectare (TAH):
            --    - Se alvará no 1º semestre: vence em 31 de julho
            --    - Se alvará no 2º semestre: vence em 31 de janeiro do ano seguinte
            WHEN 'Taxa Anual por Hectare' THEN
                IF v_mes <= 6 THEN
                    NEW.data_vencimento := make_date(v_ano, 7, 31);
                ELSE
                    NEW.data_vencimento := make_date(v_ano + 1, 1, 31);
                END IF;

            -- 3. Guia de Utilização (GU): vigência padrão de 1 ano
            WHEN 'Guia de Utilização' THEN
                NEW.data_vencimento := (NEW.data_referencia + INTERVAL '1 year')::DATE;

            -- 4. Relatório Anual de Lavra (RAL): 15 de março do ano seguinte
            WHEN 'Relatório Anual de Lavra - RAL' THEN
                IF NEW.ano_exercicio IS NOT NULL THEN
                    NEW.data_vencimento := make_date(NEW.ano_exercicio, 3, 15);
                ELSE
                    NEW.data_vencimento := make_date(v_ano + 1, 3, 15);
                END IF;

            -- 5. Cumprimento de Exigência ANM: 60 dias a partir da notificação
            WHEN 'Cumprimento de Exigência' THEN
                NEW.data_vencimento := (NEW.data_referencia + INTERVAL '60 days')::DATE;

            ELSE
                NEW.data_vencimento := (NEW.data_referencia + INTERVAL '30 days')::DATE;
        END CASE;
    END IF;

    -- Se valor_devido for 0 ou nulo para TAH, calcula automaticamente (R$ 4,71/ha)
    IF NEW.tipo_obrigacao = 'Taxa Anual por Hectare' AND (NEW.valor_devido IS NULL OR NEW.valor_devido = 0) THEN
        SELECT area_ha INTO v_area FROM processo WHERE id = NEW.processo_id;
        IF v_area IS NOT NULL THEN
            NEW.valor_devido := ROUND(v_area * 4.71, 2);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para cálculo automático do vencimento antes de inserir obrigação
DROP TRIGGER IF EXISTS trg_calcular_vencimento_obrigacao ON obrigacao;
CREATE TRIGGER trg_calcular_vencimento_obrigacao
BEFORE INSERT ON obrigacao
FOR EACH ROW
EXECUTE FUNCTION fn_calcular_vencimento_automatica_obrigacao();

-- ==============================================================================
-- 2. Função: Recalcular Alerta e Dias para Vencer
--    Atualiza dinamicamente status e nível de alerta:
--    - 'Vencido' (dias < 0)
--    - 'Alerta Crítico / Próximo ao Vencimento' (0 a 30 dias)
--    - 'No Prazo' (> 30 dias)
--    - 'Cumprido' (se data_cumprimento preenchida ou status cumprido/dispensado)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_recalcular_alerta_obrigacao()
RETURNS TRIGGER AS $$
BEGIN
    -- Se houver data de cumprimento preenchida, considera CUMPRIDO
    IF NEW.data_cumprimento IS NOT NULL THEN
        NEW.status := 'Cumprido';
        NEW.nivel_alerta := 'Cumprido';
        NEW.dias_para_vencer := (NEW.data_vencimento - NEW.data_cumprimento);
    ELSIF NEW.status IN ('Cumprido', 'Dispensado', 'Cancelado') THEN
        NEW.nivel_alerta := 'Cumprido';
        IF NEW.data_cumprimento IS NULL AND NEW.status = 'Cumprido' THEN
            NEW.data_cumprimento := CURRENT_DATE;
        END IF;
        NEW.dias_para_vencer := (NEW.data_vencimento - CURRENT_DATE);
    ELSE
        -- Obrigação Pendente: calcular em relação à data atual (CURRENT_DATE)
        NEW.status := 'Pendente';
        NEW.dias_para_vencer := (NEW.data_vencimento - CURRENT_DATE);

        IF NEW.dias_para_vencer < 0 THEN
            NEW.nivel_alerta := 'Vencido';
        ELSIF NEW.dias_para_vencer <= 30 THEN
            NEW.nivel_alerta := 'Alerta Crítico / Próximo ao Vencimento';
        ELSE
            NEW.nivel_alerta := 'No Prazo';
        END IF;
    END IF;

    NEW.atualizado_em := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger que recalcula alerta antes de inserir ou atualizar a obrigação
DROP TRIGGER IF EXISTS trg_recalcular_alerta_obrigacao ON obrigacao;
CREATE TRIGGER trg_recalcular_alerta_obrigacao
BEFORE INSERT OR UPDATE ON obrigacao
FOR EACH ROW
EXECUTE FUNCTION fn_recalcular_alerta_obrigacao();

-- ==============================================================================
-- 3. Função: Sincronização e Geração Automática de Obrigações por Evento
--    Ao inserir um evento regulatório no processo, cria ou cumpre obrigações
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_gerar_obrigacoes_por_evento()
RETURNS TRIGGER AS $$
DECLARE
    v_proc RECORD;
    v_venc_tah DATE;
    v_mes_evento INT;
    v_ano_evento INT;
    v_tah_existente INT;
    v_rfp_existente INT;
    v_gu_existente INT;
BEGIN
    -- Carrega dados do processo associado
    SELECT * INTO v_proc FROM processo WHERE id = NEW.processo_id;

    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    v_mes_evento := EXTRACT(MONTH FROM NEW.data_evento)::INT;
    v_ano_evento := EXTRACT(YEAR FROM NEW.data_evento)::INT;

    -- Caso 1: Publicação de Alvará de Pesquisa no DOU
    IF NEW.tipo_evento = 'Publicação de Alvará de Pesquisa no DOU' THEN
        -- Atualiza datas no processo
        UPDATE processo
        SET data_publicacao_alvara = NEW.data_evento,
            data_vencimento_alvara = (NEW.data_evento + INTERVAL '3 years')::DATE,
            fase = 'Autorização de Pesquisa'
        WHERE id = NEW.processo_id;

        -- Gera obrigação do Relatório Final de Pesquisa (se não existir)
        SELECT COUNT(*) INTO v_rfp_existente
        FROM obrigacao
        WHERE processo_id = NEW.processo_id
          AND tipo_obrigacao = 'Relatório de Pesquisa'
          AND status = 'Pendente';

        IF v_rfp_existente = 0 THEN
            INSERT INTO obrigacao (
                processo_id,
                tipo_obrigacao,
                descricao,
                ano_exercicio,
                data_referencia,
                data_vencimento,
                status,
                valor_devido,
                numero_guia_documento,
                observacoes
            ) VALUES (
                NEW.processo_id,
                'Relatório de Pesquisa',
                'Relatório Final de Pesquisa gerado automaticamente pelo Alvará de ' || TO_CHAR(NEW.data_evento, 'DD/MM/YYYY'),
                EXTRACT(YEAR FROM (NEW.data_evento + INTERVAL '3 years'))::INT,
                NEW.data_evento,
                (NEW.data_evento + INTERVAL '3 years')::DATE,
                'Pendente',
                0.00,
                NEW.documento_sei,
                'Gerado via Trigger por publicação de alvará'
            );
        END IF;

        -- Gera 1ª anuidade da Taxa Anual por Hectare (TAH)
        IF v_mes_evento <= 6 THEN
            v_venc_tah := make_date(v_ano_evento, 7, 31);
        ELSE
            v_venc_tah := make_date(v_ano_evento + 1, 1, 31);
        END IF;

        SELECT COUNT(*) INTO v_tah_existente
        FROM obrigacao
        WHERE processo_id = NEW.processo_id
          AND tipo_obrigacao = 'Taxa Anual por Hectare'
          AND data_vencimento = v_venc_tah;

        IF v_tah_existente = 0 THEN
            INSERT INTO obrigacao (
                processo_id,
                tipo_obrigacao,
                descricao,
                ano_exercicio,
                data_referencia,
                data_vencimento,
                status,
                valor_devido,
                numero_guia_documento,
                observacoes
            ) VALUES (
                NEW.processo_id,
                'Taxa Anual por Hectare',
                '1ª Anuidade TAH - Exercício ' || EXTRACT(YEAR FROM v_venc_tah)::INT,
                EXTRACT(YEAR FROM v_venc_tah)::INT,
                NEW.data_evento,
                v_venc_tah,
                'Pendente',
                ROUND(v_proc.area_ha * 4.71, 2),
                NULL,
                'Gerado via Trigger após outorga de alvará de pesquisa'
            );
        END IF;

    -- Caso 2: Emissão de Guia de Utilização
    ELSIF NEW.tipo_evento = 'Emissão de Guia de Utilização' THEN
        INSERT INTO obrigacao (
            processo_id,
            tipo_obrigacao,
            descricao,
            ano_exercicio,
            data_referencia,
            data_vencimento,
            status,
            valor_devido,
            numero_guia_documento,
            observacoes
        ) VALUES (
            NEW.processo_id,
            'Guia de Utilização',
            'Vigência e prestação de contas da Guia de Utilização (' || COALESCE(NEW.documento_sei, 'GU') || ')',
            v_ano_evento,
            NEW.data_evento,
            (NEW.data_evento + INTERVAL '1 year')::DATE,
            'Pendente',
            0.00,
            NEW.documento_sei,
            'Gerado via Trigger por emissão de GU'
        );

    -- Caso 3: Pagamento de TAH informado em evento -> dá baixa na obrigação mais antiga pendente
    ELSIF NEW.tipo_evento = 'Pagamento de TAH' THEN
        UPDATE obrigacao
        SET status = 'Cumprido',
            data_cumprimento = NEW.data_evento,
            observacoes = COALESCE(observacoes, '') || ' [Quitado via evento: ' || COALESCE(NEW.documento_sei, 'comprovante') || ']'
        WHERE id = (
            SELECT id FROM obrigacao
            WHERE processo_id = NEW.processo_id
              AND tipo_obrigacao = 'Taxa Anual por Hectare'
              AND status = 'Pendente'
            ORDER BY data_vencimento ASC
            LIMIT 1
        );

    -- Caso 4: Protocolo de Relatório Final de Pesquisa -> cumpre obrigação de RFP
    ELSIF NEW.tipo_evento = 'Protocolo de Relatório Final de Pesquisa' THEN
        UPDATE obrigacao
        SET status = 'Cumprido',
            data_cumprimento = NEW.data_evento,
            observacoes = COALESCE(observacoes, '') || ' [Cumprido via protocolo SEI: ' || COALESCE(NEW.documento_sei, '') || ']'
        WHERE id = (
            SELECT id FROM obrigacao
            WHERE processo_id = NEW.processo_id
              AND tipo_obrigacao = 'Relatório de Pesquisa'
              AND status = 'Pendente'
            ORDER BY data_vencimento ASC
            LIMIT 1
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pós-inserção de evento
DROP TRIGGER IF EXISTS trg_gerar_obrigacoes_evento ON evento;
CREATE TRIGGER trg_gerar_obrigacoes_evento
AFTER INSERT ON evento
FOR EACH ROW
EXECUTE FUNCTION fn_gerar_obrigacoes_por_evento();

-- ==============================================================================
-- 4. Função Utilitária de Recálculo Geral em Lote
--    Pode ser disparada periodicamente ou por agendamento cron
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_atualizar_todos_alertas()
RETURNS TABLE (
    total_processadas INT,
    total_vencidas INT,
    total_alerta_critico INT,
    total_no_prazo INT,
    total_cumpridas INT
) AS $$
DECLARE
    v_total INT;
    v_venc INT;
    v_crit INT;
    v_prazo INT;
    v_cump INT;
BEGIN
    -- Executa UPDATE disparando o trigger trg_recalcular_alerta_obrigacao
    UPDATE obrigacao
    SET atualizado_em = CURRENT_TIMESTAMP;

    SELECT COUNT(*) INTO v_total FROM obrigacao;
    SELECT COUNT(*) INTO v_venc FROM obrigacao WHERE nivel_alerta = 'Vencido';
    SELECT COUNT(*) INTO v_crit FROM obrigacao WHERE nivel_alerta = 'Alerta Crítico / Próximo ao Vencimento';
    SELECT COUNT(*) INTO v_prazo FROM obrigacao WHERE nivel_alerta = 'No Prazo';
    SELECT COUNT(*) INTO v_cump FROM obrigacao WHERE nivel_alerta = 'Cumprido';

    RETURN QUERY SELECT v_total, v_venc, v_crit, v_prazo, v_cump;
END;
$$ LANGUAGE plpgsql;

-- Disparar a atualização inicial para sincronizar os dados já inseridos
SELECT * FROM fn_atualizar_todos_alertas();
