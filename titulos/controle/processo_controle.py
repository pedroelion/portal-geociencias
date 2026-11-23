"""
Módulo: controle/processo_controle.py
Descrição: Controlador da lógica de negócio para titulares, processos, eventos,
            obrigações, triggers e views do sistema minerário.
"""

import json
try:
    from titulos.db.database import execute_query, execute_single, execute_commit
except ImportError:
    from db.database import execute_query, execute_single, execute_commit
try:
    from titulos.modelo.titular import Titular
except ImportError:
    from modelo.titular import Titular
try:
    from titulos.modelo.processo import Processo
except ImportError:
    from modelo.processo import Processo
try:
    from titulos.modelo.evento import Evento
except ImportError:
    from modelo.evento import Evento
try:
    from titulos.modelo.obrigacao import Obrigacao
except ImportError:
    from modelo.obrigacao import Obrigacao

class ProcessoControle:

    @staticmethod
    def listar_titulares():
        """Lista todos os titulares minerários cadastrados."""
        sql = "SELECT * FROM titular ORDER BY razao_social ASC;"
        rows = execute_query(sql)
        return [Titular.from_dict(r).to_dict() for r in rows]

    @staticmethod
    def listar_processos(filtro_fase=None, filtro_alerta=None):
        """Lista processos minerários a partir da view consolidada de situação."""
        sql = """
        SELECT 
            processo_id, numero_processo, ano_processo, fase, substancia_mineral,
            uso_substancia, area_ha, municipio, uf, data_requerimento,
            data_publicacao_alvara, data_vencimento_alvara, status_processo,
            titular_id, titular_razao_social, titular_cnpj_cpf, titular_email, titular_telefone,
            total_obrigacoes, total_pendentes, total_vencidas, total_alerta_critico,
            total_no_prazo, total_cumpridas, valor_tah_pendente, pior_nivel_alerta,
            proxima_obrigacao_tipo, proxima_obrigacao_data, proxima_obrigacao_dias,
            proxima_obrigacao_alerta
        FROM vw_processos_situacao_espacial
        WHERE 1=1
        """
        params = []
        if filtro_fase:
            sql += " AND fase = %s"
            params.append(filtro_fase)
        if filtro_alerta:
            sql += " AND pior_nivel_alerta = %s"
            params.append(filtro_alerta)
        sql += " ORDER BY total_vencidas DESC, total_alerta_critico DESC, processo_id ASC;"
        rows = execute_query(sql, params)
        # Formata datas para string serializável
        for r in rows:
            for k in ["data_requerimento", "data_publicacao_alvara", "data_vencimento_alvara", "proxima_obrigacao_data"]:
                if r.get(k):
                    r[k] = str(r[k])
            if r.get("area_ha"):
                r["area_ha"] = float(r["area_ha"])
            if r.get("valor_tah_pendente"):
                r["valor_tah_pendente"] = float(r["valor_tah_pendente"])
        return rows

    @staticmethod
    def obter_processo_detalhado(processo_id):
        """Obtém detalhes completos de um processo, incluindo histórico de eventos e obrigações."""
        sql_proc = """
        SELECT p.*, t.razao_social AS titular_razao_social, t.cnpj_cpf AS titular_cnpj_cpf,
               t.email AS titular_email, t.telefone AS titular_telefone,
               ST_AsGeoJSON(p.geom) AS geojson
        FROM processo p
        JOIN titular t ON p.titular_id = t.id
        WHERE p.id = %s;
        """
        proc = execute_single(sql_proc, [processo_id])
        if not proc:
            return None

        for k in ["data_requerimento", "data_publicacao_alvara", "data_vencimento_alvara", "data_portaria_lavra", "criado_em"]:
            if proc.get(k):
                proc[k] = str(proc[k])
        if proc.get("area_ha"):
            proc["area_ha"] = float(proc["area_ha"])
        if proc.get("geojson"):
            proc["geom_geojson"] = json.loads(proc["geojson"])

        # Eventos do processo (1:N)
        sql_eventos = "SELECT * FROM evento WHERE processo_id = %s ORDER BY data_evento DESC, id DESC;"
        ev_rows = execute_query(sql_eventos, [processo_id])
        eventos = [Evento.from_dict(r).to_dict() for r in ev_rows]

        # Obrigações do processo (1:N)
        sql_obrig = "SELECT * FROM obrigacao WHERE processo_id = %s ORDER BY data_vencimento ASC, id ASC;"
        ob_rows = execute_query(sql_obrig, [processo_id])
        obrigacoes = [Obrigacao.from_dict(r).to_dict() for r in ob_rows]

        proc["eventos"] = eventos
        proc["obrigacoes"] = obrigacoes
        return proc

    @staticmethod
    def listar_eventos(processo_id=None):
        """Lista eventos regulatórios com dados do processo associado."""
        sql = """
        SELECT e.*, p.numero_processo, p.substancia_mineral, t.razao_social AS titular
        FROM evento e
        JOIN processo p ON e.processo_id = p.id
        JOIN titular t ON p.titular_id = t.id
        """
        params = []
        if processo_id:
            sql += " WHERE e.processo_id = %s"
            params.append(processo_id)
        sql += " ORDER BY e.data_evento DESC, e.id DESC;"
        rows = execute_query(sql, params)
        for r in rows:
            for k in ["data_evento", "criado_em"]:
                if r.get(k):
                    r[k] = str(r[k])
        return rows

    @staticmethod
    def inserir_evento(processo_id, tipo_evento, data_evento, descricao, documento_sei="", responsavel=""):
        """
        Insere novo evento regulatório.
        Dispara o trigger trg_gerar_obrigacoes_evento que automaticamente gera/cumpre obrigações.
        """
        sql = """
        INSERT INTO evento (processo_id, tipo_evento, data_evento, descricao, documento_sei, responsavel)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        res = execute_commit(sql, [processo_id, tipo_evento, data_evento, descricao, documento_sei, responsavel])
        return res

    @staticmethod
    def listar_obrigacoes(processo_id=None, tipo=None, alerta=None):
        """Lista obrigações legais com informações do processo e titular."""
        sql = """
        SELECT o.*, p.numero_processo, p.substancia_mineral, p.area_ha,
               t.razao_social AS titular_razao_social
        FROM obrigacao o
        JOIN processo p ON o.processo_id = p.id
        JOIN titular t ON p.titular_id = t.id
        WHERE 1=1
        """
        params = []
        if processo_id:
            sql += " AND o.processo_id = %s"
            params.append(processo_id)
        if tipo:
            sql += " AND o.tipo_obrigacao = %s"
            params.append(tipo)
        if alerta:
            sql += " AND o.nivel_alerta = %s"
            params.append(alerta)
        sql += " ORDER BY o.data_vencimento ASC;"
        rows = execute_query(sql, params)
        for r in rows:
            for k in ["data_referencia", "data_vencimento", "data_cumprimento", "criado_em", "atualizado_em"]:
                if r.get(k):
                    r[k] = str(r[k])
            if r.get("valor_devido"):
                r["valor_devido"] = float(r["valor_devido"])
            if r.get("area_ha"):
                r["area_ha"] = float(r["area_ha"])
        return rows

    @staticmethod
    def cumprir_obrigacao(obrigacao_id, data_cumprimento=None):
        """Marca uma obrigação como cumprida, disparando o recálculo do trigger."""
        sql = """
        UPDATE obrigacao
        SET status = 'Cumprido',
            data_cumprimento = COALESCE(%s, CURRENT_DATE),
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, status, nivel_alerta, data_cumprimento;
        """
        res = execute_commit(sql, [data_cumprimento, obrigacao_id])
        return res

    @staticmethod
    def obter_painel_consolidado():
        """Obtém os dados agregados da view vw_painel_prazos_consolidado."""
        sql = "SELECT * FROM vw_painel_prazos_consolidado;"
        rows = execute_query(sql)
        for r in rows:
            if r.get("valor_total_pendente"):
                r["valor_total_pendente"] = float(r["valor_total_pendente"])
            if r.get("conformidade_percentual"):
                r["conformidade_percentual"] = float(r["conformidade_percentual"])
        return rows

    @staticmethod
    def obter_alertas_urgentes():
        """Obtém os prazos vencidos ou críticos da view vw_painel_alertas_urgentes."""
        sql = "SELECT * FROM vw_painel_alertas_urgentes;"
        rows = execute_query(sql)
        for r in rows:
            if r.get("data_vencimento"):
                r["data_vencimento"] = str(r["data_vencimento"])
            if r.get("valor_devido"):
                r["valor_devido"] = float(r["valor_devido"])
        return rows

    @staticmethod
    def obter_situacao_espacial_geojson():
        """Retorna FeatureCollection GeoJSON com as poligonais dos processos e níveis de alerta."""
        sql = """
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(ST_AsGeoJSON(v.*)::json), '[]'::json)
        ) AS geojson
        FROM vw_processos_situacao_espacial v;
        """
        res = execute_single(sql)
        if res and res.get("geojson"):
            return res["geojson"]
        return {"type": "FeatureCollection", "features": []}
